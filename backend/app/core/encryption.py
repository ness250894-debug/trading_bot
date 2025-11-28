from cryptography.fernet import Fernet
import os
import logging

logger = logging.getLogger("Encryption")

class EncryptionHelper:
    """Helper class for encrypting and decrypting sensitive data using Fernet (AES-256)."""
    
    def __init__(self, key: bytes = None):
        """
        Initialize the encryption helper.
        
        Args:
            key: Encryption key (32 url-safe base64-encoded bytes).
                 If not provided, will try to load from environment variable ENCRYPTION_KEY.
        """
        if key is None:
            key = os.getenv("ENCRYPTION_KEY")
            if key is None:
                raise ValueError("ENCRYPTION_KEY environment variable is not set")
            key = key.encode()
        
        try:
            self.fernet = Fernet(key)
        except Exception as e:
            raise ValueError(f"Invalid encryption key format: {e}")
        
        logger.info("Encryption helper initialized")
    
    @staticmethod
    def generate_key() -> bytes:
        """Generate a new encryption key."""
        return Fernet.generate_key()
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.
        
        Args:
            plaintext: The string to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        try:
            encrypted = self.fernet.encrypt(plaintext.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt a ciphertext string.
        Supports fallback to ENCRYPTION_KEY_OLD for key rotation.
        
        Args:
            ciphertext: The base64-encoded encrypted string
            
        Returns:
            Decrypted plaintext string
        """
        try:
            decrypted = self.fernet.decrypt(ciphertext.encode())
            return decrypted.decode()
        except Exception as e:
            # Try fallback to old key if available (for key rotation)
            old_key = os.getenv("ENCRYPTION_KEY_OLD")
            if old_key:
                try:
                    from cryptography.fernet import Fernet
                    old_fernet = Fernet(old_key.encode())
                    decrypted = old_fernet.decrypt(ciphertext.encode())
                    logger.info("Successfully decrypted with old key (consider re-encrypting)")
                    return decrypted.decode()
                except:
                    pass
            
            logger.error(f"Decryption failed: {e}")
            raise

