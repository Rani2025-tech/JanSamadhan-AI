import os
import sys
import subprocess
import signal
import time
from pathlib import Path
from threading import Thread

# Support UTF-8 console output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent
DB_FILE = ROOT_DIR / "jansamadhan.db"
ENV_FILE = ROOT_DIR / ".env"
ENV_EXAMPLE = ROOT_DIR / ".env.example"

def stream_output(process, prefix, color_code):
    reset_code = "\033[0m"
    try:
        for line in iter(process.stdout.readline, b""):
            decoded = line.decode("utf-8", errors="replace").rstrip()
            if decoded:
                print(f"{color_code}[{prefix}]{reset_code} {decoded}", flush=True)
    except Exception:
        pass

def main():
    # 1. Ensure .env exists
    if not ENV_FILE.exists() and ENV_EXAMPLE.exists():
        print("[SETUP] Creating .env from .env.example...")
        ENV_FILE.write_text(ENV_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")

    # 2. Ensure database is seeded
    if not DB_FILE.exists():
        print("[SETUP] Database not found. Seeding initial demo data...")
        subprocess.run([sys.executable, str(ROOT_DIR / "backend" / "seed.py")], check=True)

    print("\n" + "=" * 60)
    print("  * JANSAMADHAN - STARTING FULL-STACK LOCAL ENVIRONMENT")
    print("=" * 60)
    print("  * Backend:  http://127.0.0.1:8000 (Docs: http://127.0.0.1:8000/docs)")
    print("  * Frontend: http://localhost:3000")
    print("  * Press Ctrl+C at any time to stop both servers.")
    print("=" * 60 + "\n")

    # Determine npm executable for Windows vs Unix
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"

    # Start FastAPI backend
    backend_env = os.environ.copy()
    backend_env["PYTHONUNBUFFERED"] = "1"
    backend_proc = subprocess.Popen(
        [sys.executable, str(ROOT_DIR / "backend" / "main.py")],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=str(ROOT_DIR),
        env=backend_env
    )

    # Start Vite frontend
    frontend_proc = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=str(ROOT_DIR),
        shell=(sys.platform == "win32")
    )

    # Magenta for backend, Cyan for frontend
    backend_thread = Thread(target=stream_output, args=(backend_proc, "BACKEND", "\033[95m"), daemon=True)
    frontend_thread = Thread(target=stream_output, args=(frontend_proc, "FRONTEND", "\033[96m"), daemon=True)

    backend_thread.start()
    frontend_thread.start()

    def cleanup(signum=None, frame=None):
        print("\n[STOPPING] Terminating Backend and Frontend...")
        try:
            backend_proc.terminate()
            backend_proc.kill()
        except Exception:
            pass
        try:
            frontend_proc.terminate()
            frontend_proc.kill()
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, cleanup)

    try:
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None:
                print(f"[BACKEND] Exited with code {backend_proc.returncode}")
                cleanup()
            if frontend_proc.poll() is not None:
                print(f"[FRONTEND] Exited with code {frontend_proc.returncode}")
                cleanup()
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()
