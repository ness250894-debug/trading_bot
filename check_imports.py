import sys
print(f"Python: {sys.executable}")
try:
    import uvicorn
    print(f"Uvicorn: {uvicorn.__version__}")
except ImportError as e:
    print(f"Uvicorn: Not found ({e})")

try:
    import websockets
    print(f"Websockets: {websockets.__version__}")
except ImportError as e:
    print(f"Websockets: Not found ({e})")

try:
    import wsproto
    print(f"Wsproto: {wsproto.__version__}")
except ImportError as e:
    print(f"Wsproto: Not found ({e})")
