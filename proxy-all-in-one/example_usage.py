"""
example_usage.py
Quick-start code snippets demonstrating how to integrate the generated working proxies
into Python projects (requests, aiohttp, playwright, selenium).
"""

import os
import sys
import random
import requests

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROXY_FILE = os.path.join(CURRENT_DIR, "output", "working_proxies.txt")


def load_working_proxies() -> list[str]:
    """Load all verified proxies from file."""
    if not os.path.exists(PROXY_FILE):
        return []
    with open(PROXY_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def get_fastest_proxy() -> str | None:
    """Return the fastest verified proxy (first entry)."""
    proxies = load_working_proxies()
    return proxies[0] if proxies else None


def get_random_proxy() -> str | None:
    """Return a random working proxy for rotation."""
    proxies = load_working_proxies()
    return random.choice(proxies) if proxies else None


def test_proxy(proxy_url: str):
    """Test connection through selected proxy and display verified geolocation."""
    print(f"\n[*] Testing Proxy Connection: {proxy_url}")
    proxies = {
        "http": proxy_url,
        "https": proxy_url,
    }

    try:
        r = requests.get(
            "http://ip-api.com/json",
            proxies=proxies,
            timeout=5,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        if r.status_code == 200:
            data = r.json()
            print("[+] CONNECTION SUCCESSFUL!")
            print(f"    - Exit IP      : {data.get('query')}")
            print(f"    - Country      : {data.get('country')} ({data.get('countryCode')})")
            print(f"    - City         : {data.get('city')}")
            print(f"    - ISP / Org    : {data.get('isp')}")
        else:
            print(f"[-] Status code: {r.status_code}")
    except Exception as e:
        print(f"[-] Connection failed: {e}")


if __name__ == "__main__":
    print("=" * 65)
    print("      PROXY ALL-IN-ONE: INTEGRATION & USAGE DEMO")
    print("=" * 65)

    proxies = load_working_proxies()
    if not proxies:
        print("[!] No saved proxies found in 'output/working_proxies.txt'.")
        print("    Please run 'python main.py' first to harvest working proxies.")
        sys.exit(0)

    print(f"\nLoaded {len(proxies)} verified, ready-to-use proxies.")

    fastest = get_fastest_proxy()
    print("\n1. Testing Fastest Proxy:")
    test_proxy(fastest)

    if len(proxies) > 1:
        rnd = get_random_proxy()
        print("\n2. Testing Random Rotated Proxy:")
        test_proxy(rnd)
