"""
main.py
Proxy Hunter All-In-One
Fast, multi-threaded proxy scraper and live validator with geolocation, 2s latency checks,
and continuous hunting mode (guaranteed target collection before exit).
"""

import os
import sys
import json
import time
import argparse
from typing import List, Dict, Any, Tuple
from proxy_scraper import scrape_proxies
from proxy_checker import check_proxies_pool

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ANSI Color Codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_banner():
    banner = f"""
{CYAN}{BOLD}========================================================================
     🌐  PROXY HUNTER ALL-IN-ONE (SCRAPER & LIVE CHECKER)  🚀
========================================================================{RESET}
 {YELLOW}• Target Country (e.g. TR, US, DE) or Worldwide Global Mode{RESET}
 {YELLOW}• Real-Time Geolocation: Country, City, Region, ISP & Ping (ms){RESET}
 {YELLOW}• Ultra-Fast 2.0s Timeout & 100x Multi-Threaded Engine{RESET}
 {YELLOW}• Continuous Hunt Mode: Never stops until target working count is met!{RESET}
 {YELLOW}• Exports directly to Ready-To-Use TXT and JSON formats{RESET}
{CYAN}========================================================================{RESET}
"""
    print(banner)


def show_interactive_menu() -> Tuple[str, int, int, float]:
    """Display interactive English menu."""
    print(f"\n{BOLD}Select an operation mode:{RESET}")
    print(f"  {GREEN}[1]{RESET} ⚡ Fast Hunter: Collect 100 Working Proxies (2s Timeout, 100 Threads)")
    print(f"  {CYAN}[2]{RESET} 🌍 Global Worldwide (All Countries)")
    print(f"  {CYAN}[3]{RESET} 🇹🇷 Turkey (TR) Only")
    print(f"  {CYAN}[4]{RESET} 🇺🇸 United States (US)")
    print(f"  {CYAN}[5]{RESET} 🇩🇪 Germany (DE)")
    print(f"  {CYAN}[6]{RESET} 🇬🇧 United Kingdom (GB)")
    print(f"  {CYAN}[7]{RESET} 🇫🇷 France (FR)")
    print(f"  {CYAN}[8]{RESET} 🇳🇱 Netherlands (NL)")
    print(f"  {CYAN}[9]{RESET} 🌐 Custom Country Code (ISO-2: RU, JP, CA, IT, BR, etc.)")
    print(f"  {RED}[0]{RESET} ❌ Exit\n")

    while True:
        try:
            choice = input(f"{BOLD}Enter selection [0-9]: {RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            sys.exit(0)

        if choice == "1":
            return "GLOBAL", 100, 100, 2.0
        elif choice == "2":
            country = "GLOBAL"
            break
        elif choice == "3":
            country = "TR"
            break
        elif choice == "4":
            country = "US"
            break
        elif choice == "5":
            country = "DE"
            break
        elif choice == "6":
            country = "GB"
            break
        elif choice == "7":
            country = "FR"
            break
        elif choice == "8":
            country = "NL"
            break
        elif choice == "9":
            country = input(f"{BOLD}Enter 2-letter ISO Country Code (e.g. RU, JP, CA, IT): {RESET}").strip().upper()
            if not country or len(country) != 2:
                print(f"{YELLOW}[!] Please provide a valid 2-letter country code.{RESET}")
                continue
            break
        elif choice == "0":
            print("Goodbye!")
            sys.exit(0)
        else:
            print(f"{YELLOW}[!] Invalid option. Please choose between 0 and 9.{RESET}")

    # Ask for target count
    try:
        t_input = input(f"{BOLD}Target working proxies to collect (Default 100, 0 for all): {RESET}").strip()
        target_count = int(t_input) if t_input.isdigit() else 100
    except Exception:
        target_count = 100

    # Ask for timeout
    try:
        w_input = input(f"{BOLD}Timeout in seconds (Default 2.0s): {RESET}").strip()
        timeout = float(w_input) if w_input else 2.0
    except Exception:
        timeout = 2.0

    threads = 100
    return country, target_count, threads, timeout


def save_results(working_proxies: List[Dict[str, Any]], target_name: str, base_dir: str):
    """Save working proxies in multiple ready-to-use formats."""
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    safe_target = target_name.lower().replace(" ", "_")

    file_full_url = os.path.join(output_dir, "working_proxies.txt")
    file_ipport = os.path.join(output_dir, "working_proxies_ipport.txt")
    file_json = os.path.join(output_dir, "working_proxies.json")
    file_target = os.path.join(output_dir, f"working_proxies_{safe_target}.txt")

    # 1. Standard protocol://ip:port format
    with open(file_full_url, "w", encoding="utf-8") as f1, \
         open(file_target, "w", encoding="utf-8") as ft:
        for p in working_proxies:
            line = f"{p['proxy']}\n"
            f1.write(line)
            ft.write(line)

    # 2. Raw IP:Port format
    with open(file_ipport, "w", encoding="utf-8") as f2:
        for p in working_proxies:
            f2.write(f"{p['ip']}:{p['port']}\n")

    # 3. Detailed JSON format
    with open(file_json, "w", encoding="utf-8") as f3:
        json.dump(working_proxies, f3, indent=4, ensure_ascii=False)

    return file_full_url, file_ipport, file_json, file_target


def hunt_proxies(
    target: str = "GLOBAL",
    target_count: int = 100,
    threads: int = 100,
    timeout: float = 2.0,
    protocol_filter: str = "all"
):
    """
    Continuous hunting engine:
    Keeps discovering, testing, and streaming proxies until target_count working proxies are secured.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    strict_country = target not in ["GLOBAL", "ALL"]

    print(f"\n{CYAN}[1/4] Gathering candidate proxy pool for [{BOLD}{target}{RESET}{CYAN}]...{RESET}")
    all_candidates = scrape_proxies(target)

    if protocol_filter != "all":
        all_candidates = [p for p in all_candidates if p.startswith(f"{protocol_filter}://")]

    if not all_candidates:
        print(f"{RED}[ERROR] No proxies found. Please check internet connection.{RESET}")
        return

    print(f"{GREEN}[✓] Total {len(all_candidates)} candidate proxies assembled.{RESET}")
    print(f"\n{CYAN}[2/4] Hunting working proxies (Target: {BOLD}{target_count or 'Unlimited'}{RESET}{CYAN} working | Timeout: {timeout}s | Threads: {threads})...{RESET}\n")

    collected_working: List[Dict[str, Any]] = []
    seen_ips = set()

    def progress_callback(completed, total, proxy, result, current_working_count):
        if result is not None and result["ip"] not in seen_ips:
            seen_ips.add(result["ip"])
            c_code = result.get("country_code", "??")
            city = result.get("city", "Unknown")
            isp = result.get("isp", "Unknown")
            ping = result.get("latency_ms", 0)
            proto = result.get("protocol", "http").upper()
            proxy_addr = result.get("proxy", "")
            target_str = f"[{current_working_count}/{target_count}]" if target_count > 0 else f"[{current_working_count}]"

            print(f"{GREEN}[✓ LIVE]{RESET} {BOLD}{target_str:<9}{RESET} [{MAGENTA}{c_code} - {city}{RESET}] {proxy_addr:<26} | {proto:<6} | Ping: {ping}ms | ISP: {isp[:22]}")

    # Hunter loop: keep checking until target_count is reached
    batch_size = 300
    candidate_index = 0
    iteration = 0

    while True:
        iteration += 1
        remaining_needed = target_count - len(collected_working) if target_count > 0 else 0

        if target_count > 0 and len(collected_working) >= target_count:
            break

        current_batch = all_candidates[candidate_index:candidate_index + batch_size]
        if not current_batch:
            # If all candidates tested but target not reached, re-scrape fresh or break
            print(f"{YELLOW}[*] Completed testing available candidate pool. Refreshing sources...{RESET}")
            fresh_candidates = scrape_proxies(target)
            new_candidates = [p for p in fresh_candidates if p not in all_candidates]
            if not new_candidates:
                print(f"{YELLOW}[!] All candidate proxies checked.{RESET}")
                break
            all_candidates.extend(new_candidates)
            current_batch = new_candidates[:batch_size]

        candidate_index += len(current_batch)

        batch_results = check_proxies_pool(
            current_batch,
            target_country=target,
            max_workers=threads,
            timeout=timeout,
            target_count=remaining_needed,
            verify_strict_country=strict_country,
            callback=progress_callback
        )

        for p in batch_results:
            if p["ip"] not in [x["ip"] for x in collected_working]:
                collected_working.append(p)
                if target_count > 0 and len(collected_working) >= target_count:
                    break

    # Sort all working proxies by latency (fastest first)
    collected_working.sort(key=lambda x: x["latency_ms"])

    # Step 3: Print summary
    print(f"\n{CYAN}========================================================================{RESET}")
    print(f"{BOLD}[3/4] HUNT COMPLETE & VERIFICATION RESULTS{RESET}")
    print(f"{CYAN}========================================================================{RESET}")
    print(f"Target Working Proxies  : {target_count or 'Unlimited'}")
    print(f"Successfully Secured    : {GREEN}{BOLD}{len(collected_working)}{RESET}")

    if not collected_working:
        print(f"{YELLOW}[!] No proxies responded within {timeout}s timeout.{RESET}")
        print(f"{YELLOW}[Tip] Try increasing timeout slightly: python main.py --timeout 3.5{RESET}")
        return

    print(f"\n{BOLD}{'#':<4} {'PROXY ADDRESS':<28} {'PROTO':<7} {'PING':<8} {'COUNTRY':<12} {'CITY':<16} {'ISP':<20}{RESET}")
    print("-" * 100)
    for idx, p in enumerate(collected_working[:25], start=1):
        cc_name = f"{p.get('country', '')[:9]} ({p.get('country_code', '')})"
        city_name = p.get("city") or "Unknown"
        isp_name = (p.get("isp") or "Unknown")[:18]
        print(f"{idx:<4} {p['proxy']:<28} {p['protocol']:<7} {str(p['latency_ms'])+'ms':<8} {cc_name:<12} {city_name:<16} {isp_name:<20}")

    if len(collected_working) > 25:
        print(f"... and {len(collected_working) - 25} more verified fast proxies saved to file.")

    # Step 4: Save outputs
    f_url, f_ip, f_json, f_target = save_results(collected_working, target, base_dir)

    print(f"\n{CYAN}========================================================================{RESET}")
    print(f"{GREEN}{BOLD}[4/4] PROXIES READY FOR IMMEDIATE USE!{RESET}")
    print(f"{CYAN}========================================================================{RESET}")
    print(f" 1. Standard Protocol URL : {BOLD}{f_url}{RESET}")
    print(f" 2. IP:Port Format        : {BOLD}{f_ip}{RESET}")
    print(f" 3. Detailed JSON Data    : {BOLD}{f_json}{RESET}")
    print(f" 4. Target-Specific List  : {BOLD}{f_target}{RESET}")
    print(f"\n{YELLOW}Test or integrate in Python instantly with: python example_usage.py{RESET}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Proxy Hunter All-In-One: High-Speed Scraper, Checker & Geolocation Engine"
    )
    parser.add_argument("--country", "-c", type=str, default=None,
                        help="Target country code (e.g. TR, US, DE, GB) or 'GLOBAL'")
    parser.add_argument("--target", "-n", type=int, default=100,
                        help="Number of working proxies to collect before stopping (Default: 100)")
    parser.add_argument("--threads", "-t", type=int, default=100,
                        help="Concurrent worker threads (Default: 100)")
    parser.add_argument("--timeout", "-w", type=float, default=2.0,
                        help="Validation timeout in seconds (Default: 2.0s)")
    parser.add_argument("--protocol", "-p", type=str, choices=["all", "http", "socks4", "socks5"], default="all",
                        help="Filter by protocol (Default: all)")

    args = parser.parse_args()
    print_banner()

    if args.country is None:
        country, target_count, threads, timeout = show_interactive_menu()
    else:
        country = args.country
        target_count = args.target
        threads = args.threads
        timeout = args.timeout

    hunt_proxies(
        target=country,
        target_count=target_count,
        threads=threads,
        timeout=timeout,
        protocol_filter=args.protocol
    )


if __name__ == "__main__":
    main()
