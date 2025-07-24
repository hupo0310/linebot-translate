from flask import Flask, request, abort
import openai
import requests
import json
import re

# 輸入你的 OpenAI API 金鑰
openai.api_key = "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"

# 輸入你的 LINE Channel Access Token
LINE_CHANNEL_ACCESS_TOKEN = "k+ubF+GmoRExH4MramaX1FNSlOWGKGzB75DNZynstJjZ/fWJGQPN1LT18eR+6WsTeSY5Q9amK8HpcBU+CrgDv8F9PSNi8IiYAZwStbog6fy2J67oTZ65hU0nbhsU6MiAUtWTKbaPlNU75b3zndCLbAdB04t89/1O/w1cDnyilFU="

app = Flask(__name__)

# 翻譯主程式：使用 GPT 將中翻日或日翻中
def translate_text(text):
    # 簡易語言判斷（包含中文就當中文）
    if re.search(r'[\u4e00-\u9fff]', text):
        prompt = f"請將以下中文翻譯成自然的日文：\n{text}"
    else:
        prompt = f"請將以下日文翻譯成自然的中文：\n{text}"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # 若你有 GPT-4 API 可改成 gpt-4
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

if __name__ == "__main__":
    app.run(port=5000)
