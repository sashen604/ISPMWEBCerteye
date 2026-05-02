import datetime
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa

def analyze_certificate_health(cert: x509.Certificate) -> dict:
    """
    Analyzes an X.509 certificate for cryptographic weaknesses and returns a health report.
    
    Checks for:
    - Weak signature algorithms (MD5, SHA1)
    - Weak RSA key sizes (< 2048 bits)
    - Validity period (days remaining)
    - Basic extensions (presence of Subject Alternative Name)
    
    Returns:
        dict: A structured JSON-like dictionary with the analysis results.
    """
    issues = []
    
    # 1. Signature Algorithm
    is_weak_algorithm = False
    try:
        hash_algo = cert.signature_hash_algorithm
        if isinstance(hash_algo, (hashes.MD5, hashes.SHA1)):
            is_weak_algorithm = True
            issues.append(f"Weak signature algorithm detected: {hash_algo.name}")
    except Exception:
        # If the algorithm is unsupported or missing
        is_weak_algorithm = True
        issues.append("Unknown, unsupported, or missing signature algorithm")
        
    # 2. Public Key Size
    is_weak_key = False
    try:
        public_key = cert.public_key()
        if isinstance(public_key, rsa.RSAPublicKey):
            if public_key.key_size < 2048:
                is_weak_key = True
                issues.append(f"Weak RSA key size detected: {public_key.key_size} bits (minimum 2048 required)")
        # For non-RSA keys, we assume they are fine unless specifically checked
    except Exception:
        issues.append("Could not extract public key")
            
    # 3. Validity Period
    try:
        # cryptography >= 42.0.0 uses not_valid_after_utc, fallback to not_valid_after
        if hasattr(cert, 'not_valid_after_utc'):
            not_after = cert.not_valid_after_utc
            now = datetime.datetime.now(datetime.timezone.utc)
        else:
            not_after = cert.not_valid_after
            now = datetime.datetime.utcnow()
            
        days_remaining = (not_after - now).days
        
        if days_remaining < 0:
            issues.append(f"Certificate has expired ({abs(days_remaining)} days ago)")
        elif days_remaining < 30:
            issues.append(f"Certificate expires soon ({days_remaining} days remaining)")
    except Exception:
        days_remaining = 0
        issues.append("Could not determine validity period")

    # 4. Basic Extension Validation (SAN)
    try:
        san_ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
        if not san_ext.value:
            issues.append("Subject Alternative Name (SAN) extension is empty")
    except x509.ExtensionNotFound:
        issues.append("Subject Alternative Name (SAN) extension is missing")
    except Exception:
        issues.append("Error reading extensions")

    return {
        "is_weak_algorithm": is_weak_algorithm,
        "is_weak_key": is_weak_key,
        "days_remaining": days_remaining,
        "issues": issues
    }
