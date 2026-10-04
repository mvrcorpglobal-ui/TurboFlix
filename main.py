import os, threading, asyncio
from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import StringSession

app = Flask(__name__)
@app.route('/')
def home():
    return "TurboFlix 24/7 ON"

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION = os.getenv("SESSION")

client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

@client.on(events.NewMessage(outgoing=True, pattern=r"\.ping"))
print(f"CHAT ID: {event.chat_id}")
print(f"ID DEL GRUPO ES: {event.chat_id}")
async def ping(event):
    await event.edit("🚀 TurboFlix 24/7 ON - Conectado!")

@client.on(events.NewMessage(outgoing=True, pattern=r"\.mp4link"))
async def mp4link(event):
    reply = await event.get_reply_message()
    if not reply or not reply.file:
        return await event.edit("❌ Responde a un video con .mp4link")
    await event.edit(f"✅ Video: {reply.file.name}\nLink: https://turboflix.onrender.com/stream/{event.chat_id}/{reply.id}")

async def start_bot():
    await client.start()
    print("Bot ON - TurboFlix")
    await client.run_until_disconnected()

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(start_bot())
