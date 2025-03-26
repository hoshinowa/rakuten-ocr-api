# ✅ 最小構成の楽天API × GPTS 中継サーバー試作コード（OCR機能付き）

# 必要なライブラリ
# pip install fastapi uvicorn requests pillow pytesseract beautifulsoup4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
from PIL import Image
import pytesseract
from io import BytesIO
import re

app = FastAPI()

# CORS設定（GPTSからのリクエスト許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 楽天URLをスマホ版に変換（末尾スラッシュ＆クエリ除去対応）
def convert_to_mobile_url(url: str) -> str:
    url = url.split("?")[0]
    if not url.endswith("/"):
        url += "/"
    match = re.match(r"https://item\.rakuten\.co\.jp/([^/]+)/([^/]+)/", url)
    if match:
        shop, item = match.groups()
        return f"https://m.rakuten.co.jp/{shop}/n/{item}/"
    return url

@app.post("/rakuten-ocr")
async def rakuten_ocr(req: Request):
    body = await req.json()
    url = body.get("url")

    if not url:
        return {"error": "楽天URLが必要です"}

    mobile_url = convert_to_mobile_url(url)

    try:
        # スマホ版ページを取得
        response = requests.get(mobile_url, timeout=20)
        soup = BeautifulSoup(response.text, "html.parser")

        # 商品画像を取得（ALT属性またはサイズでフィルタ）
        all_images = soup.find_all("img")
        filtered_images = []

        for img in all_images:
            alt = img.get("alt", "").strip()
            width = img.get("width")
            height = img.get("height")
            src = img.get("src")

            if not src or not src.startswith("http"):
                continue

            # altに商品説明が含まれる、または画像サイズが中〜大きめなものを優先
            if alt or (width and height and int(width) > 100 and int(height) > 100):
                filtered_images.append(src)

            if len(filtered_images) >= 10:
                break

        image_texts = []

        for img_url in filtered_images:
            try:
                img_response = requests.get(img_url, timeout=20)
                image = Image.open(BytesIO(img_response.content)).convert("RGB")
                text = pytesseract.image_to_string(image, lang="jpn")
                if text.strip():
                    image_texts.append(text.strip())
            except:
                continue

        combined_text = "\n".join(image_texts)

        return {
            "mobile_url": mobile_url,
            "extracted_text": combined_text or "画像からテキストを抽出できませんでした。"
        }

    except Exception as e:
        return {"error": str(e)}
