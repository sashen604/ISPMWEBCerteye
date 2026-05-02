"""
SSL/TLS Certificate Parser Module

Extracts certificate metadata (issuer, subject, validity dates, etc.)
from X.509 certificate objects and structures it for database storage.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional

from OpenSSL import crypto


class CertificateParsingError(Exception):
    """Raised when certificate parsing fails."""
    pass


class CertificateParser:
    """
    Parses X.509 certificates and extracts relevant metadata.
    
    Converts OpenSSL certificate objects into structured data
    matching the Certificate model schema.
    """
    
    @staticmethod
    def parse_certificate(cert: crypto.X509, domain: str) -> Dict[str, Any]:
        """
        Parse X.509 certificate and extract all metadata.
        
        Args:
            cert (crypto.X509): OpenSSL certificate object
            domain (str): Domain name the certificate was retrieved from
            
        Returns:
            dict: Dictionary with keys matching Certificate model fields:
                - domain
                - certificate_type
                - issuer
                - subject
                - serial_number
                - signature_algorithm
                - key_length
                - valid_from
                - valid_to
                - days_remaining
                - last_scanned
                
        Raises:
            CertificateParsingError: If required fields cannot be extracted
        """
        try:
            # Extract subject and issuer
            subject = CertificateParser._extract_subject_name(cert.get_subject())
            issuer = CertificateParser._extract_issuer_name(cert.get_issuer())
            
            # Extract dates
            not_before = CertificateParser._parse_asn1_date(cert.get_notBefore())
            not_after = CertificateParser._parse_asn1_date(cert.get_notAfter())
            
            # Calculate days remaining
            now = datetime.now(timezone.utc)
            days_remaining = max(0, (not_after - now).days)
            
            # Extract serial number
            serial_number = str(cert.get_serial_number())
            
            # Extract signature algorithm
            signature_algorithm = cert.get_signature_algorithm().decode('utf-8')
            
            # Extract key length
            key_length = cert.get_pubkey().bits()
            
            # Determine certificate type
            cert_type = CertificateParser._determine_certificate_type(subject)
            san_list = CertificateParser._extract_san_list(cert)
            is_self_signed = subject == issuer
            
            return {
                'domain': domain,
                'certificate_type': cert_type,
                'issuer': issuer,
                'subject': subject,
                'serial_number': serial_number,
                'signature_algorithm': signature_algorithm,
                'key_length': key_length,
                'valid_from': not_before,
                'valid_to': not_after,
                'days_remaining': days_remaining,
                'last_scanned': now,
                'source_type': 'scanner',
                'status': 'active' if not_after > now else 'expired',
                'san_list': san_list,
                'is_self_signed': is_self_signed,
            }
            
        except AttributeError as e:
            raise CertificateParsingError(f"Missing certificate attribute: {str(e)}")
        except Exception as e:
            raise CertificateParsingError(f"Failed to parse certificate: {str(e)}")
    
    @staticmethod
    def _extract_subject_name(subject: crypto.X509Name) -> str:
        """
        Extract subject distinguished name from certificate.
        
        Args:
            subject (crypto.X509Name): Subject component
            
        Returns:
            str: Formatted subject DN (e.g., "CN=example.com, O=Company, C=US")
        """
        components = []
        
        # Common name
        if hasattr(subject, 'CN') and subject.CN:
            components.append(f"CN={subject.CN}")
        
        # Organization
        if hasattr(subject, 'O') and subject.O:
            components.append(f"O={subject.O}")
        
        # Organizational Unit
        if hasattr(subject, 'OU') and subject.OU:
            components.append(f"OU={subject.OU}")
        
        # Locality
        if hasattr(subject, 'L') and subject.L:
            components.append(f"L={subject.L}")
        
        # State/Province
        if hasattr(subject, 'ST') and subject.ST:
            components.append(f"ST={subject.ST}")
        
        # Country
        if hasattr(subject, 'C') and subject.C:
            components.append(f"C={subject.C}")
        
        return ", ".join(components) if components else "Unknown"
    
    @staticmethod
    def _extract_issuer_name(issuer: crypto.X509Name) -> str:
        """
        Extract issuer distinguished name from certificate.
        
        Args:
            issuer (crypto.X509Name): Issuer component
            
        Returns:
            str: Formatted issuer DN
        """
        return CertificateParser._extract_subject_name(issuer)
    
    @staticmethod
    def _parse_asn1_date(asn1_date: bytes) -> datetime:
        """
        Parse ASN.1 time format to Python datetime.
        
        ASN.1 format: YYYYMMDDhhmmssZ (e.g., b'20260101235959Z')
        
        Args:
            asn1_date (bytes): ASN.1 encoded date
            
        Returns:
            datetime: Timezone-aware datetime object in UTC
            
        Raises:
            CertificateParsingError: If date format is invalid
        """
        try:
            date_str = asn1_date.decode('utf-8').rstrip('Z')
            
            # Parse YYYYMMDDHHMMSS format
            dt = datetime.strptime(date_str, '%Y%m%d%H%M%S')
            
            # Make timezone-aware (UTC)
            return dt.replace(tzinfo=timezone.utc)
            
        except (ValueError, UnicodeDecodeError) as e:
            raise CertificateParsingError(f"Cannot parse certificate date '{asn1_date}': {str(e)}")
    
    @staticmethod
    def _determine_certificate_type(subject: str) -> str:
        """
        Determine certificate type from subject DN.
        
        Args:
            subject (str): Subject distinguished name
            
        Returns:
            str: Certificate type ('wildcard', 'single', 'multi-domain', 'self-signed', or 'other')
        """
        if not subject or subject == "Unknown":
            return "other"
        
        subject_upper = subject.upper()
        
        # Self-signed check
        if "CN=" in subject_upper and "SELF" in subject_upper:
            return "self-signed"
        
        # Wildcard check
        if "CN=*" in subject:
            return "wildcard"
        
        # Multi-domain typically has multiple CN or SAN extensions
        # For simplicity, classify as 'single' if single CN, else 'multi-domain'
        cn_count = subject.count("CN=")
        if cn_count > 1:
            return "multi-domain"
        
        return "single"

    @staticmethod
    def _extract_san_list(cert: crypto.X509) -> list:
        """Extract SAN entries from certificate extensions."""
        san_values = []
        try:
            for idx in range(cert.get_extension_count()):
                extension = cert.get_extension(idx)
                if extension.get_short_name().decode("utf-8").lower() == "subjectaltname":
                    san_text = str(extension)
                    parts = [part.strip() for part in san_text.split(",")]
                    for part in parts:
                        if ":" in part:
                            san_values.append(part.split(":", 1)[1].strip())
                        else:
                            san_values.append(part)
        except Exception:
            return []
        return san_values
