import os
import re
import asyncio
from telethon import TelegramClient, events, Button
from flask import Flask
import threading

# --- CONFIG ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# TU ID NUEVO - GRUPO DE PELICULAS & SERIES
CANAL_DB = -1001571126545 

client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# --- KEEP ALIVE PARA RENDER ---
app = Flask(__name__)
@app.route('/')
def home():
    return "TurboFlix Bot Live"
def run_flask():
    app.run(host='0.0.0.0', port=8080)
threading.Thread(target=run_flask).start()

# --- HANDLER PARA GUARDAR ---
@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    await event.respond(
        "🔥 **TurboFlix Bot Activo**\n\nEnvíame un video y lo guardaré en la base de datos.",
        buttons=[
            [Button.url("🎬 Ver Películas", "https://turboflix.vercel.app")]
        ]
    )

@client.on(events.NewMessage(func=lambda e: e.video or e.document))
async def save_file(event):
    try:
        msg = await event.respond("⏳ Guardando en la DB...")
        # Reenvia al grupo/canal DB
        file_msg = await client.send_message(CANAL_DB, event.message)
        file_id = file_msg.id
        
        # Link directo que usa tu web
        bot_username = (await client.get_me()).username
        link = f"https://t.me/{bot_username}?start=file_{file_id}"
        
        await msg.edit(f"✅ **Guardado**\n\nID: `{file_id}`\nLink: {link}")
        print(f"Archivo guardado ID: {file_id} en {CANAL_DB}")
    except Exception as e:
        await event.respond(f"❌ Error: {e}")
        print(f"Error guardando: {e}")

# --- HANDLER PARA ENVIAR ARCHIVO /f/ ---
@client.on(events.NewMessage(pattern=r'/start file_(\d+)'))
async def send_file(event):
    try:
        file_id = int(event.pattern_match.group(1))
        # Saca el archivo del grupo DB
        msg = await client.get_messages(CANAL_DB, ids=file_id)
        await client.send_message(event.chat_id, file=msg.media, caption="🎬 Aquí tienes tu película - TurboFlix")
    except Exception as e:
        await event.respond(f"❌ Archivo no encontrado. Error: {e}")

print("Bot iniciado...")
client.run_until_disconnected()
