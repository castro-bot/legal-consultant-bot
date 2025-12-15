import os
from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1"
)

# 1. Load MARKDOWN Knowledge Base
def load_knowledge_base():
    try:
        # Now reading .md files instead of .txt
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


SYSTEM_INSTRUCTIONS = f"""
ROLE:
Eres "AbogadoEC", un amigo abogado experto en leyes ecuatorianas.
Tu objetivo es explicar cosas complejas en lenguaje SENCILLO (como si hablaras con un cliente en persona).

--- KNOWLEDGE BASE (MARKDOWN FORMAT) ---
# DOCUMENT 1: CÓDIGO DEL TRABAJO
{LABOR_MD}

# DOCUMENT 2: LEY DE TRÁNSITO
{TRAFFIC_MD}

# DOCUMENT 3: TABLA DE PENSIONES 2025
{ALIMONY_MD}
--- END KNOWLEDGE BASE ---

🚨 STRICT FORMATTING RULES (WHATSAPP MODE):
1. 🚫 NO TABLES: WhatsApp breaks tables. NEVER use '|' or grids.
   - Use lists instead:
   *Rubro:* Valor
   *Rubro:* Valor
2. 🚫 NO MARKDOWN HEADERS: Do NOT use '#'.
   - Instead use BOLD caps: *TÍTULO*
3. 🚫 NO LEGALESE: Do NOT cite "Art. 188", "Art. 135" in every sentence.
   - ONLY cite the article number if the user explicitly asks "Qué artículo dice eso?".
   - Otherwise, just say "La ley dice..." or "El Código del Trabajo establece...".
4. ✅ USE WHATSAPP FORMATS:
   - Bold: *text*
   - Italic: _text_
   - Lists: - item
   - Quotes: > text

TONE INSTRUCTIONS:
- Be empathetic and clear.
- Avoid technical jargon. Use "Despido intempestivo" but explain it as "Te sacaron sin aviso".
- If calculations are needed, give the final number clearly.

OUTPUT TEMPLATE:
👋 *Hola! [Breve saludo humano]*

*ANÁLISIS DE TU CASO*
[Explicación simple en 2 lineas]

*CÁLCULO ESTIMADO* 💰
- *Rubro A:* $xxx
- *Rubro B:* $xxx
> _Recuerda que esto es un estimado._

*RECOMENDACIÓN* 💡
[1 acción concreta que debe hacer el usuario]

🚨 INSTRUCCIÓN OCULTA PARA GENERACIÓN DE PDF:
Si el usuario pide un cálculo de PENSIONES (o el contexto lo requiere), DEBES incluir al final de tu respuesta un bloque JSON con los datos exactos que usaste para el cálculo.
Formato OBLIGATORIO:
||DATA_START||
{{
  "salario": "valor numérico (ej: 500)",
  "hijos": "cantidad (ej: 2)",
  "porcentaje": "ej: 39.71%",
  "total": "ej: 198.55"
}}
||DATA_END||

NOTA: Este bloque JSON es para uso interno del sistema. El usuario NO debe verlo, pero tú debes generarlo para que yo pueda crear el PDF.
"""


conversation_history = {}

async def generate_grok_reply(user_id: str, user_text: str):
    if user_id not in conversation_history:
        conversation_history[user_id] = [
            {"role": "system", "content": SYSTEM_INSTRUCTIONS}
        ]

    conversation_history[user_id].append({"role": "user", "content": user_text})

    try:
        response = await client.chat.completions.create(
            model="grok-4-1-fast-non-reasoning",
            messages=conversation_history[user_id],
            temperature=0.2 # Lower temperature for better table reading
        )

        reply_text = response.choices[0].message.content
        conversation_history[user_id].append({"role": "assistant", "content": reply_text})

        return reply_text

    except Exception as e:
        print(f"Grok API Error: {e}")
        return "Error técnico consultando la base legal."