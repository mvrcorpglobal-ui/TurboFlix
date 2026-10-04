import os
from telethon import TelegramClient, events
from flask import Flask
import threading

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CANAL_DB = -1001571126545

app = Flask(__name__)
@app.route('/')
def home():
    return "TurboFlix Bot Live"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run_flask).start()
client = TelegramClient('turbo', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# --- CUANDO TÚ ENVÍAS VIDEO AL BOT ---
@client.on(events.NewMessage)
async def guardar(e):
    # Solo tú en privado y que sea video/documento
    if e.is_private and (e.message.video or e.message.document):
        if e.message.text and e.message.text.startswith('/start'): return
        
        status = await e.respond("⏳ Guardando y generando link...")
        # 1. Guardar en el canal
        m = await client.forward_messages(CANAL_DB, e.message)
        link = f"https://t.me/TurboFlixBot?start=file_{m.id}"
        
        await status.delete()
        # 2. Devolver contenido + link
        await client.send_file(e.chat_id, e.message.media, caption=f"✅ **Guardado permanente**\n\n🆔 ID: `{m.id}`\n🔗 **Link de reproducción:**\n{link}\n\nManda ese link a tus usuarios.")
        
# --- CUANDO UN USUARIO DA CLIC AL LINK ---
@client.on(events.NewMessage(pattern=r'/start file_(\d+)'))
async def enviar(e):
    file_id = int(e.pattern_match.group(1))
    msg = await client.get_messages(CANAL_DB, ids=file_id)
    if msg and msg.media:
        await client.send_file(e.chat_id, msg.media, caption="🎬 Aquí tienes tu contenido - TurboFlix")
    else:
        await e.respond("❌ Archivo no encontrado")

@client.on(events.NewMessage(pattern='/start'))
async def start(e):
    if 'file_' not in e.text:
        await e.respond("👋 Bienvenido a TurboFlix. Envía un link de reproducción para ver el contenido.")

print("Bot iniciado - TurboFlix listo")
client.run_until_disconnected()
