from flask import Flask, request, abort
import openai
import requests
import json
import re
import os  # 新增：讀取環境變數

# 從環境變數讀取 OpenAI 金鑰
openai.api_key = os.getenv("OPENAI_API_KEY")

# 從環境變數讀取 LINE 金鑰
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

app = Flask(__name__)

# 翻譯主程式：使用 GPT 將中翻日或日翻中
def translate_text(text):
    if re.search(r'[\u4e00-\u9fff]', text):
        prompt = f"請將以下中文翻譯成自然的日文：\n{text}"
    else:
        prompt = f"請將以下日文翻譯成自然的中文：\n{text}"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # 如果你使用 GPT-3.5 改為 gpt-3.5-turbo
            messages=[
                {"role": "system", "content": "你是一個雙語翻譯助手。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print("❌ GPT 回傳錯誤：", e)
        return "翻譯失敗，請稍後再試～"

# 回覆訊息到 LINE 群組
def reply_to_line(reply_token, message):
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    body = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": message}]
    }

    res = requests.post("https://api.line.me/v2/bot/message/reply",
                        headers=headers, data=json.dumps(body))
    print("✅ 已回覆 LINE，狀態：", res.status_code)

@app.route("/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        body = request.get_json()
        print("✅ 收到 LINE 訊息：", body)

        events = body.get("events", [])
        for event in events:
            if event["type"] == "message" and event["message"]["type"] == "text":
                text = event["message"]["text"]
                reply_token = event["replyToken"]
                translation = translate_text(text)
                reply_to_line(reply_token, translation)

        return "OK", 200
    else:
        abort(400)

# ✅ 修正這一段：讓 Render 能偵測你的服務
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
