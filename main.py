import os, asyncio, threading, requests
from telethon import TelegramClient, events, Button
from flask import Flask, Response, redirect

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
    # Esta página ahora carga el mp4 directo de Telegram
    return f"""
    <html><head><meta name="viewport" content="width=device-width,initial-scale=1">
    <style>body{{margin:0;background:#000;color:#fff;font-family:sans-serif}}
    video{{width:100%;height:100vh;background:#000}} .load{{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%)}}</style>
    </head><body>
    <div class="load" id="l">⏳ Generando link directo...</div>
    <video id="v" controls autoplay playsinline></video>
    <script>
    fetch('/getlink/{mid}').then(r=>r.text()).then(url=>{{
        document.getElementById('l').style.display='none';
        let v=document.getElementById('v');
        v.src=url.trim();
        v.play().catch(()=>{{}});
    }});
    </script></body></html>
    """

@app.route('/getlink/<int:mid>')
def getlink(mid):
    try:
        # 1. Copiamos el mensaje en el mismo canal para obtener el file_id de Bot API
        r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage",
            json={"chat_id": CANAL_DB, "from_chat_id": CANAL_DB, "message_id": mid}).json()
        
        if not r.get('ok'):
            return f"{BASE_URL}/stream/{mid}"

        result = r['result']
        file_id = (result.get('document') or result.get('video') or {}).get('file_id')
        new_msg_id = result['message_id']

        # 2. Pedimos el file_path a Telegram
        f = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}").json()
        file_path = f['result']['file_path']

        # 3. Borramos la copia para no llenar el canal
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage",
            json={"chat_id": CANAL_DB, "message_id": new_msg_id})

        direct_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        return direct_url
    except Exception as e:
        return f"{BASE_URL}/stream/{mid}"

@app.route('/stream/<int:mid>')
def stream(mid):
    # Este queda solo como respaldo para archivos pequeños
    async def get_msg(): return await client.get_messages(CANAL_DB, ids=mid)
    msg = asyncio.run_coroutine_threadsafe(get_msg(), client.loop).result()
    if not msg or not msg.media: return "No encontrado",404
    async def file_gen():
        async for c in client.iter_download(msg.media, chunk_size=1024*1024): yield c
    def gen():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        g = file_gen()
        while True:
            try: yield loop.run_until_complete(g.__anext__())
            except StopAsyncIteration: break
    return Response(gen(), mimetype='video/mp4', headers={'Content-Disposition': 'inline'})

def run_flask(): app.run(host='0.0.0.0', port=10000)
threading.Thread(target=run_flask).start()

@client.on(events.NewMessage(pattern=r'/start file_(\d+)'))
async def enviar(e):
    fid = int(e.pattern_match.group(1))
    msg = await client.get_messages(CANAL_DB, ids=fid)
    await client.send_file(e.chat_id, msg.media, caption="🎬 La Mujer Rey (2022) - Latino",
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
            caption=f"✅ ID {m.id}\n🔗 Watch: {BASE_URL}/watch/{m.id}",
            buttons=[[Button.inline("📥 DOWNLOAD", data=f"dl_{m.id}".encode())],
                     [Button.url("▶️ STREAM MP4", f"{BASE_URL}/watch/{m.id}")]])

print("Bot TurboFlix listo")
client.run_until_disconnected()
