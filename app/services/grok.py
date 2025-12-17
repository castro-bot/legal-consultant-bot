import os
from openai import AsyncOpenAI
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

client = AsyncOpenAI(
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1"
)

template_env = Environment(loader=FileSystemLoader("templates"))

# 1. Load MARKDOWN Knowledge Base
def load_knowledge_base():
    try:
        with open("data/laboral.md", "r", encoding="utf-8") as f:
            labor_law = f.read()
        with open("data/transito.md", "r", encoding="utf-8") as f:
            traffic_law = f.read()
        with open("data/pensiones.md", "r", encoding="utf-8") as f:
            alimony_table = f.read()
        return labor_law, traffic_law, alimony_table
    except Exception as e:
        print(f"CRITICAL ERROR: Could not load laws. {e}")
        return "", "", ""

LABOR_MD, TRAFFIC_MD, ALIMONY_MD = load_knowledge_base()


def get_system_prompt():
    """
    Lee el archivo .j2 y rellena las variables (Leyes, Fecha, Lógica)
    """
    try:
        template = template_env.get_template("abogado_ec.j2")

        return template.render(
            LABOR_MD=LABOR_MD,
            TRAFFIC_MD=TRAFFIC_MD,
            ALIMONY_MD=ALIMONY_MD,
            date=datetime.now().strftime("%d/%m/%Y"),
            # Cambia a True si en el futuro usas un modelo que "piensa" (ej: grok-beta)
            is_thinking_model=True
        )
    except Exception as e:
        print(f"Error loading template: {e}")
        return "Error crítico cargando instrucciones del sistema."


conversation_history = {}

def reset_user_memory(user_id: str):
    """
    Clears the conversation history for a specific user.
    """
    if user_id in conversation_history:
        del conversation_history[user_id]
        print(f"🧹 Memory wiped for user {user_id}")
        return True
    return False

async def generate_grok_reply(user_id: str, user_text: str):
    if user_id not in conversation_history:
        system_content = get_system_prompt()
        conversation_history[user_id] = [
            {"role": "system", "content": system_content}
        ]

    conversation_history[user_id].append({"role": "user", "content": user_text})

    try:
        response = await client.chat.completions.create(
            model="grok-4-1-fast-reasoning",
            messages=conversation_history[user_id],
            temperature=0.2 # Lower temperature for better table reading
        )

        reply_text = response.choices[0].message.content
        conversation_history[user_id].append({"role": "assistant", "content": reply_text})

        return reply_text

    except Exception as e:
        print(f"Grok API Error: {e}")
        return "Error técnico consultando la base legal."