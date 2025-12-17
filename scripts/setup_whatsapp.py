"""import httpx
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERSION = os.getenv("VERSION")

async def setup_conversational_components():
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/conversational_automation"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "enable_welcome_message": True,
        # Keep your Ice Breakers if you want them
        "prompts": [
            "Calculadora Laboral 💼",
            "Multas de Tránsito 🚗",
            "Pensiones Alimenticias 👶",
        ],
        # NEW: Commands Configuration
        "commands": [
            {
                "command_name": "reset",
                "command_description": "Borrar memoria y empezar nuevo chat 🔄"
            },
            {
                "command_name": "ayuda",
                "command_description": "Ver lista de temas legales 📜"
            }
        ]
    }

    print("⏳ Configuring WhatsApp Commands...")
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print("✅ Success! Commands registered.")
            print(response.json())
        else:
            print(f"❌ Error: {response.text}")

if __name__ == "__main__":
    asyncio.run(setup_conversational_components())"""