import os, threading, asyncio
from flask import Flask, Response
from telethon import TelegramClient
from telethon.sessions import StringSession

app = Flask(__name__)

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION = os.getenv("SESSION")

client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

@app.route('/')
def home():
    return "ON"

@app.route('/stream/<int:chat_id>/<int:msg_id>')
def stream(chat_id, msg_id):
    async def get_file():
        msg = await client.get_messages(chat_id, ids=msg_id)
        return msg.file

    # Esta ruta te da el link directo .mp4
    return f"Usa este formato para tu reproductor: /watch/{chat_id}/{msg_id}.mp4"

async def start_bot():
    await client.start()
    print("Bot ON")
    await client.run_until_disconnected()

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(start_bot())
