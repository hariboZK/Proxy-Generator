"""
proxy_scraper.py
Multi-source proxy aggregator supporting country-specific and global worldwide proxy lists.
"""

import re
import logging
from typing import Set, List
import requests

logger = logging.getLogger("ProxyScraper")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
HEADERS = {"User-Agent": USER_AGENT}
DEFAULT_TIMEOUT = 7


def fetch_country_proxifly(country_code: str) -> Set[str]:
    """Fetch country-specific proxies from Proxifly repository."""
    results = set()
    url = f"https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/countries/{country_code.upper()}/data.txt"
    try:
        r = requests.get(url, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
        if r.status_code == 200:
            for line in r.text.splitlines():
                line = line.strip()
                if line and "://" in line:
                    results.add(line.lower())
    except Exception as e:
        logger.debug(f"Proxifly ({country_code}) error: {e}")
    return results


def fetch_country_proxyscrape_v3(country_code: str) -> Set[str]:
    """Fetch country-specific proxies from ProxyScrape v3 API."""
    results = set()
    url = f"https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&country={country_code.upper()}&proxy_format=protocolipport&format=text"
    try:
        r = requests.get(url, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
        if r.status_code == 200:
            for line in r.text.splitlines():
                line = line.strip()
                if line and "://" in line:
                    results.add(line.lower())
    except Exception as e:
        logger.debug(f"ProxyScrape v3 ({country_code}) error: {e}")
    return results


def fetch_country_proxyscrape_v2(country_code: str) -> Set[str]:
    """Fetch country-specific proxies from ProxyScrape v2 APIs."""
    results = set()
    for proto in ["http", "socks4", "socks5"]:
        url = f"https://api.proxyscrape.com/v2/?request=displayproxies&protocol={proto}&timeout=10000&country={country_code.upper()}&ssl=all&anonymity=all"
        try:
            r = requests.get(url, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
            if r.status_code == 200:
                for line in r.text.splitlines():
                    line = line.strip()
                    if line and ":" in line:
                        results.add(f"{proto}://{line}".lower())
        except Exception as e:
            logger.debug(f"ProxyScrape v2 ({country_code}-{proto}) error: {e}")
    return results


def fetch_country_geonode(country_code: str) -> Set[str]:
    """Fetch country-specific proxies from Geonode API."""
    results = set()
    url = f"https://proxylist.geonode.com/api/proxy-list?country={country_code.upper()}&limit=500&sort_by=lastChecked&sort_type=desc"
    try:
        r = requests.get(url, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
        if r.status_code == 200:
            data = r.json().get("data", [])
            for item in data:
                ip = item.get("ip")
                port = item.get("port")
                protocols = item.get("protocols", ["http"])
                if ip and port:
                    for proto in protocols:
                        results.add(f"{proto.lower()}://{ip}:{port}".lower())
    except Exception as e:
        logger.debug(f"Geonode ({country_code}) error: {e}")
    return results


def fetch_html_table_by_country(country_code: str) -> Set[str]:
    """Scrape HTML proxy tables filtered by target country code."""
    results = set()
    sites = [
        ("https://free-proxy-list.net/", "http"),
        ("https://www.sslproxies.org/", "http"),
        ("https://socks-proxy.net/", "socks4"),
    ]
    target_cc = country_code.upper()
    for url, default_proto in sites:
        try:
            r = requests.get(url, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
            if r.status_code == 200:
                rows = re.findall(r"<tr><td>([\d\.]+)<\/td><td>(\d+)<\/td><td>([A-Z]{2})<\/td>", r.text)
                for ip, port, code in rows:
                    if code.upper() == target_cc:
                        results.add(f"{default_proto}://{ip}:{port}".lower())
        except Exception as e:
            logger.debug(f"HTML table scraper ({url}) error: {e}")
    return results


# ==========================================
# GLOBAL WORLDWIDE HIGH-VOLUME SOURCES
# ==========================================

def fetch_global_proxyscrape_v3() -> Set[str]:
    """Fetch thousands of global proxies from ProxyScrape v3."""
    results = set()
    url = "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&proxy_format=protocolipport&format=text"
    try:
        r = requests.get(url, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
        if r.status_code == 200:
            for line in r.text.splitlines():
                line = line.strip()
                if line and "://" in line:
                    results.add(line.lower())
    except Exception as e:
        logger.debug(f"ProxyScrape v3 Global error: {e}")
    return results


def fetch_global_monosans() -> Set[str]:
    """Fetch worldwide proxies from Monosans repository."""
    results = set()
    url = "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt"
    try:
        r = requests.get(url, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
        if r.status_code == 200:
            for line in r.text.splitlines():
                line = line.strip()
                if line and "://" in line:
                    results.add(line.lower())
    except Exception as e:
        logger.debug(f"Monosans Global error: {e}")
    return results


def fetch_global_thespeedx() -> Set[str]:
    """Fetch HTTP/SOCKS proxies from TheSpeedX lists."""
    results = set()
    sources = [
        ("http", "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt"),
        ("socks4", "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt"),
        ("socks5", "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt"),
    ]
    for proto, url in sources:
        try:
            r = requests.get(url, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
            if r.status_code == 200:
                for line in r.text.splitlines()[:800]:
                    line = line.strip()
                    if line and ":" in line:
                        results.add(f"{proto}://{line}".lower())
        except Exception as e:
            logger.debug(f"TheSpeedX ({proto}) error: {e}")
    return results


def fetch_global_roosterkid() -> Set[str]:
    """Fetch proxies from RoosterKid open proxy lists."""
    results = set()
    sources = [
        ("http", "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt"),
        ("socks4", "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS4_RAW.txt"),
        ("socks5", "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt"),
    ]
    for proto, url in sources:
        try:
            r = requests.get(url, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
            if r.status_code == 200:
                for line in r.text.splitlines():
                    line = line.strip()
                    if line and ":" in line:
                        results.add(f"{proto}://{line}".lower())
        except Exception as e:
            logger.debug(f"RoosterKid ({proto}) error: {e}")
    return results


def fetch_global_clarketm_and_razvan() -> Set[str]:
    """Fetch additional curated open proxy lists."""
    results = set()
    urls = [
        ("http", "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt"),
        ("http", "https://raw.githubusercontent.com/im-razvan/proxy_list/main/http.txt"),
    ]
    for proto, url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
            if r.status_code == 200:
                for line in r.text.splitlines():
                    line = line.strip()
                    if line and ":" in line and not line.startswith("#"):
                        results.add(f"{proto}://{line}".lower())
        except Exception as e:
            logger.debug(f"Curated list error ({url}): {e}")
    return results


def fetch_global_geonode() -> Set[str]:
    """Fetch worldwide proxies from Geonode API."""
    results = set()
    url = "https://proxylist.geonode.com/api/proxy-list?limit=500&sort_by=lastChecked&sort_type=desc"
    try:
        r = requests.get(url, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
        if r.status_code == 200:
            data = r.json().get("data", [])
            for item in data:
                ip = item.get("ip")
                port = item.get("port")
                protocols = item.get("protocols", ["http"])
                if ip and port:
                    for proto in protocols:
                        results.add(f"{proto.lower()}://{ip}:{port}".lower())
    except Exception as e:
        logger.debug(f"Geonode Global error: {e}")
    return results


def scrape_proxies(target: str = "GLOBAL") -> List[str]:
    """
    Scrape and normalize proxies for target country or worldwide.
    :param target: ISO-2 country code (e.g., 'TR', 'US', 'DE') or 'GLOBAL' / 'ALL'
    :return: Clean list of unique 'protocol://ip:port' proxy URLs
    """
    target = target.strip().upper()
    combined: Set[str] = set()

    if target in ["GLOBAL", "ALL"]:
        sources = [
            ("ProxyScrape v3 Global", fetch_global_proxyscrape_v3),
            ("Monosans Global", fetch_global_monosans),
            ("TheSpeedX Multi-Protocol", fetch_global_thespeedx),
            ("RoosterKid Lists", fetch_global_roosterkid),
            ("Geonode Global API", fetch_global_geonode),
            ("ClarkeTM & Razvan Lists", fetch_global_clarketm_and_razvan),
        ]
    else:
        sources = [
            (f"Proxifly ({target})", lambda: fetch_country_proxifly(target)),
            (f"ProxyScrape v3 ({target})", lambda: fetch_country_proxyscrape_v3(target)),
            (f"ProxyScrape v2 ({target})", lambda: fetch_country_proxyscrape_v2(target)),
            (f"Geonode ({target})", lambda: fetch_country_geonode(target)),
            (f"HTML Tables ({target})", lambda: fetch_html_table_by_country(target)),
        ]

    for name, func in sources:
        try:
            found = func()
            if found:
                logger.info(f"[{name}] Discovered {len(found)} proxies.")
            combined.update(found)
        except Exception as e:
            logger.debug(f"[{name}] failed: {e}")

    pattern = re.compile(r"^(https?|socks4|socks5)://(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{2,5})$", re.IGNORECASE)
    cleaned = []
    for p in sorted(combined):
        p = p.strip()
        if pattern.match(p):
            cleaned.append(p.lower())

    return cleaned


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    t = sys.argv[1] if len(sys.argv) > 1 else "GLOBAL"
    proxies = scrape_proxies(t)
    print(f"\nTotal collected unique proxies for [{t}]: {len(proxies)}")
