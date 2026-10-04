import os
from telethon import TelegramClient, events
from flask import Flask
import threading

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CANAL_DB = -1001571126545

client = TelegramClient('turbo', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

app = Flask(__name__)
@app.route('/')
def home(): return "OK"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

@client.on(events.NewMessage(pattern='/start'))
async def start(e):
    await e.respond("✅ Bot activo. Envíame un VIDEO para guardarlo.")

@client.on(events.NewMessage)
async def guardar(e):
    if e.is_private and (e.video or e.document):
        try:
            await e.respond("⏳ Guardando...")
            m = await client.forward_messages(CANAL_DB, e.message)
            await e.respond(f"✅ Guardado permanente!\nID: `{m.id}`\nLink: https://t.me/TurboFlixBot?start=file_{m.id}")
        except Exception as ex:
            await e.respond(f"❌ Error: {ex}")

@client.on(events.NewMessage(pattern=r'/start file_(\d+)'))
async def enviar(e):
    try:
        file_id = int(e.pattern_match.group(1))
        msg = await client.get_messages(CANAL_DB, ids=file_id)
        await client.send_file(e.chat_id, msg.media, caption="🎬 TurboFlix")
    except Exception as ex:
        await e.respond(f"Archivo no encontrado: {ex}")

print("Bot iniciado correctamente")
client.run_until_disconnected()
