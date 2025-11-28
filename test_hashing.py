from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

try:
    hash = pwd_context.hash("testpassword")
    print(f"Hash success: {hash}")
    verify = pwd_context.verify("testpassword", hash)
    print(f"Verify success: {verify}")
except Exception as e:
    print(f"Error: {e}")
