# Example JSON Payload from PowerShell Agent

This file contains example JSON payloads that a PowerShell agent can send to the CertEye API.

## Single Certificate Example

```json
{
    "server_name": "SERVER01",
    "subject": "CN=server01.corp.local",
    "issuer": "CN=Corp Issuing CA",
    "thumbprint": "ABC123DEF456789012345678901234567890ABCD",
    "expiry_date": "2025-12-31T23:59:59Z",
    "certificate_template": "WebServer"
}
```

## PowerShell Script Example

Here's a PowerShell script that collects certificate data and sends it to the CertEye API:

```powershell
# PowerShell Script: Send-CertificateToCertEye.ps1
# This script retrieves certificates from the local computer store and sends them to CertEye API

param(
    [string]$CertEyeApiUrl = "http://localhost:5000/api/internal-certificates",
    [string]$CertificateStore = "LocalMachine",
    [string]$CertificatePath = "My"  # "My" is the Personal certificate store
)

function Send-CertificateToCertEye {
    param(
        [System.Security.Cryptography.X509Certificates.X509Certificate2]$Certificate,
        [string]$ApiUrl
    )
    
    # Convert expiry date to ISO 8601 format
    $expiryDate = $Certificate.NotAfter.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    
    # Extract server/computer name
    $serverName = $env:COMPUTERNAME
    
    # Build payload
    $payload = @{
        server_name = $serverName
        subject = $Certificate.Subject
        issuer = $Certificate.Issuer
        thumbprint = $Certificate.Thumbprint
        expiry_date = $expiryDate
        certificate_template = $Certificate.Extensions.Name -join ", "  # Certificate template
    }
    
    # Convert to JSON
    $jsonPayload = $payload | ConvertTo-Json
    
    # Send to API
    try {
        $response = Invoke-WebRequest -Uri $ApiUrl `
            -Method POST `
            -ContentType "application/json" `
            -Body $jsonPayload `
            -ErrorAction Stop
        
        Write-Host "✓ Certificate sent successfully: $($Certificate.Subject)" -ForegroundColor Green
        return $response
    }
    catch {
        Write-Host "✗ Error sending certificate: $($Certificate.Subject)" -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)"
        return $null
    }
}

# Main script
Write-Host "Retrieving certificates from $CertificateStore\$CertificatePath..."

$store = New-Object System.Security.Cryptography.X509Certificates.X509Store($CertificatePath, $CertificateStore)
$store.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadOnly)

$certificates = $store.Certificates

Write-Host "Found $($certificates.Count) certificates`n"

$successCount = 0
$errorCount = 0

foreach ($cert in $certificates) {
    # Skip self-signed root certificates (optional)
    if ($cert.Subject -eq $cert.Issuer) {
        Write-Host "⊘ Skipping self-signed: $($cert.Subject)" -ForegroundColor Yellow
        continue
    }
    
    $response = Send-CertificateToCertEye -Certificate $cert -ApiUrl $CertEyeApiUrl
    if ($response) {
        $successCount++
    }
    else {
        $errorCount++
    }
}

$store.Close()

Write-Host "`n--- Summary ---"
Write-Host "Successfully sent: $successCount"
Write-Host "Failed: $errorCount"
Write-Host "Total: $($certificates.Count)"
## Auto-Collector Script (Recommended)

Use the production-ready auto-collector located at `powershell/AutoCollect-CertEye.ps1`.

### Usage

```powershell
.\powershell\AutoCollect-CertEye.ps1
```

### Parameters

```powershell
.\powershell\AutoCollect-CertEye.ps1 \
  -CertEyeApiUrl "http://localhost:5000/api/internal-certificates" \
  -StoreLocation "LocalMachine" \
  -StoreName "My" \
  -IncludeExpired \
  -SkipSelfSigned \
  -TimeoutSeconds 15
```

### Examples

```powershell
# Send all non-expired certificates from LocalMachine\My
.\powershell\AutoCollect-CertEye.ps1

# Include expired certificates
.\powershell\AutoCollect-CertEye.ps1 -IncludeExpired

# Skip self-signed certificates
.\powershell\AutoCollect-CertEye.ps1 -SkipSelfSigned

# Point to a remote CertEye server
.\powershell\AutoCollect-CertEye.ps1 -CertEyeApiUrl "https://certeye.internal/api/internal-certificates"
```

### Scheduling (Task Scheduler)

Create a daily task:

```powershell
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File C:\\CertEye\\AutoCollect-CertEye.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At 3:00am
Register-ScheduledTask -TaskName "CertEye Auto Collect" -Action $action -Trigger $trigger -RunLevel Highest
```
```

## Batch Send Examples

### Send Multiple Certificates (Sequential)

```powershell
$certs = Get-ChildItem -Path "Cert:\LocalMachine\My"
foreach ($cert in $certs) {
    $payload = @{
        server_name = $env:COMPUTERNAME
        subject = $cert.Subject
        issuer = $cert.Issuer
        thumbprint = $cert.Thumbprint
        expiry_date = $cert.NotAfter.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        certificate_template = "WebServer"
    } | ConvertTo-Json
    
    Invoke-WebRequest -Uri "http://localhost:5000/api/internal-certificates" `
        -Method POST `
        -ContentType "application/json" `
        -Body $payload
}
```

## Expected API Response

### Success Response (201 Created or 200 OK)

```json
{
    "success": true,
    "message": "Certificate stored successfully",
    "certificate": {
        "id": 1,
        "server_name": "SERVER01",
        "subject": "CN=server01.corp.local",
        "issuer": "CN=Corp Issuing CA",
        "thumbprint": "ABC123DEF456789012345678901234567890ABCD",
        "expiry_date": "2025-12-31T23:59:59+00:00",
        "certificate_template": "WebServer",
        "days_to_expiry": 315,
        "risk_level": "NORMAL",
        "is_expired": false,
        "expiry_status": "Expires in 315 days",
        "created_at": "2024-03-19T10:30:00",
        "updated_at": "2024-03-19T10:30:00"
    }
}
```

### Error Response (400 Bad Request)

```json
{
    "success": false,
    "error": "Missing required field: thumbprint"
}
```

## Testing with curl

```bash
# Send a test certificate
curl -X POST http://localhost:5000/api/internal-certificates \
  -H "Content-Type: application/json" \
  -d '{
    "server_name": "SERVER01",
    "subject": "CN=server01.corp.local",
    "issuer": "CN=Corp Issuing CA",
    "thumbprint": "ABC123DEF456789012345678901234567890ABCD",
    "expiry_date": "2025-12-31T23:59:59Z",
    "certificate_template": "WebServer"
  }'

# Get all certificates
curl http://localhost:5000/api/certificates

# Get alerts (expiring in 30 days)
curl http://localhost:5000/api/alerts

# Get alerts (expiring in 60 days)
curl http://localhost:5000/api/alerts?days=60
```

## Date Format

CertEye expects expiry dates in **ISO 8601 format** with UTC timezone:

- Format: `YYYY-MM-DDTHH:MM:SSZ` or `YYYY-MM-DDTHH:MM:SS+00:00`
- Example: `2025-12-31T23:59:59Z`

### Converting from PowerShell

```powershell
# X509Certificate2 object (typical)
$cert.NotAfter.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

# Unix timestamp
[DateTime]::UnixEpoch.AddSeconds($unixTimestamp).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

# DateTime object
$dateTime.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
```
