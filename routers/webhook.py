import os
import re
import json
import time
import unicodedata
from fastapi import APIRouter, Request, Query, Response, BackgroundTasks, Depends
from dependencies import validate_signature
from services.grok import generate_grok_reply, reset_user_memory
from utils.pdf_generator import generar_pdf_pension
from utils.whatsapp import send_whatsapp_message, mark_as_read_and_typing, send_whatsapp_pdf, send_interactive_list

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
        # Check if it's a valid WhatsApp message
        if (
            body.get("entry")
            and body["entry"][0].get("changes")
            and body["entry"][0]["changes"][0].get("value")
            and body["entry"][0]["changes"][0]["value"].get("messages")
        ):
            entry = body["entry"][0]
            changes = entry["changes"][0]
            value = changes["value"]
            message = value["messages"][0]

            # Extract ID and Number (Present in ALL types)
            from_number = message["from"]
            message_id = message["id"]

            # --- CRITICAL FIX: DETECT TYPE ---
            msg_type = message.get("type")
            user_text = ""

            # CASE A: Standard Text Message
            if msg_type == "text":
                user_text = message["text"]["body"]

            # CASE B: Interactive (Button/List Click)
            elif msg_type == "interactive":
                interaction = message["interactive"]
                interaction_type = interaction["type"]

                if interaction_type == "list_reply":
                    # User clicked a List Menu option
                    # We use the title/description as the text to send to Grok
                    user_text = interaction["list_reply"]["title"]
                    # Optional: You can also use interaction["list_reply"]["id"] for logic

                elif interaction_type == "button_reply":
                    # User clicked a Button
                    user_text = interaction["button_reply"]["title"]

            # CASE C: Ignore other types (Image, Audio, Status updates)
            else:
                print(f"Ignored message type: {msg_type}")
                return {"status": "ignored"}

            # --- PROCESS IF WE EXTRACTED TEXT ---
            if user_text:
                # Handle special menu commands locally
                if user_text.lower() in ["menu", "menú", "ayuda"]:
                    # Ensure send_interactive_list is imported from utils.whatsapp
                    background_tasks.add_task(send_interactive_list, from_number)
                else:
                    # Send to AI
                    background_tasks.add_task(process_conversation, from_number, user_text, message_id)

    except Exception as e:
        # Print the full error to help debug future issues
        print(f"Parsing error: {e}")

    return {"status": "ok"}

def normalizar(texto: str) -> str:
    """Quita tildes y pasa a minúsculas para comparaciones robustas"""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    ).lower()


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


async def process_conversation(user_id: str, user_text: str, message_id: str):

    # --- COMMAND HANDLER ---
    # Check if message is a command (starts with /)
    if user_text.startswith("/"):
        command = user_text.lower().strip()

        if command == "/reset":
            # Execute Reset
            reset_user_memory(user_id)

            # Confirm to User
            await send_whatsapp_message(
                user_id,
                "🔄 *Memoria reiniciada.* \nHe olvidado nuestra conversación anterior. ¿En qué puedo ayudarte ahora?"
            )
            return # STOP here, do not send to Grok

        elif command == "/ayuda":
            # Trigger your menu
            await send_interactive_list(user_id)
            return

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
            porcentaje=datos_pdf.get('porcentaje', '0%'), # Matches prompt key "porcentaje"
            total_estimado=f"${datos_pdf.get('total', '0.00')}",
            nivel=datos_pdf.get('nivel_tabla', 'N/A') # NEW FIELD
        )

        if NGROK_URL:
            pdf_link = f"{NGROK_URL}/static/{filename}"
            await send_whatsapp_pdf(
                to_number=user_id,
                pdf_url=pdf_link,
                caption="📄 Aquí tienes el reporte oficial con TUS datos.",
                filename="Reporte_Personalizado.pdf"
            )