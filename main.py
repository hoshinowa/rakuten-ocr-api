# ? �ŏ��\���̊y�VAPI �~ GPTS ���p�T�[�o�[����R�[�h�iOCR�@�\�t���j

# �K�v�ȃ��C�u����
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

# CORS�ݒ�iGPTS����̃��N�G�X�g���j
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# �y�VURL���X�}�z�łɕϊ�
def convert_to_mobile_url(url: str) -> str:
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
        return {"error": "�y�VURL���K�v�ł�"}

    mobile_url = convert_to_mobile_url(url)

    try:
        # �X�}�z�Ńy�[�W���擾
        response = requests.get(mobile_url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # ���i�摜���擾�iALT�����܂��̓T�C�Y�Ńt�B���^�j
        all_images = soup.find_all("img")
        filtered_images = []

        for img in all_images:
            alt = img.get("alt", "").strip()
            width = img.get("width")
            height = img.get("height")
            src = img.get("src")

            if not src or not src.startswith("http"):
                continue

            # alt�ɏ��i�������܂܂��A�܂��͉摜�T�C�Y����?�傫�߂Ȃ��̂�D��
            if alt or (width and height and int(width) > 100 and int(height) > 100):
                filtered_images.append(src)

            if len(filtered_images) >= 10:
                break

        image_texts = []

        for img_url in filtered_images:
            try:
                img_response = requests.get(img_url, timeout=10)
                image = Image.open(BytesIO(img_response.content)).convert("RGB")
                text = pytesseract.image_to_string(image, lang="jpn")
                if text.strip():
                    image_texts.append(text.strip())
            except:
                continue

        combined_text = "\n".join(image_texts)

        return {
            "mobile_url": mobile_url,
            "extracted_text": combined_text or "�摜����e�L�X�g�𒊏o�ł��܂���ł����B"
        }

    except Exception as e:
        return {"error": str(e)}
