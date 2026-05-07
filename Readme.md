# ⚡ MultiDork — Multi-Engine Automated Dorking Tool

> **For authorized security testing and VAPT only.**

---

## 🔧 Installation

```bash
pip install -r requirements.txt
```

---

## 🖥️ CLI Usage

```bash
# Basic query across all 10 engines
python main.py -q "site:example.com filetype:pdf"

# Specific engines only
python main.py -q 'inurl:admin intitle:login' -e google,bing,duckduckgo

# Control results per engine
python main.py -q 'filetype:env "DB_PASSWORD"' -n 50

# List supported engines
python main.py --list-engines
```

### CLI Flags
| Flag | Description |
|------|-------------|
| `-q` / `--query` | Dork query (required) |
| `-e` / `--engines` | Comma-separated engines or `all` (default: all) |
| `-n` / `--max-results` | Max results per engine (default: 30) |
| `--list-engines` | List all supported engines |

---

## 🌐 Web UI Usage

```bash
python app.py
```

Then open: **http://localhost:5000**

Features:
- Select/deselect individual search engines
- 30+ preset dorks across 8 categories
- Collapsible per-engine result blocks
- One-click copy for individual URLs or all results
- Ctrl+Enter shortcut to run

---

## 🔍 Supported Search Engines (10)

| # | Engine | URL |
|---|--------|-----|
| 1 | Google | google.com |
| 2 | Bing | bing.com |
| 3 | DuckDuckGo | duckduckgo.com |
| 4 | Yahoo | search.yahoo.com |
| 5 | Brave | search.brave.com |
| 6 | Yandex | yandex.com |
| 7 | Ask | ask.com |
| 8 | AOL | search.aol.com |
| 9 | Startpage | startpage.com |
| 10 | Dogpile | dogpile.com |

---

## 💡 Dork Examples

```bash
# Exposed config files
filetype:env "DB_PASSWORD"
filetype:env "AWS_SECRET_ACCESS_KEY"

# Confidential docs
filetype:pdf "confidential" site:target.com
filetype:docx "internal use only"

# Admin panels
inurl:admin intitle:login
inurl:wp-admin intitle:WordPress

# Open directories
intitle:"index of" "parent directory"
intitle:"index of" ".git"

# Database exposure
filetype:sql "INSERT INTO"
inurl:phpmyadmin intitle:phpMyAdmin

# API keys
"api_key" filetype:env
"secret_key" filetype:py
```

---

## ⚠️ Disclaimer

This tool is intended **solely for authorized penetration testing and security research**. 
Use only on systems you own or have explicit written permission to test.
Unauthorized use is illegal and unethical.
