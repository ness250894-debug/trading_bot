import subprocess
import os
import sys
import time
import webbrowser
import socket

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def start_backend(backend_dir, backend_env):
    print("\n🔹 Starting Backend API...")
    # Use shell=True for Windows to ensure environment is picked up correctly
    backend_cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--ws", "websockets"]
    
    process = subprocess.Popen(
        backend_cmd,
        cwd=backend_dir,
        env=backend_env
    )
    return process

def wait_for_backend(process):
    print("   Waiting for Backend to start...")
    for i in range(10):
        if is_port_open(8000):
            print("   ✅ Backend is ready!")
            return True
        time.sleep(1)
        if process.poll() is not None:
            print("   ❌ Backend failed to start!")
            return False
    print("   ⚠️ Backend taking a while...")
    return True

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, 'backend')
    frontend_dir = os.path.join(root_dir, 'frontend')

    print("🚀 Starting Trading Bot UI...")
    print(f"📂 Root: {root_dir}")

    backend_env = os.environ.copy()
    backend_env['PYTHONPATH'] = backend_dir

    # Start Backend
    backend_process = start_backend(backend_dir, backend_env)
    if not wait_for_backend(backend_process):
        sys.exit(1)

    # Start Frontend
    print("\n🔹 Starting Frontend...")
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir,
        shell=True
    )

    print("\n✅ Services Started!")
    print("👉 Backend: http://localhost:8000/api/health")
    print("👉 Frontend: http://localhost:5173")
    print("\nPress Ctrl+C to stop all services.")

    # Open Browser
    time.sleep(2)
    try:
        webbrowser.open("http://localhost:5173")
    except:
        pass

    try:
        while True:
            time.sleep(1)
            # Check if backend is running
            if backend_process.poll() is not None:
                print("\n♻️ Backend stopped. Restarting...")
                backend_process = start_backend(backend_dir, backend_env)
                wait_for_backend(backend_process)

    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        backend_process.terminate()
        if sys.platform == 'win32':
             subprocess.call(['taskkill', '/F', '/T', '/PID', str(frontend_process.pid)])
             subprocess.call(['taskkill', '/F', '/T', '/PID', str(backend_process.pid)])
        else:
            frontend_process.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
