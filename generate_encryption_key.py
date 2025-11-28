"""
Script to generate an encryption key for the .env file.
Run this once to generate the ENCRYPTION_KEY.
"""
from cryptography.fernet import Fernet

# Generate a new encryption key
key = Fernet.generate_key()

print("=== Encryption Key Generated ===")
print(f"\nAdd this to your .env file:")
print(f"ENCRYPTION_KEY={key.decode()}")
print("\nWARNING: Keep this key secure! If you lose it, you won't be able to decrypt stored API keys.")
