#!/usr/bin/env python3
"""
MultiDork - CLI Interface
Automated multi-engine dorking tool for VAPT
"""

import argparse
import sys
from colorama import Fore, Style, init
from engines import ENGINES, run_all_engines

init(autoreset=True)

BANNER = (
    f"\n{Fore.CYAN}"
    "  __  __       _ _   _ ____             _    \n"
    " |  \\/  |_   _| | |_(_)  _ \\  ___  _ __| | __\n"
    " | |\\/| | | | | | __| | | | |/ _ \\| '__| |/ /\n"
    " | |  | | |_| | | |_| | |_| | (_) | |  |   < \n"
    " |_|  |_|\\__,_|_|\\__|_|____/ \\___/|_|  |_|\\_\\\n"
    f"{Style.RESET_ALL}\n"
    f"{Fore.YELLOW}  Multi-Engine Dorking Tool for VAPT  v2.0{Style.RESET_ALL}\n"
    f"{Fore.RED}  [!] For authorized security testing only{Style.RESET_ALL}\n"
)

def progress(engine, status, count=None):
    tag = f"[{engine.upper()}]"
    if status == "querying":
        print(f"  {Fore.CYAN}{tag:<14}{Style.RESET_ALL} trying requests...")
    elif status == "selenium":
        print(f"  {Fore.YELLOW}{tag:<14}{Style.RESET_ALL} blocked — retrying with Selenium...")
    elif status == "done":
        if count:
            print(f"  {Fore.GREEN}{tag:<14}{Style.RESET_ALL} {count} result(s) found")
        else:
            print(f"  {Fore.RED}{tag:<14}{Style.RESET_ALL} no results")

def main():
    print(BANNER)

    parser = argparse.ArgumentParser(
        description="MultiDork - Automated multi-engine dorking tool",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-q", "--query", required=True,
                        help='Dork query e.g. "site:example.com filetype:pdf"')
    parser.add_argument("-e", "--engines", default="all",
                        help=f"Comma-separated engines or 'all'. Available: {', '.join(ENGINES.keys())}")
    parser.add_argument("-n", "--max-results", type=int, default=30,
                        help="Max results per engine (default: 30)")
    parser.add_argument("--list-engines", action="store_true",
                        help="List all supported engines and exit")

    args = parser.parse_args()

    if args.list_engines:
        print(f"{Fore.CYAN}Supported engines:{Style.RESET_ALL}")
        for i, e in enumerate(ENGINES.keys(), 1):
            print(f"  {i:02d}. {e}")
        sys.exit(0)

    if args.engines.strip().lower() == "all":
        selected = list(ENGINES.keys())
    else:
        selected = [e.strip().lower() for e in args.engines.split(",")]
        invalid = [e for e in selected if e not in ENGINES]
        if invalid:
            print(f"{Fore.RED}[!] Unknown engines: {', '.join(invalid)}{Style.RESET_ALL}")
            sys.exit(1)

    print(f"  {Fore.GREEN}Query   :{Style.RESET_ALL} {args.query}")
    print(f"  {Fore.GREEN}Engines :{Style.RESET_ALL} {', '.join(selected)}")
    print(f"  {Fore.GREEN}Max/eng :{Style.RESET_ALL} {args.max_results}")
    print(f"  {Fore.CYAN}Mode    :{Style.RESET_ALL} Sequential — Selenium fallback if blocked\n")
    print(f"{Fore.CYAN}{'─'*60}{Style.RESET_ALL}\n")

    per_engine, all_urls = run_all_engines(
        query=args.query,
        selected_engines=selected,
        max_results=args.max_results,
        progress_cb=progress
    )

    # ── Final sorted unique results ───────────────────────────────────────────
    print(f"\n{Fore.CYAN}{'─'*60}{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}UNIQUE RESULTS — {len(all_urls)} URL(s) (sorted){Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'─'*60}{Style.RESET_ALL}\n")

    if all_urls:
        for i, url in enumerate(all_urls, 1):
            print(f"  {Fore.CYAN}{i:>3}.{Style.RESET_ALL}  {url}")
    else:
        print(f"  {Fore.YELLOW}No results found.{Style.RESET_ALL}")

    print(f"\n{Fore.CYAN}{'─'*60}{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}[✓] Done — {len(all_urls)} unique URLs from {len(selected)} engines{Style.RESET_ALL}\n")

if __name__ == "__main__":
    main()
