import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# Lee las variables de Render (no pongas tu session aquí)
API_ID = int(os.getenv("API_ID", "37765125"))
API_HASH = os.getenv("API_HASH", "e07cb9110285ade51f8ee52cda905c8e")
SESSION_STRING = os.getenv("SESSION")

if not SESSION_STRING:
    print("❌ ERROR: No pusiste la variable SESSION en Render")
    exit(1)

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(pattern=r"\.ping"))
async def ping(event):
    await event.edit("🚀 TurboFlix 24/7 ON - Activo!")

@client.on(events.NewMessage(pattern=r"\.alive"))
async def alive(event):
    await event.edit("✅ **TurboFlix Bot**\n🔥 Corriendo 24/7 en Render\n⚡️ Sin caídas")

async def main():
    print("=================================")
    print("   TurboFlix 24/7 ON")
    print("=================================")
    await client.start()
    print("✅ Cliente conectado!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
