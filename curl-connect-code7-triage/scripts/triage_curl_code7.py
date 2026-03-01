#!/usr/bin/env python3
import argparse
import json
import socket
import subprocess
import time
from urllib.parse import urlparse


def is_listening(host: str, port: int, timeout: float = 0.35) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        return True
    except Exception:
        return False
    finally:
        s.close()


def curl_ok(url: str) -> bool:
    cmd = ["curl", "-fsS", "--max-time", "2", url]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return p.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Triage repeated curl (7) connect failures.")
    parser.add_argument("--url", required=True, help="Target URL, e.g. http://127.0.0.1:5173/")
    parser.add_argument("--timeout", type=int, default=20, help="Wait timeout in seconds")
    parser.add_argument("--interval", type=float, default=1.0, help="Probe interval in seconds")
    args = parser.parse_args()

    u = urlparse(args.url)
    if u.scheme not in ("http", "https"):
        raise SystemExit("Only http/https URLs are supported")
    host = u.hostname or "127.0.0.1"
    port = u.port or (443 if u.scheme == "https" else 80)

    started = time.time()
    first_listen = is_listening(host, port)
    if first_listen and curl_ok(args.url):
        result = {
            "status": "READY_NOW",
            "host": host,
            "port": port,
            "url": args.url,
            "recommendation": "服务已可访问，继续后续步骤。",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    seen_listen = first_listen
    while time.time() - started < args.timeout:
        if is_listening(host, port):
            seen_listen = True
            if curl_ok(args.url):
                result = {
                    "status": "BECAME_READY",
                    "host": host,
                    "port": port,
                    "url": args.url,
                    "recommendation": "服务是延迟启动；后续探测先等待再 curl。",
                }
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 0
        time.sleep(args.interval)

    status = "NOT_LISTENING" if not seen_listen else "STILL_UNREACHABLE"
    recommendation = (
        "端口未监听：先启动服务或修正端口配置。"
        if status == "NOT_LISTENING"
        else "端口有监听但 HTTP 仍失败：检查 host/port、反向代理、容器映射与服务日志。"
    )
    result = {
        "status": status,
        "host": host,
        "port": port,
        "url": args.url,
        "timeout": args.timeout,
        "recommendation": recommendation,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
