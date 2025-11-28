from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"

data = {"sub": "test@example.com"}
expire = datetime.utcnow() + timedelta(minutes=15)
data.update({"exp": expire})

try:
    token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    print(f"Token: {token}")
    
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    print(f"Decoded: {decoded}")
except Exception as e:
    print(f"Error: {e}")
