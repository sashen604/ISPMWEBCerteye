"""
Encryption module for secure AD CS credential storage.
Uses AES-256-GCM with PBKDF2 key derivation.
"""

from django.conf import settings
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import os
import base64
import logging
import hashlib

logger = logging.getLogger(__name__)


class ADCSCredentialEncryption:
    """
    Handles encryption and decryption of AD CS credentials.
    Uses AES-256-GCM with PBKDF2 key derivation.
    """
    
    # Encryption parameters
    KEY_LENGTH = 32  # 256 bits for AES-256
    NONCE_LENGTH = 12  # 96 bits for GCM
    TAG_LENGTH = 16  # 128 bits for GCM auth tag
    SALT_LENGTH = 16  # 128 bits for PBKDF2
    ITERATIONS = 100000  # PBKDF2 iterations
    
    @staticmethod
    def get_encryption_key():
        """
        Derive encryption key from Django SECRET_KEY using PBKDF2.
        """
        secret = settings.SECRET_KEY.encode()
        salt = b'ADCS_CREDS_SALT_'  # Fixed salt for consistent key derivation
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=ADCSCredentialEncryption.KEY_LENGTH,
            salt=salt,
            iterations=ADCSCredentialEncryption.ITERATIONS,
            backend=default_backend()
        )
        key = kdf.derive(secret)
        return key
    
    @staticmethod
    def encrypt(plaintext: str) -> str:
        """
        Encrypt a string using AES-256-GCM.
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Base64-encoded encrypted string (nonce + ciphertext + tag)
        """
        try:
            key = ADCSCredentialEncryption.get_encryption_key()
            nonce = os.urandom(ADCSCredentialEncryption.NONCE_LENGTH)
            cipher = AESGCM(key)
            
            ciphertext = cipher.encrypt(
                nonce,
                plaintext.encode(),
                None  # No additional authenticated data
            )
            
            # Combine nonce + ciphertext + tag
            encrypted_data = nonce + ciphertext
            
            # Encode as base64 for storage
            encoded = base64.b64encode(encrypted_data).decode('utf-8')
            return encoded
            
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise ValueError(f"Failed to encrypt credentials: {str(e)}")
    
    @staticmethod
    def decrypt(encrypted_data: str) -> str:
        """
        Decrypt an AES-256-GCM encrypted string.
        
        Args:
            encrypted_data: Base64-encoded encrypted string
            
        Returns:
            Decrypted plaintext string
        """
        try:
            key = ADCSCredentialEncryption.get_encryption_key()
            
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            # Extract nonce and ciphertext
            nonce = encrypted_bytes[:ADCSCredentialEncryption.NONCE_LENGTH]
            ciphertext = encrypted_bytes[ADCSCredentialEncryption.NONCE_LENGTH:]
            
            cipher = AESGCM(key)
            plaintext = cipher.decrypt(nonce, ciphertext, None)
            
            return plaintext.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise ValueError(f"Failed to decrypt credentials: {str(e)}")
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Create a hash of the password for audit logging (never store plaintext).
        """
        return hashlib.sha256(password.encode()).hexdigest()
