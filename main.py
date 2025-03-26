# ✅ GPTS用API（WebPilot風）を自前Render構成で再現

from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/api/read", methods=["POST"])
def web_page_reader():
    try:
        data = request.get_json()
        url = data.get("link")
        lang = data.get("l", "ja")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(res.text, "html.parser")

        title = soup.title.string if soup.title else ""
        # 本文候補の抽出
        candidates = soup.find_all(["p", "div"], text=True)
        content = "\n".join([c.get_text(strip=True) for c in candidates if len(c.get_text(strip=True)) > 30])

        return jsonify({
            "title": title,
            "content": content[:4000],  # トークン制限に配慮
            "meta": {},
            "links": [],
            "extra_search_results": [],
            "todo": [],
            "tips": [],
            "rules": []
        })
    except Exception as e:
        return jsonify({
            "code": "error",
            "message": "Failed to extract",
            "detail": str(e)
        }), 400

if __name__ == "__main__":
    app.run(debug=True)

