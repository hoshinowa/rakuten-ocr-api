# ✅ HTML抽出用の中継API（楽天商品ページ）

# 必要なライブラリ
# pip install fastapi uvicorn requests beautifulsoup4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup

app = FastAPI()

# CORS設定（GPTSからのリクエスト許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/rakuten-html")
async def rakuten_html(req: Request):
    body = await req.json()
    url = body.get("url")

    if not url:
        return {"error": "楽天URLが必要です"}

    try:
        # 楽天ページを取得（PC版）
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # meta description の取得
        description = ""
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            description = meta["content"].strip()

        # titleタグの取得
        title = soup.title.string.strip() if soup.title else ""

        # その他の説明用候補（classベース）
        additional = ""
        for cls in ["item_desc", "product-text", "detail_txt", "item-comment"]:
            tag = soup.find(class_=cls)
            if tag:
                additional = tag.get_text(strip=True)
                break

        combined = "\n".join(filter(None, [title, description, additional]))

        return {
            "source_url": url,
            "extracted_text": combined or "ページ内に説明テキストが見つかりませんでした。"
        }

    except Exception as e:
        return {"error": str(e)}
