import os
import re
import time
import unicodedata
from fastapi import APIRouter, Request, Query, Response, BackgroundTasks, Depends
from dependencies import validate_signature
from services.grok import generate_grok_reply
from utils.pdf_generator import generar_pdf_pension
from utils.whatsapp import send_whatsapp_message, mark_as_read_and_typing, send_whatsapp_pdf

NGROK_URL = os.getenv("NGROK_URL")
router = APIRouter()
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

@router.get("/webhook")
async def verify_webhook(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge")
):
    """
    Handle the initial handshake verification from Meta.
    """
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)
    return Response(status_code=403)

@router.post("/webhook", dependencies=[Depends(validate_signature)])
async def handle_message(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()

    try:
        entry = body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" in value:
            message = value["messages"][0]

            # 2. EXTRACT DATA
            message_id = message["id"] # <--- WE NEED THIS ID
            from_number = message["from"]
            msg_body = message["text"]["body"]

            # 3. PASS 'message_id' TO THE BACKGROUND TASK
            background_tasks.add_task(process_conversation, from_number, msg_body, message_id)

    except Exception as e:
        print(f"Parsing error: {e}")

    return {"status": "ok"}

def normalizar(texto: str) -> str:
    """Quita tildes y pasa a minúsculas para comparaciones robustas"""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    ).lower()

# 4. UPDATE THE BACKGROUND TASK SIGNATURE
import json
import re # Importar Regex
# ... otros imports ...

# Función auxiliar para extraer el JSON oculto
def extraer_datos_pdf(texto_ai):
    patron = r"\|\|DATA_START\|\|(.*)\|\|DATA_END\|\|"
    match = re.search(patron, texto_ai, re.DOTALL)

    if match:
        json_str = match.group(1).strip()
        try:
            datos = json.loads(json_str)
            # Limpiamos el mensaje para que el usuario no vea el código JSON
            texto_limpio = texto_ai.replace(match.group(0), "").strip()
            return datos, texto_limpio
        except:
            return None, texto_ai
    return None, texto_ai

# ... (dentro de process_conversation) ...

async def process_conversation(user_id: str, user_text: str, message_id: str):
    await mark_as_read_and_typing(message_id)

    # 1. Grok genera respuesta (con el JSON oculto)
    ai_raw_response = await generate_grok_reply(user_id, user_text)

    # 2. Extraemos datos y limpiamos el texto
    datos_pdf, mensaje_final = extraer_datos_pdf(ai_raw_response)

    # 3. Enviamos el texto limpio al usuario
    await send_whatsapp_message(user_id, mensaje_final)

    # 4. Lógica de PDF Dinámico
    # Si Grok generó datos (datos_pdf no es None), creamos el PDF automáticamente
    if datos_pdf:
        print(f"🖨️ Generando PDF con datos dinámicos: {datos_pdf}")

        filename = f"Calculo_{user_id}_{int(time.time())}.pdf"

        generar_pdf_pension(
            nombre_archivo=filename,
            salario=f"${datos_pdf.get('salario', '0')}",
            hijos=datos_pdf.get('hijos', '0'),
            porcentaje=datos_pdf.get('porcentaje', '0%'),
            total_estimado=f"${datos_pdf.get('total', '0.00')}"
        )

        if NGROK_URL:
            pdf_link = f"{NGROK_URL}/static/{filename}"
            await send_whatsapp_pdf(
                to_number=user_id,
                pdf_url=pdf_link,
                caption="📄 Aquí tienes el reporte oficial con TUS datos.",
                filename="Reporte_Personalizado.pdf"
            )