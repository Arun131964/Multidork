import requests
from bs4 import BeautifulSoup
import time
import random
import urllib.parse
import re

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

def get_headers(referer=None):
    h = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    if referer:
        h["Referer"] = referer
    return h

def safe_get(url, params=None, timeout=15, referer=None):
    try:
        s = requests.Session()
        r = s.get(url, headers=get_headers(referer), params=params,
                  timeout=timeout, allow_redirects=True)
        return r if r.status_code == 200 else None
    except Exception:
        return None

# ── URL normalization for dedup ───────────────────────────────────────────────

def normalize_url(u):
    """Decode percent-encoding so %28 and ( are treated as the same."""
    try:
        decoded = urllib.parse.unquote(u)
        p = urllib.parse.urlparse(decoded)
        return urllib.parse.urlunparse((
            p.scheme.lower(),
            p.netloc.lower(),
            p.path.rstrip("/") or "/",
            p.params, p.query, ""
        ))
    except Exception:
        return u

# ── Filetype filter ───────────────────────────────────────────────────────────

def extract_filetype(query):
    m = re.search(r'filetype:(\w+)', query, re.IGNORECASE)
    return m.group(1).lower() if m else None

def filter_urls(urls, query):
    ext = extract_filetype(query)
    if not ext:
        return urls
    return [u for u in urls if f".{ext}" in urllib.parse.unquote(urllib.parse.urlparse(u).path).lower()]

# ── Selenium driver ───────────────────────────────────────────────────────────

def get_selenium_driver():
    import os, shutil
    BINS = ["/usr/bin/chromium", "/usr/bin/chromium-browser",
            "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable"]
    chrome = next((b for b in BINS if os.path.isfile(b)), None)
    cdpath = shutil.which("chromedriver")
    if not chrome or not cdpath:
        return None
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        opts = Options()
        opts.binary_location = chrome
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")
        opts.add_argument("--window-size=1920,1080")
        return webdriver.Chrome(service=Service(cdpath), options=opts)
    except Exception:
        return None

def selenium_search(build_url, link_selectors, exclude_domain, wait=3):
    """Open URL in headless Chrome, extract links matching selectors."""
    driver = get_selenium_driver()
    if not driver:
        return []
    urls = []
    try:
        driver.get(build_url)
        time.sleep(wait + random.uniform(0.5, 1.5))
        soup = BeautifulSoup(driver.page_source, "lxml")
        for sel in link_selectors:
            anchors = soup.select(sel)
            if anchors:
                for a in anchors:
                    href = a.get("href", "")
                    if href.startswith("http") and exclude_domain not in href:
                        urls.append(href)
                if urls:
                    break
    except Exception:
        pass
    finally:
        try:
            driver.quit()
        except Exception:
            pass
    return urls

# ── Search engines ────────────────────────────────────────────────────────────

def search_google(query, max_results=30):
    urls = []
    try:
        from googlesearch import search
        for url in search(query, num_results=max_results, sleep_interval=3):
            urls.append(url.url if hasattr(url, "url") else url)
        if urls:
            return list(dict.fromkeys(urls))[:max_results]
    except Exception:
        pass
    eq = urllib.parse.quote_plus(query)
    urls = selenium_search(
        f"https://www.google.com/search?q={eq}&num=30",
        ["div#search a[href]", "div.g h3 a"],
        "google.com", wait=3
    )
    clean = []
    for u in urls:
        if "/url?q=" in u:
            u = urllib.parse.unquote(u.split("/url?q=")[1].split("&")[0])
        if u.startswith("http") and "google.com" not in u:
            clean.append(u)
    return list(dict.fromkeys(clean))[:max_results]

def search_bing(query, max_results=30):
    urls = []
    for start in range(1, min(max_results, 30), 10):
        resp = safe_get("https://www.bing.com/search",
                        params={"q": query, "first": start, "count": 10},
                        referer="https://www.bing.com/")
        if not resp:
            break
        soup = BeautifulSoup(resp.text, "lxml")
        for sel in ["li.b_algo h2 a", "li.b_algo .b_title a"]:
            for a in soup.select(sel):
                h = a.get("href", "")
                if h.startswith("http") and "bing.com" not in h:
                    urls.append(h)
        time.sleep(random.uniform(1.5, 3.0))
    if not urls:
        eq = urllib.parse.quote_plus(query)
        urls = selenium_search(
            f"https://www.bing.com/search?q={eq}&count=30",
            ["li.b_algo h2 a", "h2 a[href]"],
            "bing.com"
        )
    return list(dict.fromkeys(urls))[:max_results]

def search_duckduckgo(query, max_results=30):
    urls = []
    for pkg in ["ddgs", "duckduckgo_search"]:
        try:
            DDGS = __import__(pkg, fromlist=["DDGS"]).DDGS
            with DDGS() as d:
                for r in d.text(query, max_results=max_results):
                    h = r.get("href") or r.get("url", "")
                    if h:
                        urls.append(h)
            if urls:
                return list(dict.fromkeys(urls))[:max_results]
        except ImportError:
            continue
        except Exception:
            break
    # HTML fallback
    resp = safe_get("https://html.duckduckgo.com/html/", params={"q": query, "ia": "web"})
    if resp:
        for a in BeautifulSoup(resp.text, "lxml").select("a.result__url,a.result__a"):
            h = a.get("href", "")
            if h.startswith("http") and "duckduckgo.com" not in h:
                urls.append(h)
    return list(dict.fromkeys(urls))[:max_results]

def search_yahoo(query, max_results=30):
    urls = []
    resp = safe_get("https://search.yahoo.com/search",
                    params={"p": query, "b": 1, "pz": 30},
                    referer="https://search.yahoo.com/")
    if resp:
        soup = BeautifulSoup(resp.text, "lxml")
        for sel in ["div.algo h3 a", "div.dd h3 a", "h3.title a"]:
            for a in soup.select(sel):
                h = a.get("href", "")
                if "yahoo.com/url" in h or "r.search.yahoo.com" in h:
                    qs = urllib.parse.parse_qs(urllib.parse.urlparse(h).query)
                    h = urllib.parse.unquote(qs.get("RU", qs.get("u", [""]))[0])
                if h.startswith("http") and "yahoo.com" not in h:
                    urls.append(h)
    if not urls:
        eq = urllib.parse.quote_plus(query)
        raw = selenium_search(
            f"https://search.yahoo.com/search?p={eq}",
            ["div.algo h3 a", "h3.title a"],
            "yahoo.com", wait=3
        )
        for h in raw:
            if "yahoo.com/url" in h:
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(h).query)
                h = urllib.parse.unquote(qs.get("RU", qs.get("u", [""]))[0])
            if h.startswith("http") and "yahoo.com" not in h:
                urls.append(h)
    return list(dict.fromkeys(urls))[:max_results]

def search_brave(query, max_results=30):
    urls = []
    resp = safe_get("https://search.brave.com/search",
                    params={"q": query, "source": "web"},
                    referer="https://search.brave.com/")
    if resp:
        soup = BeautifulSoup(resp.text, "lxml")
        for sel in ["a.result-header", "div.snippet-title a"]:
            for a in soup.select(sel):
                h = a.get("href", "")
                if h.startswith("http") and "brave.com" not in h:
                    urls.append(h)
    if not urls:
        eq = urllib.parse.quote_plus(query)
        urls = selenium_search(
            f"https://search.brave.com/search?q={eq}",
            ["a.result-header", "div.snippet a[href]", "h3 a[href]"],
            "brave.com", wait=3
        )
    return list(dict.fromkeys(urls))[:max_results]

def search_yandex(query, max_results=30):
    urls = []
    resp = safe_get("https://yandex.com/search/",
                    params={"text": query, "lr": 10393})
    if resp:
        soup = BeautifulSoup(resp.text, "lxml")
        for sel in ["a.OrganicTitle-Link", "h2.OrganicTitle a"]:
            for a in soup.select(sel):
                h = a.get("href", "")
                if h.startswith("http") and "yandex." not in h:
                    urls.append(h)
    if not urls:
        eq = urllib.parse.quote_plus(query)
        urls = selenium_search(
            f"https://yandex.com/search/?text={eq}",
            ["a.OrganicTitle-Link", "h2 a[href]"],
            "yandex.", wait=4
        )
    return list(dict.fromkeys(urls))[:max_results]

def search_ask(query, max_results=30):
    urls = []
    resp = safe_get("https://www.ask.com/web", params={"q": query},
                    referer="https://www.ask.com/")
    if resp:
        soup = BeautifulSoup(resp.text, "lxml")
        for sel in ["a.PartialSearchResults-item-title-link", "div.web-result h2 a"]:
            for a in soup.select(sel):
                h = a.get("href", "")
                if h.startswith("http") and "ask.com" not in h:
                    urls.append(h)
    if not urls:
        eq = urllib.parse.quote_plus(query)
        urls = selenium_search(
            f"https://www.ask.com/web?q={eq}",
            ["a.PartialSearchResults-item-title-link", "h3 a[href]"],
            "ask.com", wait=3
        )
    return list(dict.fromkeys(urls))[:max_results]

def search_aol(query, max_results=30):
    urls = []
    resp = safe_get("https://search.aol.com/aol/search", params={"q": query},
                    referer="https://search.aol.com/")
    if resp:
        soup = BeautifulSoup(resp.text, "lxml")
        for sel in ["h3.title a", "a.ac-algo-fnd", "div.algo h3 a"]:
            for a in soup.select(sel):
                h = a.get("href", "")
                if "aol.com/url" in h:
                    qs = urllib.parse.parse_qs(urllib.parse.urlparse(h).query)
                    h = urllib.parse.unquote(qs.get("u", [""])[0])
                if h.startswith("http") and "aol.com" not in h:
                    urls.append(h)
    if not urls:
        eq = urllib.parse.quote_plus(query)
        urls = selenium_search(
            f"https://search.aol.com/aol/search?q={eq}",
            ["h3.title a", "h3 a[href]"],
            "aol.com", wait=3
        )
    return list(dict.fromkeys(urls))[:max_results]

def search_startpage(query, max_results=30):
    urls = []
    resp = safe_get("https://www.startpage.com/sp/search",
                    params={"q": query, "cat": "web", "language": "english"})
    if resp:
        soup = BeautifulSoup(resp.text, "lxml")
        for sel in ["a.result-title", "h3.search-item__title a", "a.w-gl__result-title"]:
            for a in soup.select(sel):
                h = a.get("href", "")
                if h.startswith("http") and "startpage.com" not in h:
                    urls.append(h)
    if not urls:
        eq = urllib.parse.quote_plus(query)
        urls = selenium_search(
            f"https://www.startpage.com/search?q={eq}",
            ["a.result-title", "h3 a[href]"],
            "startpage.com", wait=4
        )
    return list(dict.fromkeys(urls))[:max_results]

def search_dogpile(query, max_results=30):
    urls = []
    resp = safe_get("https://www.dogpile.com/serp", params={"q": query})
    if resp:
        soup = BeautifulSoup(resp.text, "lxml")
        for sel in ["a.web-bing__title", "div.web-result h2 a"]:
            for a in soup.select(sel):
                h = a.get("href", "")
                if h.startswith("http") and "dogpile.com" not in h:
                    urls.append(h)
    if not urls:
        eq = urllib.parse.quote_plus(query)
        urls = selenium_search(
            f"https://www.dogpile.com/serp?q={eq}",
            ["a.web-bing__title", "h3 a[href]"],
            "dogpile.com", wait=3
        )
    return list(dict.fromkeys(urls))[:max_results]

# ── Registry ──────────────────────────────────────────────────────────────────

ENGINES = {
    "google":     search_google,
    "bing":       search_bing,
    "duckduckgo": search_duckduckgo,
    "yahoo":      search_yahoo,
    "brave":      search_brave,
    "yandex":     search_yandex,
    "ask":        search_ask,
    "aol":        search_aol,
    "startpage":  search_startpage,
    "dogpile":    search_dogpile,
}

ENGINE_SELENIUM_CONFIG = {
    "google":    ("https://www.google.com/search?q={eq}&num=30",
                  ["div#search a[href]", "div.g h3 a"], "google.com", 3),
    "bing":      ("https://www.bing.com/search?q={eq}&count=30",
                  ["li.b_algo h2 a", "h2 a[href]"], "bing.com", 2),
    "yahoo":     ("https://search.yahoo.com/search?p={eq}",
                  ["div.algo h3 a", "h3.title a"], "yahoo.com", 3),
    "brave":     ("https://search.brave.com/search?q={eq}",
                  ["a.result-header", "div.snippet a[href]", "h3 a[href]"], "brave.com", 3),
    "yandex":    ("https://yandex.com/search/?text={eq}",
                  ["a.OrganicTitle-Link", "h2 a[href]"], "yandex.", 4),
    "ask":       ("https://www.ask.com/web?q={eq}",
                  ["a.PartialSearchResults-item-title-link", "h3 a[href]"], "ask.com", 3),
    "aol":       ("https://search.aol.com/aol/search?q={eq}",
                  ["h3.title a", "h3 a[href]"], "aol.com", 3),
    "startpage": ("https://www.startpage.com/search?q={eq}",
                  ["a.result-title", "h3 a[href]"], "startpage.com", 4),
    "dogpile":   ("https://www.dogpile.com/serp?q={eq}",
                  ["a.web-bing__title", "h3 a[href]"], "dogpile.com", 3),
}

def run_all_engines(query, selected_engines=None, max_results=30, progress_cb=None):
    if selected_engines is None:
        selected_engines = list(ENGINES.keys())

    results = {e: [] for e in selected_engines}
    eq = urllib.parse.quote_plus(query)

    for engine in selected_engines:
        if progress_cb:
            progress_cb(engine, "querying")

        # Step 1: Try requests first (fast)
        try:
            urls = ENGINES[engine](query, max_results=max_results)
            urls = filter_urls(urls, query)
        except Exception:
            urls = []

        # Step 2: If blocked, retry with Selenium (one browser at a time)
        if not urls and engine in ENGINE_SELENIUM_CONFIG:
            url_tpl, selectors, excl, wait = ENGINE_SELENIUM_CONFIG[engine]
            sel_url = url_tpl.format(eq=eq)
            if progress_cb:
                progress_cb(engine, "selenium")
            raw = selenium_search(sel_url, selectors, excl, wait)

            # Unwrap redirects
            clean = []
            for u in raw:
                if engine == "google" and "/url?q=" in u:
                    u = urllib.parse.unquote(u.split("/url?q=")[1].split("&")[0])
                elif engine == "yahoo" and "yahoo.com/url" in u:
                    qs = urllib.parse.parse_qs(urllib.parse.urlparse(u).query)
                    u = urllib.parse.unquote(qs.get("RU", qs.get("u", [""]))[0])
                if u.startswith("http") and excl not in u:
                    clean.append(u)
            urls = filter_urls(list(dict.fromkeys(clean)), query)[:max_results]

        results[engine] = urls
        if progress_cb:
            progress_cb(engine, "done", len(urls))

    # Final: deduplicate with URL normalization and sort
    seen = set()
    deduped = []
    for e in selected_engines:
        for u in results[e]:
            key = normalize_url(u)
            if key not in seen:
                seen.add(key)
                deduped.append(u)

    return results, sorted(deduped)
