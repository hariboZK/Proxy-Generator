"""
proxy_checker.py
High-performance multi-threaded proxy validation engine with live IP geolocation and latency measurement.
"""

import sys
import time
import datetime
import concurrent.futures
from urllib.parse import urlparse
from typing import Optional, Dict, Any, List, Callable
import requests

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

GEO_ENDPOINT = "http://ip-api.com/json"
DEFAULT_TIMEOUT = 2.0  # Fast 2-second default verification timeout


def check_proxy(
    proxy_url: str,
    target_country: str = "GLOBAL",
    timeout: float = DEFAULT_TIMEOUT,
    verify_strict_country: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Validate a single proxy, measure latency, and extract geolocation data.
    Returns dictionary with details if successful, otherwise None.
    """
    parsed = urlparse(proxy_url)
    protocol = parsed.scheme.lower()
    host = parsed.hostname
    port = parsed.port

    proxies = {
        "http": proxy_url,
        "https": proxy_url,
    }

    start_time = time.time()
    try:
        r = requests.get(
            GEO_ENDPOINT,
            proxies=proxies,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        latency_ms = int((time.time() - start_time) * 1000)

        if r.status_code == 200:
            data = r.json()
            country_code = data.get("countryCode", "").upper()
            country_name = data.get("country", "Unknown")
            city = data.get("city", "Unknown")
            region = data.get("regionName", "")
            isp = data.get("isp", "Unknown")
            real_ip = data.get("query", host)

            # Strict country check if specific country was requested
            target_upper = target_country.strip().upper()
            if target_upper not in ["GLOBAL", "ALL"] and verify_strict_country:
                if country_code != target_upper:
                    return None

            return {
                "proxy": proxy_url,
                "ip": host,
                "port": port,
                "protocol": protocol,
                "latency_ms": latency_ms,
                "country": country_name,
                "country_code": country_code,
                "city": city,
                "region": region,
                "isp": isp,
                "real_ip": real_ip,
                "working": True,
                "checked_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    except Exception:
        pass

    return None


def check_proxies_pool(
    proxy_list: List[str],
    target_country: str = "GLOBAL",
    max_workers: int = 100,
    timeout: float = DEFAULT_TIMEOUT,
    target_count: int = 0,
    verify_strict_country: bool = True,
    callback: Optional[Callable] = None
) -> List[Dict[str, Any]]:
    """
    Test proxies concurrently using a thread pool.
    If target_count > 0, execution short-circuits as soon as target_count working proxies are gathered.
    Returns list of working proxies sorted by lowest latency.
    """
    working_proxies: List[Dict[str, Any]] = []
    total = len(proxy_list)
    completed = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_proxy = {
            executor.submit(check_proxy, p, target_country, timeout, verify_strict_country): p
            for p in proxy_list
        }

        for future in concurrent.futures.as_completed(future_to_proxy):
            completed += 1
            proxy = future_to_proxy[future]
            try:
                res = future.result()
            except Exception:
                res = None

            if res is not None:
                working_proxies.append(res)

            if callback:
                callback(completed, total, proxy, res, len(working_proxies))

            # Early exit if target working count has been achieved
            if target_count > 0 and len(working_proxies) >= target_count:
                # Cancel remaining pending tasks
                for pending in future_to_proxy:
                    pending.cancel()
                break

    working_proxies.sort(key=lambda x: x["latency_ms"])
    return working_proxies
