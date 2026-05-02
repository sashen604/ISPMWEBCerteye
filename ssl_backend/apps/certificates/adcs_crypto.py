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
import json

logger = logging.getLogger(__name__)

_PLAINTEXT_PREFIX = "ADCSPT1:"


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
    VERSION = 1
    
    @staticmethod
    def _derive_key(secret: bytes, salt: bytes) -> bytes:
        """Derive AES key from secret material and salt."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=ADCSCredentialEncryption.KEY_LENGTH,
            salt=salt,
            iterations=ADCSCredentialEncryption.ITERATIONS,
            backend=default_backend()
        )
        return kdf.derive(secret)

    @staticmethod
    def _get_secret_material() -> bytes:
        """
        Get encryption secret material from dedicated setting.
        """
        secret = getattr(settings, "ADCS_ENCRYPTION_KEY", "") or getattr(settings, "SECRET_KEY", "")
        if not secret:
            raise ValueError("ADCS encryption secret is not configured")
        if secret == "ssl-lifecycle-change-me":
            raise ValueError(
                "Insecure default secret key cannot be used for ADCS credential encryption. "
                "Set DJANGO_SECRET_KEY or ADCS_ENCRYPTION_KEY in the environment or in ssl_backend/.env "
                "(see .env.example); then restart the Django server."
            )
        return secret.encode("utf-8")
    
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
            if plaintext is None:
                raise ValueError("Credential value cannot be empty")
            if getattr(settings, "ADCS_PLAINTEXT_PASSWORDS_DEV", False):
                logger.warning(
                    "ADCS_PLAINTEXT_PASSWORDS_DEV is enabled: storing AD CS password without encryption"
                )
                raw = base64.b64encode(plaintext.encode("utf-8")).decode("ascii")
                return f"{_PLAINTEXT_PREFIX}{raw}"
            secret = ADCSCredentialEncryption._get_secret_material()
            salt = os.urandom(ADCSCredentialEncryption.SALT_LENGTH)
            key = ADCSCredentialEncryption._derive_key(secret, salt)
            nonce = os.urandom(ADCSCredentialEncryption.NONCE_LENGTH)
            cipher = AESGCM(key)
            
            ciphertext = cipher.encrypt(
                nonce,
                plaintext.encode(),
                None  # No additional authenticated data
            )
            
            payload = {
                "v": ADCSCredentialEncryption.VERSION,
                "s": base64.b64encode(salt).decode("utf-8"),
                "n": base64.b64encode(nonce).decode("utf-8"),
                "c": base64.b64encode(ciphertext).decode("utf-8"),
            }
            return base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")
            
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
            if isinstance(encrypted_data, str) and encrypted_data.startswith(_PLAINTEXT_PREFIX):
                b64 = encrypted_data[len(_PLAINTEXT_PREFIX) :]
                return base64.b64decode(b64.encode("ascii")).decode("utf-8")
            secret = ADCSCredentialEncryption._get_secret_material()
            decoded = base64.b64decode(encrypted_data)

            # New format: b64(json({"v","s","n","c"}))
            try:
                payload = json.loads(decoded.decode("utf-8"))
                salt = base64.b64decode(payload["s"])
                nonce = base64.b64decode(payload["n"])
                ciphertext = base64.b64decode(payload["c"])
                key = ADCSCredentialEncryption._derive_key(secret, salt)
                cipher = AESGCM(key)
                plaintext = cipher.decrypt(nonce, ciphertext, None)
                return plaintext.decode("utf-8")
            except Exception:
                # Backward compatibility with legacy format:
                # b64(nonce + ciphertext) using static salt derivation
                legacy_salt = b"ADCS_CREDS_SALT_"
                key = ADCSCredentialEncryption._derive_key(secret, legacy_salt)
                nonce = decoded[:ADCSCredentialEncryption.NONCE_LENGTH]
                ciphertext = decoded[ADCSCredentialEncryption.NONCE_LENGTH:]
                cipher = AESGCM(key)
                plaintext = cipher.decrypt(nonce, ciphertext, None)
                return plaintext.decode("utf-8")
            
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise ValueError(f"Failed to decrypt credentials: {str(e)}")
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Create a hash of the password for audit logging (never store plaintext).
        """
        return hashlib.sha256(password.encode()).hexdigest()
