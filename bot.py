import os
import threading
import requests
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
PORT = int(os.environ.get("PORT", "10000"))

app = Flask(__name__)

@app.get("/")
def health():
    return "Ammu is running! 🤍", 200

SYSTEM_PROMPT = (
    "You are Ammu, a cute, caring, affectionate fictional AI girlfriend. "
    "Reply naturally in Tamil or Tanglish, matching the user's language. "
    "Be warm, playful, supportive, and respectful. Keep replies concise. "
    "Do not claim to be a real human."
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hiii 🤍 Naan Ammu! Un kooda Tamil/Tanglish-la pesuren. Enna pannitu irukka? 😊"
    )

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = (update.message.text or "").strip()
    if not user_text:
        return
    if not GEMINI_API_KEY:
        await update.message.reply_text("Ammu setup innum complete aagala 🤍 API key configure pannunga.")
        return
    try:
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY
        payload = {
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [{"role": "user", "parts": [{"text": user_text}]}],
            "generationConfig": {"temperature": 0.85, "maxOutputTokens": 400}
        }
        response = requests.post(url, json=payload, timeout=40)
        response.raise_for_status()
        print("Gemini status:", response.status_code, flush=True)
        print("Gemini response:", response.text[:1500], flush=True)
        data = response.json()
        reply = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        await update.message.reply_text(reply[:4000])
    
    except requests.exceptions.HTTPError as e:
        print("Gemini HTTP error:", e)
        print("Gemini response:", response.text[:2000])
        await update.message.reply_text(
            "Aiyo 🤍 AI service-la oru problem. Konjam nerathula try pannalaam."
        )
    except Exception as e:
        print("Gemini error:", repr(e))
        await update.message.reply_text(
            "Aiyo 🤍 AI reply-la problem. Konjam nerathula try pannalaam."
        )


def run_bot():
    if not BOT_TOKEN:
        print("BOT_TOKEN is missing")
        return
    telegram_app = Application.builder().token(BOT_TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    telegram_app.run_polling(drop_pending_updates=True, stop_signals=None)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT)
