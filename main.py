import os, asyncio, threading
from telethon import TelegramClient, events, Button
from flask import Flask, Response, request

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CANAL_DB = -1001571126545
BASE_URL = "https://turboflix.onrender.com"

app = Flask(__name__)
client = TelegramClient('turbo', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@app.route('/')
def home(): return "TurboFlix Live"
@app.route('/watch/<int:mid>')
def watch(mid):
    return f'<html><body style="margin:0;background:#000"><video controls autoplay style="width:100%;height:100vh" src="{BASE_URL}/stream/{mid}"></video></body></html>'
@app.route('/stream/<int:mid>')
def stream(mid):
    async def get_msg(): return await client.get_messages(CANAL_DB, ids=mid)
    msg = asyncio.run_coroutine_threadsafe(get_msg(), client.loop).result()
    if not msg or not msg.media: return "No",404
    async def file_gen():
        async for c in client.iter_download(msg.media, chunk_size=1024*1024): yield c
    def gen():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        g = file_gen()
        while True:
            try: yield loop.run_until_complete(g.__anext__())
            except StopAsyncIteration: break
    return Response(gen(), mimetype='video/mp4', headers={'Content-Disposition': f'inline; filename={mid}.mp4'})

def run_flask(): app.run(host='0.0.0.0', port=10000)
threading.Thread(target=run_flask).start()

@client.on(events.NewMessage(pattern=r'/start file_(\d+)'))
async def enviar(e):
    fid = int(e.pattern_match.group(1))
    msg = await client.get_messages(CANAL_DB, ids=fid)
    await client.send_file(e.chat_id, msg.media, caption=f"🎬 ID {fid}",
        buttons=[[Button.inline("📥 DOWNLOAD", data=f"dl_{fid}".encode())],
                 [Button.url("▶️ STREAM MP4", f"{BASE_URL}/watch/{fid}")]])

@client.on(events.CallbackQuery(pattern=b'dl_(\d+)'))
async def dlcb(e):
    fid = int(e.pattern_match.group(1))
    msg = await client.get_messages(CANAL_DB, ids=fid)
    await client.send_file(e.chat_id, msg.media)

@client.on(events.NewMessage)
async def guardar(e):
    if e.is_private and (e.message.video or e.message.document):
        if e.text and '/start' in e.text: return
        s = await e.respond("⏳ Guardando...")
        m = await client.forward_messages(CANAL_DB, e.message)
        await s.delete()
        await client.send_file(e.chat_id, e.message.media,
            caption=f"✅ ID {m.id}\n🔗 Stream: {BASE_URL}/watch/{m.id}\n🔗 Directo: {BASE_URL}/stream/{m.id}",
            buttons=[[Button.inline("📥 DOWNLOAD", data=f"dl_{m.id}".encode())],
                     [Button.url("▶️ STREAM MP4", f"{BASE_URL}/watch/{m.id}")]])

@client.on(events.NewMessage(pattern='/start$'))
async def start(e): await e.respond("👋 Envíame un video.")

print("Bot + Streaming TurboFlix listo")
client.run_until_disconnected()
