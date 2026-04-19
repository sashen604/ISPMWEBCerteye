param(
    [string]$CertEyeApiUrl = "http://localhost:5000/api/internal-certificates",
    [string]$StoreLocation = "LocalMachine",
    [string]$StoreName = "My",
    [switch]$IncludeExpired,
    [switch]$SkipSelfSigned,
    [int]$TimeoutSeconds = 15
)

function Get-CertificateTemplate {
    param(
        [System.Security.Cryptography.X509Certificates.X509Certificate2]$Certificate
    )

    $template = $null

    foreach ($ext in $Certificate.Extensions) {
        if ($ext.Oid.Value -eq "1.3.6.1.4.1.311.20.2" -or $ext.Oid.Value -eq "1.3.6.1.4.1.311.21.7") {
            $formatted = $ext.Format($false)
            if ($formatted) {
                $template = $formatted.Trim()
                break
            }
        }
    }

    if (-not $template -and $Certificate.Extensions.Count -gt 0) {
        $template = ($Certificate.Extensions | ForEach-Object { $_.Oid.FriendlyName } | Where-Object { $_ }) -join ", "
    }

    return $template
}

function Send-CertificateToCertEye {
    param(
        [System.Security.Cryptography.X509Certificates.X509Certificate2]$Certificate,
        [string]$ApiUrl,
        [int]$TimeoutSeconds
    )

    $expiryDate = $Certificate.NotAfter.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $serverName = $env:COMPUTERNAME
    $template = Get-CertificateTemplate -Certificate $Certificate

    $payload = @{
        server_name = $serverName
        subject = $Certificate.Subject
        issuer = $Certificate.Issuer
        thumbprint = $Certificate.Thumbprint
        expiry_date = $expiryDate
        certificate_template = $template
    }

    $jsonPayload = $payload | ConvertTo-Json

    try {
        $response = Invoke-RestMethod -Uri $ApiUrl -Method POST -ContentType "application/json" -Body $jsonPayload -TimeoutSec $TimeoutSeconds -ErrorAction Stop
        Write-Host "✓ Sent: $($Certificate.Subject)" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "✗ Failed: $($Certificate.Subject)" -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)"
        return $false
    }
}

$path = "Cert:\$StoreLocation\$StoreName"
Write-Host "Scanning $path..."

$certificates = Get-ChildItem -Path $path

if (-not $IncludeExpired) {
    $certificates = $certificates | Where-Object { $_.NotAfter -gt (Get-Date) }
}

if ($SkipSelfSigned) {
    $certificates = $certificates | Where-Object { $_.Subject -ne $_.Issuer }
}

$total = $certificates.Count
$successCount = 0
$failureCount = 0

foreach ($cert in $certificates) {
    $sent = Send-CertificateToCertEye -Certificate $cert -ApiUrl $CertEyeApiUrl -TimeoutSeconds $TimeoutSeconds
    if ($sent) {
        $successCount++
    }
    else {
        $failureCount++
    }
}

Write-Host ""
Write-Host "--- Summary ---"
Write-Host "Total scanned: $total"
Write-Host "Sent: $successCount"
Write-Host "Failed: $failureCount"
