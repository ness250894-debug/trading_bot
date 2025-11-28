"""
Script to rotate encryption keys for API key storage.

Usage:
    1. Generate new encryption key: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    2. Add new key as ENCRYPTION_KEY_NEW in .env
    3. Run this script: python key_rotation.py
    4. After successful rotation, move ENCRYPTION_KEY_NEW to ENCRYPTION_KEY in .env
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import DuckDBHandler
from app.core.encryption import EncryptionHelper

def rotate_keys():
    """Rotate encryption keys for all stored API keys."""
    load_dotenv()
    
    old_key = os.getenv("ENCRYPTION_KEY")
    new_key = os.getenv("ENCRYPTION_KEY_NEW")
    
    if not old_key:
        print("Error: ENCRYPTION_KEY not found in environment")
        return False
    
    if not new_key:
        print("Error: ENCRYPTION_KEY_NEW not found in environment")
        print("Generate a new key and add it to .env as ENCRYPTION_KEY_NEW")
        return False
    
    try:
        # Initialize encryptors
        old_encryptor = EncryptionHelper(key=old_key.encode())
        new_encryptor = EncryptionHelper(key=new_key.encode())
        
        # Get database instance
        db = DuckDBHandler()
        
        # Fetch all API keys
        result = db.conn.execute("SELECT id, user_id, exchange, api_key_encrypted, api_secret_encrypted FROM api_keys WHERE is_active = TRUE").fetchall()
        
        if not result:
            print("No API keys found to rotate")
            return True
        
        print(f"Found {len(result)} API key(s) to rotate")
        
        # Rotate each key
        for row in result:
            key_id, user_id, exchange, old_api_key_enc, old_api_secret_enc = row
            
            try:
                # Decrypt with old key
                api_key_plain = old_encryptor.decrypt(old_api_key_enc)
                api_secret_plain = old_encryptor.decrypt(old_api_secret_enc)
                
                # Encrypt with new key
                new_api_key_enc = new_encryptor.encrypt(api_key_plain)
                new_api_secret_enc = new_encryptor.encrypt(api_secret_plain)
                
                # Update database
                db.conn.execute(
                    "UPDATE api_keys SET api_key_encrypted = ?, api_secret_encrypted = ? WHERE id = ?",
                    [new_api_key_enc, new_api_secret_enc, key_id]
                )
                
                print(f"✓ Rotated keys for user {user_id}, exchange {exchange}")
                
            except Exception as e:
                print(f"✗ Failed to rotate keys for user {user_id}, exchange {exchange}: {e}")
                return False
        
        print(f"\n✓ Successfully rotated {len(result)} API key(s)")
        print("\nNext steps:")
        print("1. Update .env: rename ENCRYPTION_KEY_NEW to ENCRYPTION_KEY")
        print("2. Remove the old ENCRYPTION_KEY value")
        print("3. Restart the application")
        
        return True
        
    except Exception as e:
        print(f"Error during key rotation: {e}")
        return False

if __name__ == "__main__":
    success = rotate_keys()
    sys.exit(0 if success else 1)
