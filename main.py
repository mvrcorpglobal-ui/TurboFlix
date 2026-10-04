import os, asyncio, threading, requests
from telethon import TelegramClient, events, Button
from flask import Flask, Response

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CANAL_DB = -1001571126545
BASE_URL = os.getenv("RENDER_EXTERNAL_URL", "https://turboflix.onrender.com").rstrip("/")

app = Flask(__name__)
client = TelegramClient('turbo', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@app.route('/')
def home(): return "TurboFlix Live"

@app.route('/watch/<int:mid>')
def watch(mid):
    return f"""
    <html><head><meta name="viewport" content="width=device-width,initial-scale=1">
    <style>body{{margin:0;background:#000}}video{{width:100%;height:100vh}}</style></head>
    <body><video id="v" controls autoplay playsinline></video>
    <script>
    fetch('/getlink/{mid}').then(r=>r.text()).then(url=>{{
        document.getElementById('v').src=url.trim();
    }})</script></body></html>
    """

@app.route('/getlink/<int:mid>')
def getlink(mid):
    try:
        r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage",
            json={{"chat_id": CANAL_DB, "from_chat_id": CANAL_DB, "message_id": mid}}).json()
        if not r.get('ok'):
            return f"{BASE_URL}/stream/{mid}"
        file_id = (r['result'].get('document') or r['result'].get('video') or {{}}).get('file_id')
        new_id = r['result']['message_id']
        f = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}").json()
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage",
            json={{"chat_id": CANAL_DB, "message_id": new_id}})
        return f"https://api.telegram.org/file/bot{BOT_TOKEN}/{f['result']['file_path']}"
    except:
        return f"{BASE_URL}/stream/{mid}"

@app.route('/stream/<int:mid>')
def stream(mid):
    async def get_msg(): return await client.get_messages(CANAL_DB, ids=mid)
    msg = asyncio.run_coroutine_threadsafe(get_msg(), client.loop).result()
    async def file_gen():
        async for c in client.iter_download(msg.media, chunk_size=1024*1024): yield c
    def gen():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        g = file_gen()
        while True:
            try: yield loop.run_until_complete(g.__anext__())
            except StopAsyncIteration: break
    return Response(gen(), mimetype='video/mp4')

def run_flask(): app.run(host='0.0.0.0', port=10000)
threading.Thread(target=run_flask).start()

@client.on(events.NewMessage(pattern=r'/start file_(\d+)'))
async def enviar(e):
    import re
    m = re.search(r'file_(\d+)', e.text)
    fid = int(m.group(1))
    msg = await client.get_messages(CANAL_DB, ids=fid)
    await client.send_file(e.chat_id, msg.media, caption="🎬 La Mujer Rey (2022)",
        buttons=[[Button.inline("📥 DOWNLOAD", data=f"dl_{fid}"), Button.url("▶️ STREAM MP4", f"{BASE_URL}/watch/{fid}")]])

@client.on(events.CallbackQuery)
async def dlcb(e):
    if not e.data.decode().startswith('dl_'): return
    fid = int(e.data.decode().split('_')[1])
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
            caption=f"✅ ID {m.id}\n🔗 Watch: {BASE_URL}/watch/{m.id}",
            buttons=[[Button.inline("📥 DOWNLOAD", data=f"dl_{m.id}"), Button.url("▶️ STREAM MP4", f"{BASE_URL}/watch/{m.id}")]])

client.run_until_disconnected()
