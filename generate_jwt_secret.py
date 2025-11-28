"""
Script to generate a secure JWT secret key.
Run this once and add the output to your .env file as JWT_SECRET_KEY.
"""
import secrets

# Generate a secure random secret key (32 bytes = 256 bits)
secret_key = secrets.token_hex(32)

print("=== JWT Secret Key Generated ===")
print(f"\nAdd this to your .env file:")
print(f"JWT_SECRET_KEY={secret_key}")
print("\nWARNING: Keep this key secure! If compromised, attackers can generate valid JWT tokens.")
