#!/usr/bin/env python3
"""
MultiDork - Flask Web UI Backend
"""

from flask import Flask, render_template, request, jsonify
from engines import ENGINES, run_all_engines
import threading

app = Flask(__name__)

# Preset dork categories
PRESET_DORKS = {
    "Exposed Config Files": [
        'filetype:env "DB_PASSWORD"',
        'filetype:env "AWS_SECRET"',
        'filetype:xml "connectionString"',
        'filetype:cfg password',
        'filetype:ini "password="',
    ],
    "Sensitive Documents": [
        'filetype:pdf "confidential"',
        'filetype:docx "internal use only"',
        'filetype:xlsx "salary"',
        'filetype:pdf "not for distribution"',
    ],
    "Admin Panels": [
        'inurl:admin intitle:login',
        'inurl:/admin/login',
        'intitle:"admin panel" inurl:admin',
        'inurl:wp-admin intitle:WordPress',
    ],
    "Login Pages": [
        'intitle:"login" inurl:login',
        'inurl:signin intitle:signin',
        'inurl:portal intitle:portal login',
    ],
    "Database Exposure": [
        'filetype:sql "INSERT INTO"',
        'filetype:sql "CREATE TABLE"',
        'inurl:phpmyadmin intitle:phpMyAdmin',
    ],
    "Open Directories": [
        'intitle:"index of" "parent directory"',
        'intitle:"index of" passwords',
        'intitle:"index of" ".git"',
    ],
    "API Keys / Tokens": [
        'inurl:api_key filetype:txt',
        '"api_key" filetype:env',
        '"secret_key" filetype:py',
    ],
    "Camera / IoT": [
        'inurl:"/view/view.shtml"',
        'intitle:"webcamXP 5"',
        'inurl:top.htm inurl:currenttime',
    ],
}


@app.route("/")
def index():
    return render_template("index.html", engines=list(ENGINES.keys()), presets=PRESET_DORKS)


@app.route("/search", methods=["POST"])
def search():
    data = request.get_json()
    query = data.get("query", "").strip()
    selected_engines = data.get("engines", list(ENGINES.keys()))
    max_results = int(data.get("max_results", 20))

    if not query:
        return jsonify({"error": "Query is required"}), 400

    try:
        per_engine, all_urls = run_all_engines(
            query=query,
            selected_engines=selected_engines,
            max_results=max_results
        )
        return jsonify({
            "query": query,
            "per_engine": per_engine,
            "all_urls": all_urls,
            "total": len(all_urls)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("\n  MultiDork Web UI running at http://127.0.0.1:5000\n")
    app.run(debug=False, host="0.0.0.0", port=5000)
