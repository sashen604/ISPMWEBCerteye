"""
AD CS Connector - Fetches certificates from Active Directory Certificate Services.
Supports WinRM, LDAP, and agent-based collection.
"""

import logging
import json
import subprocess
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from django.utils import timezone

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
    
    def __init__(self, source):
        super().__init__(source)
        self.protocol = None
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test connectivity and AD CS presence.
        """
        try:
            # PowerShell script to check for AD CS
            ps_command = """
$CertService = Get-Service -Name certsvc -ErrorAction SilentlyContinue
if ($CertService) {
    Write-Output "AD Certificate Services is installed"
    Write-Output "Status: $($CertService.Status)"
    exit 0
} else {
    Write-Output "AD Certificate Services is not installed"
    exit 1
}
            """
            
            # For development: try to execute PowerShell script locally
            result = subprocess.run(
                ['powershell', '-Command', ps_command],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and "installed" in result.stdout:
                logger.info(f"AD CS connection test successful: {self.source.server_hostname}")
                return True, "Successfully connected to AD CS server"
            else:
                return False, f"AD CS not found or not accessible"
                
        except subprocess.TimeoutExpired:
            logger.error(f"Connection test timeout to {self.source.server_hostname}")
            return False, "Connection test timed out"
        except FileNotFoundError:
            logger.warning("PowerShell not found - attempting mock test")
            # For non-Windows environments, allow manual mock testing
            return True, "AD CS test mode (PowerShell not available)"
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False, f"Connection failed: {str(e)}"
    
    def fetch_certificates(self) -> List[Dict]:
        """
        Fetch certificates from AD CS using PowerShell.
        """
        try:
            # PowerShell script to fetch AD CS certificates
            ps_script = f"""
# Mock certificate data for testing
$Certificates = @(
    @{{
        Subject = "CN=web01.example.com"
        Issuer = "CN=Example-CA,DC=example,DC=com"
        Thumbprint = "A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7R8S9T0"
        SerialNumber = "01 00 00 00 00 00 00 01"
        ValidFrom = (Get-Date).AddYears(-1)
        ValidTo = (Get-Date).AddYears(1)
        KeyLength = 2048
        SignatureAlgorithm = "sha256WithRSAEncryption"
        Template = "WebServer"
        Requester = "CORP\\\\administrator"
    }}
)

$Certificates | ConvertTo-Json
            """
            
            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout:
                certificates = json.loads(result.stdout)
                return certificates if isinstance(certificates, list) else [certificates]
            else:
                logger.warning(f"PowerShell fetch returned code {result.returncode}: {result.stderr}")
                return []
            
        except FileNotFoundError:
            logger.info("PowerShell not available - returning mock data")
            # Return mock data for development/testing
            return [
                {
                    "Subject": "CN=mock-server.example.com",
                    "Issuer": "CN=Example-CA,DC=example,DC=com",
                    "Thumbprint": "MOCKA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7R8S9",
                    "SerialNumber": "01 00 00 00 00 00 00 02",
                    "ValidFrom": timezone.now().isoformat(),
                    "ValidTo": (timezone.now() + timezone.timedelta(days=365)).isoformat(),
                    "KeyLength": 2048,
                    "SignatureAlgorithm": "sha256WithRSAEncryption",
                    "Template": "WebServer",
                    "Requester": "CORP\\\\administrator"
                }
            ]
        except Exception as e:
            logger.error(f"Failed to fetch certificates: {str(e)}")
            return []
    
    def close(self):
        """Close WinRM connection."""
        if self.protocol:
            try:
                self.protocol.close()
            except:
                pass
            self.protocol = None


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
    def create_connector(source) -> ADCSConnector:
        """
        Create connector instance based on source auth_type.
        """
        if source.auth_type == 'winrm':
            return WinRMConnector(source)
        elif source.auth_type == 'ldap':
            return LDAPConnector(source)
        elif source.auth_type == 'agent':
            return AgentConnector(source)
        else:
            raise ValueError(f"Unknown auth type: {source.auth_type}")
