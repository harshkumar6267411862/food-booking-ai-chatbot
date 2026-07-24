import time
import subprocess
import sys
import os
import re
import urllib.request
from app.config import settings


def wait_for_server(port: int, max_wait: int = 15) -> bool:
    """Poll localhost until server is responding."""
    for _ in range(max_wait):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1)
            return True
        except Exception:
            time.sleep(1)
    return False


def main():
    print("🚀 Starting MunchBot Server & Public Tunnel...")

    # 1. Start Uvicorn Server (capturing stdout+stderr so we can debug)
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    # 2. Wait until server is actually responding
    print("   Waiting for server to start...", end="", flush=True)
    if not wait_for_server(8000, max_wait=20):
        print("\n❌ Server failed to start! Reading output:")
        out, _ = server_process.communicate(timeout=5)
        print(out.decode("utf-8", errors="ignore"))
        sys.exit(1)
    print(" ✅ Server is UP on http://127.0.0.1:8000")

    authtoken = os.getenv("NGROK_AUTHTOKEN", "").strip()

    # 3a. Use ngrok if authtoken is provided
    if authtoken and authtoken != "YOUR_AUTHTOKEN_HERE":
        try:
            from pyngrok import ngrok
            ngrok.set_auth_token(authtoken)
            tunnel = ngrok.connect(8000)
            public_url = tunnel.public_url.replace("http://", "https://")
            webhook_url = f"{public_url}/webhook"
            print_success(webhook_url)
            server_process.wait()
            return
        except Exception as e:
            print(f"⚠️  Ngrok failed ({e}), falling back to SSH tunnel...")

    # 3b. Zero-signup SSH tunnel (localhost.run)
    print("   Starting SSH tunnel via localhost.run...")
    try:
        ssh_process = subprocess.Popen(
            ["ssh", "-o", "StrictHostKeyChecking=no",
             "-o", "ServerAliveInterval=30",
             "-R", "80:localhost:8000",
             "nokey@localhost.run"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        # Read lines until we find the public URL
        webhook_url = None
        for line in ssh_process.stdout:
            match = re.search(r'https://[a-zA-Z0-9]+\.lhr\.life', line)
            if match:
                webhook_url = f"{match.group(0)}/webhook"
                break

        if not webhook_url:
            print("❌ Could not get public URL from localhost.run tunnel.")
            server_process.terminate()
            return

        # Verify tunnel is actually forwarding before printing
        print("   Verifying tunnel is reachable...", end="", flush=True)
        tunnel_ok = False
        for _ in range(15):
            try:
                urllib.request.urlopen(webhook_url + "?hub.mode=test", timeout=3)
                tunnel_ok = True
                break
            except urllib.error.HTTPError as e:
                if e.code in (403, 405):   # Our server responded (just wrong params) — tunnel works!
                    tunnel_ok = True
                    break
            except Exception:
                time.sleep(1)

        if tunnel_ok:
            print(" ✅ Tunnel verified!")
        else:
            print(" ⚠️  Tunnel may not be stable. Try re-running.")

        print_success(webhook_url)

        try:
            ssh_process.wait()
        except KeyboardInterrupt:
            print("\nStopping...")

    except KeyboardInterrupt:
        print("\nStopping server & tunnel...")
    finally:
        server_process.terminate()
        print("Server stopped.")


def print_success(webhook_url: str):
    print("\n" + "=" * 75)
    print("🎉  SERVER AND PUBLIC TUNNEL ARE LIVE!")
    print("=" * 75)
    print(f"👉  Local Admin Dashboard : http://localhost:8000/admin-dashboard")
    print(f"👉  Public Webhook URL    : {webhook_url}")
    print(f"👉  Meta Verify Token     : {settings.WHATSAPP_VERIFY_TOKEN}")
    print("=" * 75)
    print("\n📋  PASTE THESE INTO META DEVELOPER DASHBOARD → WhatsApp → Configuration:")
    print(f"     Callback URL  →  {webhook_url}")
    print(f"     Verify Token  →  {settings.WHATSAPP_VERIFY_TOKEN}")
    print("\nPress Ctrl+C to stop.\n")


if __name__ == "__main__":
    main()
