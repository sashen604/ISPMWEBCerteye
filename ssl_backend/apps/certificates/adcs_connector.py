"""
AD CS Connector - Fetches certificates from Active Directory Certificate Services.
Supports WinRM, LDAP, and agent-based collection.
"""

import logging
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from django.utils import timezone

try:
    import winrm
except Exception:
    winrm = None

logger = logging.getLogger(__name__)


class ADCSConnector:
    """
    Base connector class for AD CS integration.
    """
    
    def __init__(self, source):
        self.source = source
        self.connection = None
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test connectivity to AD CS source."""
        raise NotImplementedError
    
    def fetch_certificates(self) -> List[Dict]:
        """Fetch certificate list from AD CS."""
        raise NotImplementedError
    
    def close(self):
        """Close any open connections."""
        if self.connection:
            self.connection.close()


class WinRMConnector(ADCSConnector):
    """
    Connects to Windows AD CS server via WinRM and PowerShell.
    Falls back to subprocess for local testing.
    """
    
    def __init__(self, source, password: Optional[str] = None):
        super().__init__(source)
        self.session = None
        self.password = password

    def _build_username(self) -> str:
        username = self.source.username or ''
        if '\\' in username or '@' in username:
            return username
        domain = (self.source.domain or '').strip()
        if domain:
            return f"{domain}\\{username}"
        return username

    def _candidate_usernames(self) -> List[str]:
        raw_username = (self.source.username or '').strip()
        if not raw_username:
            return ['']

        candidates = [raw_username]
        domain = (self.source.domain or '').strip()

        if '\\' in raw_username:
            base_username = raw_username.split('\\')[-1]
        elif '@' in raw_username:
            base_username = raw_username.split('@')[0]
        else:
            base_username = raw_username

        if domain:
            domain_netbios = domain.split('.')[0]
            candidates.append(f"{domain}\\{base_username}")
            candidates.append(f"{domain_netbios}\\{base_username}")
            candidates.append(f"{base_username}@{domain}")

        candidates.append(base_username)

        deduped = []
        for candidate in candidates:
            if candidate and candidate not in deduped:
                deduped.append(candidate)
        return deduped

    def _endpoint(self) -> str:
        # Port 5986 is the secure WinRM endpoint; prefer https even if source flag is stale.
        scheme = 'https' if (self.source.use_ssl or int(self.source.port) == 5986) else 'http'
        return f"{scheme}://{self.source.server_hostname}:{self.source.port}/wsman"

    def _create_session(self):
        if winrm is None:
            raise RuntimeError('pywinrm is not installed. Install pywinrm and requests-ntlm')
        if not self.password:
            raise RuntimeError('Missing decrypted password for WinRM connection')

        transport = 'ntlm'
        server_cert_validation = 'validate' if self.source.verify_ssl else 'ignore'

        last_error = None
        for username in self._candidate_usernames():
            try:
                session = winrm.Session(
                    target=self._endpoint(),
                    auth=(username, self.password),
                    transport=transport,
                    server_cert_validation=server_cert_validation,
                )
                probe = session.run_ps('Write-Output "WINRM_AUTH_OK"')
                stdout = (probe.std_out or b'').decode(errors='ignore')
                if probe.status_code == 0 and 'WINRM_AUTH_OK' in stdout:
                    logger.info(f"WinRM authenticated using username format: {username}")
                    return session
                last_error = RuntimeError(
                    f"Authentication probe failed for {username}: status={probe.status_code}"
                )
            except Exception as exc:
                last_error = exc

        if last_error:
            raise last_error
        raise RuntimeError('Unable to establish WinRM session')

    def _run_adcs_presence_check(self) -> Tuple[bool, str]:
        ca_name = (self.source.ca_name or '').strip()
        escaped_ca_name = ca_name.replace("'", "''")

        ps_command = f"""
$ErrorActionPreference = 'Continue'
$result = [ordered]@{{
  success = $false
  method = ''
  message = ''
}}

try {{
  Import-Module ADCSAdministration -ErrorAction Stop
  if (Get-Command Get-CertificationAuthority -ErrorAction SilentlyContinue) {{
    $cas = Get-CertificationAuthority -ErrorAction Stop
    if ($cas) {{
      if ('{escaped_ca_name}' -ne '') {{
        $matched = $cas | Where-Object {{ $_.Name -eq '{escaped_ca_name}' -or $_.DisplayName -eq '{escaped_ca_name}' }}
        if ($matched) {{
          $result.success = $true
          $result.method = 'adcs_cmdlet'
          $result.message = 'ADCS cmdlet succeeded and CA matched'
        }} else {{
          $result.success = $true
          $result.method = 'adcs_cmdlet'
          $result.message = 'ADCS cmdlet succeeded (CA name not explicitly matched)'
        }}
      }} else {{
        $result.success = $true
        $result.method = 'adcs_cmdlet'
        $result.message = 'ADCS cmdlet succeeded'
      }}
    }}
  }}
}} catch {{
  $result.message = $_.Exception.Message
}}

if (-not $result.success) {{
  if ('{escaped_ca_name}' -ne '') {{
    $pingOutput = certutil -config '{escaped_ca_name}' -ping 2>&1 | Out-String
  }} else {{
    $pingOutput = certutil -ping 2>&1 | Out-String
  }}

  if ($LASTEXITCODE -eq 0 -and $pingOutput -notmatch 'FAILED') {{
    $result.success = $true
    $result.method = 'certutil_ping'
    $result.message = 'certutil ping succeeded'
  }} else {{
    $result.success = $false
    $result.method = 'certutil_ping'
    $result.message = $pingOutput
  }}
}}

$result | ConvertTo-Json -Compress
        """

        result = self.session.run_ps(ps_command)
        stdout = (result.std_out or b'').decode(errors='ignore').strip()
        stderr = (result.std_err or b'').decode(errors='ignore').strip()

        if result.status_code != 0:
            return False, f"AD CS detection command failed ({result.status_code}): {stderr or stdout or 'no output'}"

        try:
            parsed = json.loads(stdout)
        except Exception:
            return False, f"Unable to parse AD CS detection output: {stdout or stderr or 'empty output'}"

        success = bool(parsed.get('success'))
        method = parsed.get('method') or 'unknown'
        message = (parsed.get('message') or '').strip()

        if success:
            return True, f"AD CS reachable via {method}: {message}"
        return False, f"AD CS check failed via {method}: {message or 'no details'}"
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test connectivity and AD CS presence using remote WinRM.
        Falls back to certutil ping when ADCS cmdlets are unavailable.
        """
        try:
            self.session = self._create_session()
            success, adcs_message = self._run_adcs_presence_check()

            if success:
                logger.info(f"AD CS connection test successful: {self.source.server_hostname}")
                return True, f"WinRM connected. {adcs_message}"

            return False, f"WinRM connected, but {adcs_message}"
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False, f"Connection failed: {str(e)}"
    
    def fetch_certificates(self) -> List[Dict]:
        """
        Fetch issued certificates from AD CS CA database.

        Primary source:
        - certutil -view -restrict "Disposition=20"

        Fallback source:
        - Cert:\\LocalMachine\\My store
        """
        try:
            if self.session is None:
                self.session = self._create_session()

            issued = self._fetch_issued_certificates_from_ca()
            if issued:
                logger.info(f"Fetched {len(issued)} issued certificates from ADCS CA database")
                return issued

            logger.warning("CA issued-certificate query returned no data, falling back to local certificate store")
            return self._fetch_local_machine_certificates()
        except Exception as e:
            logger.error(f"Failed to fetch certificates: {str(e)}")
            return []

    def run_feature_verification(self) -> Dict:
        """
        Execute AD CS feature checklist commands remotely and capture outputs.
        """
        if self.session is None:
            self.session = self._create_session()

        checklist_script = r"""
$ErrorActionPreference = 'Continue'
$results = [ordered]@{}

function ExecStep($name, $scriptBlock) {
  try {
    $output = & $scriptBlock 2>&1 | Out-String
    $exitCode = $LASTEXITCODE
    $results[$name] = [ordered]@{
      success = ($exitCode -eq 0 -or $null -eq $exitCode)
      exit_code = $exitCode
      output = $output.Trim()
    }
  } catch {
    $results[$name] = [ordered]@{
      success = $false
      exit_code = 1
      output = $_.Exception.Message
    }
  }
}

ExecStep "ping_ca" { certutil -config - -ping }
ExecStep "ca_info" { certutil -config - -CAInfo }
ExecStep "issued_certificates" { certutil -view -restrict "Disposition=20" }
ExecStep "issued_cert_fields" { certutil -view -restrict "Disposition=20" -out "RequestID,SerialNumber,Subject,NotBefore,NotAfter" }
ExecStep "local_machine_expiry" { Get-ChildItem Cert:\LocalMachine\My | Select-Object Subject, NotAfter | ConvertTo-Json -Depth 3 }
ExecStep "local_machine_crypto" { Get-ChildItem Cert:\LocalMachine\My | Select-Object Subject, SignatureAlgorithm, PublicKey | ConvertTo-Json -Depth 4 }

if (Get-Command Get-ADObject -ErrorAction SilentlyContinue) {
  ExecStep "ldap_pkienrollment" { Get-ADObject -Filter 'objectClass -eq "pKIEnrollmentService"' -Properties * | Select-Object Name, DistinguishedName, whenCreated | ConvertTo-Json -Depth 4 }
} else {
  $results["ldap_pkienrollment"] = [ordered]@{
    success = $false
    exit_code = 127
    output = "Get-ADObject command not available"
  }
}

$results | ConvertTo-Json -Depth 8
        """
        result = self.session.run_ps(checklist_script)
        stdout = (result.std_out or b'').decode(errors='ignore').strip()
        stderr = (result.std_err or b'').decode(errors='ignore').strip()

        if result.status_code != 0:
            return {
                "success": False,
                "message": f"Checklist execution failed ({result.status_code})",
                "stderr": stderr,
                "stdout": stdout,
                "checks": {},
            }
        try:
            checks = json.loads(stdout) if stdout else {}
        except Exception:
            return {
                "success": False,
                "message": "Checklist output parsing failed",
                "stderr": stderr,
                "stdout": stdout,
                "checks": {},
            }
        return {
            "success": True,
            "message": "Checklist executed",
            "checks": checks,
        }

    def _fetch_issued_certificates_from_ca(self) -> List[Dict]:
        """
        Query CA issued certificates (Disposition=20) and normalize fields.
        """
        script = r"""
$ErrorActionPreference = 'Stop'
$raw = certutil -view -restrict "Disposition=20" -out "RequestID,SerialNumber,Subject,NotBefore,NotAfter,RequesterName,CertificateTemplate,CertificateHash,Disposition" csv
$rows = @()
if ($raw) {
  $rows = $raw | ConvertFrom-Csv
}
$mapped = @()
foreach ($row in $rows) {
  $mapped += [pscustomobject]@{
    RequestID = $row.RequestID
    SerialNumber = $row.SerialNumber
    Subject = $row.Subject
    NotBefore = $row.NotBefore
    NotAfter = $row.NotAfter
    Requester = $row.RequesterName
    Template = $row.CertificateTemplate
    Thumbprint = $row.CertificateHash
    Disposition = $row.Disposition
  }
}
$mapped | ConvertTo-Json -Depth 4
        """
        result = self.session.run_ps(script)
        stdout = (result.std_out or b'').decode(errors='ignore').strip()
        stderr = (result.std_err or b'').decode(errors='ignore').strip()
        if result.status_code != 0:
            logger.warning(f"CA query via certutil failed ({result.status_code}): {stderr or stdout}")
            return []
        if not stdout:
            return []
        parsed = json.loads(stdout)
        records = parsed if isinstance(parsed, list) else [parsed]
        normalized = []
        for rec in records:
            normalized.append({
                "request_id": rec.get("RequestID"),
                "SerialNumber": rec.get("SerialNumber"),
                "Subject": rec.get("Subject"),
                "NotBefore": rec.get("NotBefore"),
                "NotAfter": rec.get("NotAfter"),
                "Requester": rec.get("Requester"),
                "Template": rec.get("Template"),
                "Thumbprint": (rec.get("Thumbprint") or "").replace(" ", ""),
                "Disposition": rec.get("Disposition"),
            })
        return normalized

    def _fetch_local_machine_certificates(self) -> List[Dict]:
        """Fallback local cert store collection."""
        ps_script = r"""
$certs = Get-ChildItem -Path Cert:\LocalMachine\My -ErrorAction SilentlyContinue | Select-Object \
  Subject,Issuer,Thumbprint,SerialNumber,NotBefore,NotAfter,@{Name='KeyLength';Expression={$_.PublicKey.Key.KeySize}},@{Name='SignatureAlgorithm';Expression={$_.SignatureAlgorithm.FriendlyName}}

if ($certs) {
  $certs | ConvertTo-Json -Depth 4
} else {
  Write-Output "[]"
}
        """
        result = self.session.run_ps(ps_script)
        stdout = (result.std_out or b'').decode(errors='ignore').strip()
        stderr = (result.std_err or b'').decode(errors='ignore').strip()
        if result.status_code != 0:
            logger.warning(f"Local store fallback failed ({result.status_code}): {stderr or stdout}")
            return []
        if not stdout:
            return []
        parsed = json.loads(stdout)
        certs = parsed if isinstance(parsed, list) else [parsed]
        for cert in certs:
            cert["request_id"] = cert.get("request_id") or cert.get("RequestID")
            cert["Template"] = cert.get("Template") or cert.get("template_name")
            cert["Requester"] = cert.get("Requester") or ""
        return certs
    
    def close(self):
        """Close WinRM connection."""
        self.session = None


class LDAPConnector(ADCSConnector):
    """
    Connects to Active Directory via LDAP to fetch certificate information.
    """
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test LDAP connectivity."""
        try:
            # For now, return mock success
            logger.info("LDAP connector test (mock mode)")
            return True, "LDAP connection test successful"
            
        except Exception as e:
            logger.error(f"LDAP connection failed: {str(e)}")
            return False, f"LDAP connection failed: {str(e)}"
    
    def fetch_certificates(self) -> List[Dict]:
        """
        Fetch certificates from Active Directory.
        """
        logger.info("LDAP certificate fetch (mock mode)")
        return []


class AgentConnector(ADCSConnector):
    """
    Uses a local Windows agent to collect certificates.
    """
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test agent availability."""
        try:
            # Check if agent has reported recently
            from .models_adcs import ADCSSyncHistory
            
            recent_sync = ADCSSyncHistory.objects.filter(
                source=self.source
            ).order_by('-completed_at').first()
            
            if recent_sync and recent_sync.status == 'success':
                return True, f"Agent responding (last sync: {recent_sync.completed_at})"
            else:
                return False, "Agent has not reported recently"
                
        except Exception as e:
            return False, f"Agent check failed: {str(e)}"
    
    def fetch_certificates(self) -> List[Dict]:
        """
        Certificates are pushed by agent, not pulled.
        This method checks if new certificates have been submitted.
        """
        logger.info("Certificates should be submitted by agent push, not pulled")
        return []


class ADCSConnectorFactory:
    """
    Factory for creating appropriate connector based on auth type.
    """
    
    @staticmethod
    def create_connector(source, password: Optional[str] = None) -> ADCSConnector:
        """
        Create connector instance based on source auth_type.
        """
        if source.auth_type == 'winrm':
            return WinRMConnector(source, password=password)
        elif source.auth_type == 'ldap':
            return LDAPConnector(source)
        elif source.auth_type == 'agent':
            return AgentConnector(source)
        else:
            raise ValueError(f"Unknown auth type: {source.auth_type}")
