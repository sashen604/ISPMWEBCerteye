# PowerShell Agent Configuration Template
# 
# This file should be placed at: powershell/AGENT_CONFIG_TEMPLATE.ps1
# Copy and customize for each Windows server that will submit certificates
#

# ============================================================================
# CONFIGURATION SECTION - CUSTOMIZE FOR YOUR ENVIRONMENT
# ============================================================================

# 1. Backend API Settings
$API_URL = "http://localhost:8000"  # Change to your production URL
$API_ENDPOINT = "$API_URL/api/certificates/collect/"
$AGENT_TOKEN = "YOUR_TOKEN_HERE"    # Generate from Python: AgentAuthenticator().generate_token()

# 2. Agent Identification
$AGENT_NAME = "PowerShell-Agent-Prod-01"  # Unique name for this agent
$SERVER_HOSTNAME = $env:COMPUTERNAME      # Or specify manually if needed

# 3. Certificate Store Settings
$CERT_STORE_PATH = "Cert:\LocalMachine\My"  # Default: Local Machine personal store

# 4. Submission Settings
$BATCH_SIZE = 10                    # Certificates per request
$RETRY_COUNT = 3                    # Retry failed submissions
$RETRY_DELAY = 5                    # Seconds between retries
$ENABLE_LOGGING = $true             # Enable detailed logging

# 5. Scheduling Settings (if running as scheduled task)
$RUN_ON_STARTUP = $false            # Run when system starts
$RUN_FREQUENCY = "HOURLY"           # HOURLY, DAILY, WEEKLY, etc.

# 6. Logging Settings
$LOG_DIR = "C:\Logs\CertEye"        # Directory for log files
$LOG_FILE = "$LOG_DIR\cert-collection-$(Get-Date -Format 'yyyyMMdd').log"

# ============================================================================
# DO NOT MODIFY BELOW THIS LINE (UNLESS YOU KNOW WHAT YOU'RE DOING)
# ============================================================================

# Create log directory if it doesn't exist
if (-not (Test-Path $LOG_DIR)) {
    New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null
}

# Logging function
function Write-Log {
    param(
        [string]$Message,
        [ValidateSet('INFO', 'WARNING', 'ERROR')][string]$Level = 'INFO'
    )
    
    if ($ENABLE_LOGGING) {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $logEntry = "[$timestamp] [$Level] $Message"
        Add-Content -Path $LOG_FILE -Value $logEntry
        Write-Host $logEntry
    }
}

# ============================================================================
# CERTIFICATE COLLECTION LOGIC
# ============================================================================

function Get-CertificatesFromStore {
    Write-Log "Starting certificate collection from $CERT_STORE_PATH" "INFO"
    
    try {
        # Get all certificates
        $certificates = Get-ChildItem -Path $CERT_STORE_PATH -ErrorAction Stop
        Write-Log "Found $($certificates.Count) certificates" "INFO"
        
        # Build certificate objects
        $certObjects = @()
        foreach ($cert in $certificates) {
            try {
                $certObject = @{
                    hostname = $SERVER_HOSTNAME
                    subject = $cert.Subject
                    issuer = $cert.Issuer
                    thumbprint = $cert.Thumbprint
                    valid_from = $cert.NotBefore.ToString("yyyy-MM-ddTHH:mm:ssZ")
                    valid_to = $cert.NotAfter.ToString("yyyy-MM-ddTHH:mm:ssZ")
                    signature_algorithm = $cert.SignatureAlgorithm.FriendlyName
                    key_length = $cert.PublicKey.Key.KeySize
                    certificate_template = ""  # Try to extract template name
                }
                
                # Try to get certificate template name
                $templateExt = $cert.Extensions | Where-Object { 
                    $_.Oid.FriendlyName -eq "Certificate Template Name" 
                }
                if ($templateExt) {
                    $certObject.certificate_template = $templateExt.Format($false)
                }
                
                $certObjects += $certObject
                Write-Log "Processed certificate: $($cert.Subject)" "INFO"
            }
            catch {
                Write-Log "Failed to process certificate $($cert.Subject): $_" "WARNING"
            }
        }
        
        return $certObjects
    }
    catch {
        Write-Log "Error collecting certificates: $_" "ERROR"
        return $null
    }
}

# ============================================================================
# API SUBMISSION LOGIC
# ============================================================================

function Submit-CertificatesToAPI {
    param(
        [Array]$Certificates
    )
    
    if ($Certificates.Count -eq 0) {
        Write-Log "No certificates to submit" "WARNING"
        return $false
    }
    
    # Split into batches if needed
    $batches = @()
    for ($i = 0; $i -lt $Certificates.Count; $i += $BATCH_SIZE) {
        $batch = $Certificates[$i..([Math]::Min($i + $BATCH_SIZE - 1, $Certificates.Count - 1))]
        $batches += , @($batch)
    }
    
    Write-Log "Submitting $($Certificates.Count) certificates in $($batches.Count) batch(es)" "INFO"
    
    $totalSuccess = 0
    $totalFailed = 0
    
    foreach ($batch in $batches) {
        # Build payload
        $payload = @{
            agent_token = $AGENT_TOKEN
            certificates = $batch
        } | ConvertTo-Json -Depth 10
        
        # Attempt submission with retries
        $attempt = 0
        $success = $false
        
        while ($attempt -lt $RETRY_COUNT -and -not $success) {
            try {
                $attempt++
                Write-Log "Submitting batch (attempt $attempt/$RETRY_COUNT)..." "INFO"
                
                $response = Invoke-RestMethod `
                    -Uri $API_ENDPOINT `
                    -Method Post `
                    -Body $payload `
                    -ContentType "application/json" `
                    -TimeoutSec 30 `
                    -ErrorAction Stop
                
                if ($response.success) {
                    Write-Log "Batch submitted successfully: Created=$($response.created), Updated=$($response.updated), Failed=$($response.failed)" "INFO"
                    $totalSuccess += $batch.Count
                    $success = $true
                }
                else {
                    Write-Log "API returned success=false: $($response.message)" "WARNING"
                    $totalFailed += $batch.Count
                    $success = $true  # Don't retry if API returns error (not network issue)
                }
            }
            catch {
                $error_msg = $_.Exception.Message
                Write-Log "Submission attempt $attempt failed: $error_msg" "WARNING"
                
                if ($attempt -lt $RETRY_COUNT) {
                    Write-Log "Waiting $RETRY_DELAY seconds before retry..." "INFO"
                    Start-Sleep -Seconds $RETRY_DELAY
                }
                else {
                    Write-Log "All retry attempts exhausted" "ERROR"
                    $totalFailed += $batch.Count
                }
            }
        }
    }
    
    Write-Log "Submission complete: Success=$totalSuccess, Failed=$totalFailed" "INFO"
    return ($totalFailed -eq 0)
}

# ============================================================================
# VALIDATION LOGIC
# ============================================================================

function Validate-Configuration {
    Write-Log "Validating configuration..." "INFO"
    
    $isValid = $true
    
    # Check token
    if ([string]::IsNullOrWhiteSpace($AGENT_TOKEN) -or $AGENT_TOKEN -eq "YOUR_TOKEN_HERE") {
        Write-Log "ERROR: AGENT_TOKEN not configured" "ERROR"
        $isValid = $false
    }
    
    # Check API URL
    if ([string]::IsNullOrWhiteSpace($API_URL)) {
        Write-Log "ERROR: API_URL not configured" "ERROR"
        $isValid = $false
    }
    
    # Check cert store
    if (-not (Test-Path $CERT_STORE_PATH)) {
        Write-Log "ERROR: Certificate store not found: $CERT_STORE_PATH" "ERROR"
        $isValid = $false
    }
    
    # Check API connectivity
    try {
        Write-Log "Testing API connectivity to $API_URL..." "INFO"
        $response = Invoke-RestMethod -Uri $API_URL -Method Get -TimeoutSec 5 -ErrorAction Stop
        Write-Log "API connectivity test passed" "INFO"
    }
    catch {
        Write-Log "WARNING: Could not reach API at $API_URL" "WARNING"
        # Don't fail validation - might be temporary network issue
    }
    
    return $isValid
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

function Invoke-CertificateCollection {
    Write-Log "============================================" "INFO"
    Write-Log "CertEye Certificate Collection Starting" "INFO"
    Write-Log "Agent: $AGENT_NAME" "INFO"
    Write-Log "Server: $SERVER_HOSTNAME" "INFO"
    Write-Log "============================================" "INFO"
    
    # Validate configuration
    if (-not (Validate-Configuration)) {
        Write-Log "Configuration validation failed. Aborting." "ERROR"
        exit 1
    }
    
    # Get certificates
    $certificates = Get-CertificatesFromStore
    
    if ($null -eq $certificates) {
        Write-Log "Failed to collect certificates. Aborting." "ERROR"
        exit 1
    }
    
    # Submit to API
    $success = Submit-CertificatesToAPI -Certificates $certificates
    
    Write-Log "============================================" "INFO"
    if ($success) {
        Write-Log "Certificate collection COMPLETED successfully" "INFO"
        Write-Log "============================================" "INFO"
        exit 0
    }
    else {
        Write-Log "Certificate collection COMPLETED with errors" "WARNING"
        Write-Log "============================================" "WARNING"
        exit 1
    }
}

# ============================================================================
# EXECUTION
# ============================================================================

# Set error action preference
$ErrorActionPreference = "Continue"

# Run collection
Invoke-CertificateCollection

# ============================================================================
# END OF SCRIPT
# ============================================================================
