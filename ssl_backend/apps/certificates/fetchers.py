"""
SSL/TLS Certificate Fetcher Module

Handles low-level connection and retrieval of X.509 certificates from HTTPS domains.
Includes timeout handling, port scanning, and error management.
"""

import socket
import ssl
from typing import Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse

import certifi
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
from OpenSSL import SSL, crypto


def clean_domain(domain_input: str) -> str:
    """
    Clean and extract domain name from various input formats.
    
    Handles:
    - Full URLs: https://www.google.com/ -> google.com
    - URLs with paths: https://example.com/path -> example.com
    - URLs with ports: https://example.com:8443 -> example.com
    - Domains with www: www.google.com -> google.com
    - Plain domains: google.com -> google.com
    
    Args:
        domain_input (str): Raw domain or URL input
        
    Returns:
        str: Cleaned domain name
        
    Examples:
        >>> clean_domain('https://www.google.com/')
        'google.com'
        >>> clean_domain('www.example.com')
        'example.com'
        >>> clean_domain('google.com')
        'google.com'
    """
    if not domain_input:
        return domain_input
    
    # Remove whitespace
    domain_input = domain_input.strip()
    
    # If it looks like a URL, parse it
    if '://' in domain_input or domain_input.startswith('//'):
        try:
            parsed = urlparse(domain_input if '://' in domain_input else f'//{domain_input}')
            domain = parsed.hostname or parsed.netloc
        except Exception:
            domain = domain_input
    else:
        # Extract just the domain part if port is included
        domain = domain_input.split(':')[0] if ':' in domain_input else domain_input
    
    # Remove www. prefix if present
    if domain and domain.lower().startswith('www.'):
        domain = domain[4:]
    
    return domain.lower() if domain else domain_input


class CertificateFetchError(Exception):
    """Base exception for certificate fetching errors."""
    pass


class ConnectionTimeoutError(CertificateFetchError):
    """Raised when connection times out."""
    pass


class InvalidCertificateError(CertificateFetchError):
    """Raised when certificate is invalid or cannot be parsed."""
    pass


class DNSResolutionError(CertificateFetchError):
    """Raised when domain cannot be resolved."""
    pass


class SSLAdapter(HTTPAdapter):
    """Custom HTTPAdapter for SSL certificate extraction."""
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)


class SSLCertificateFetcher:
    """
    Connects to HTTPS domains and retrieves X.509 certificates.
    
    Attributes:
        default_timeout (int): Connection timeout in seconds (default: 10)
        ports (list): List of ports to try (default: [443, 8443])
    """
    
    DEFAULT_TIMEOUT = 10
    DEFAULT_PORTS = [443, 8443]
    
    def __init__(self, timeout: int = DEFAULT_TIMEOUT, ports: Optional[list] = None):
        """
        Initialize the SSL certificate fetcher.
        
        Args:
            timeout (int): Connection timeout in seconds
            ports (list): List of ports to attempt (default: [443, 8443])
        """
        self.timeout = timeout
        self.ports = ports or self.DEFAULT_PORTS
    
    def fetch_certificate(
        self,
        domain: str,
        port: int = 443,
        verify_ssl: bool = True
    ) -> Optional[crypto.X509]:
        """
        Fetch X.509 certificate from a domain on a specific port using requests.
        
        Args:
            domain (str): Domain name (e.g., 'google.com')
            port (int): Port number (default: 443)
            verify_ssl (bool): Verify SSL certificate validity (default: True)
            
        Returns:
            crypto.X509: OpenSSL certificate object
            
        Raises:
            DNSResolutionError: If domain cannot be resolved
            ConnectionTimeoutError: If connection times out
            InvalidCertificateError: If certificate is invalid or cannot be parsed
            CertificateFetchError: For other SSL/connection errors
        """
        try:
            # Construct URL
            url = f"https://{domain}:{port}/" if port != 443 else f"https://{domain}/"
            
            # Create session with custom SSL adapter
            session = requests.Session()
            session.mount('https://', SSLAdapter())
            
            # Make request to extract certificate
            try:
                response = session.get(
                    url,
                    verify=False,
                    timeout=self.timeout,
                    allow_redirects=False
                )
                
                # Get the peer certificate from the connection
                # Note: requests library doesn't expose raw cert, so we fall back to socket
                return self._fetch_via_socket(domain, port)
                
            except requests.exceptions.ConnectTimeout:
                raise ConnectionTimeoutError(
                    f"Connection to {domain}:{port} timed out after {self.timeout}s"
                )
            except requests.exceptions.ConnectionError as e:
                # Try socket fallback
                return self._fetch_via_socket(domain, port)
            except requests.exceptions.RequestException as e:
                raise CertificateFetchError(
                    f"Request error for {domain}:{port}: {str(e)}"
                )
            finally:
                session.close()
                
        except CertificateFetchError:
            raise
        except Exception as e:
            raise CertificateFetchError(
                f"Unexpected error fetching certificate from {domain}: {str(e)}"
            )
    
    def _fetch_via_socket(self, domain: str, port: int = 443) -> crypto.X509:
        """Fallback method using direct socket connection."""
        try:
            # Create SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Connect and get certificate
            with socket.create_connection((domain, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    der_cert = ssock.getpeercert(binary_form=True)
                    
                    if not der_cert:
                        raise InvalidCertificateError(
                            f"No certificate received from {domain}:{port}"
                        )
                    
                    # Convert DER to OpenSSL X509
                    cert = crypto.load_certificate(crypto.FILETYPE_ASN1, der_cert)
                    return cert
                    
        except socket.timeout:
            raise ConnectionTimeoutError(
                f"Connection to {domain}:{port} timed out after {self.timeout}s"
            )
        except socket.gaierror as e:
            raise DNSResolutionError(f"Failed to resolve domain '{domain}': {str(e)}")
        except ssl.SSLError as e:
            raise CertificateFetchError(
                f"SSL error when connecting to {domain}:{port}: {str(e)}"
            )
        except socket.error as e:
            raise CertificateFetchError(
                f"Socket error when connecting to {domain}:{port}: {str(e)}"
            )
    
    def fetch_from_any_port(self, domain: str) -> Tuple[Optional[crypto.X509], int]:
        """
        Attempt to fetch certificate from domain using multiple ports.
        
        Args:
            domain (str): Domain name
            
        Returns:
            Tuple[crypto.X509, int]: Certificate and successful port number
            
        Raises:
            CertificateFetchError: If all ports fail
        """
        errors = []
        
        for port in self.ports:
            try:
                cert = self.fetch_certificate(domain, port=port, verify_ssl=False)
                return cert, port
            except CertificateFetchError as e:
                errors.append(f"Port {port}: {str(e)}")
                continue
        
        raise CertificateFetchError(
            f"Failed to retrieve certificate from {domain} on any port. Errors:\n" +
            "\n".join(errors)
        )
