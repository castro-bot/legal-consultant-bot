import os
import re
import json
import time
import unicodedata
from fastapi import APIRouter, Request, Query, Response, BackgroundTasks, Depends
from app.dependencies import validate_signature
from app.services.grok import generate_grok_reply, reset_user_memory
from app.utils.pdf_generator import generar_pdf_pension
from app.utils.whatsapp import send_whatsapp_message, mark_as_read_and_typing, send_whatsapp_pdf, send_interactive_list

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

            # Extract ID and Number
            from_number = message["from"]
            message_id = message["id"]

            msg_type = message.get("type")
            user_text = ""

            # Standard Text Message
            if msg_type == "text":
                user_text = message["text"]["body"]

            # Interactive (Button/List Click)
            elif msg_type == "interactive":
                interaction = message["interactive"]
                interaction_type = interaction["type"]

                if interaction_type == "list_reply":
                    # User clicked a List Menu option

                    user_text = interaction["list_reply"]["title"]


                elif interaction_type == "button_reply":
                    # User clicked a Button
                    user_text = interaction["button_reply"]["title"]

            # Ignore other types (Image, Audio, Status updates)
            else:
                print(f"Ignored message type: {msg_type}")
                return {"status": "ignored"}


            if user_text:

                if user_text.lower() in ["menu", "menú", "ayuda"]:

                    background_tasks.add_task(send_interactive_list, from_number)
                else:

                    background_tasks.add_task(process_conversation, from_number, user_text, message_id)

    except Exception as e:
        print(f"Parsing error: {e}")

    return {"status": "ok"}

def normalizar(texto: str) -> str:
    """Quita tildes y pasa a minúsculas para comparaciones robustas"""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    ).lower()


def extraer_datos_pdf(texto_ai):
    print("🔍 INTENTANDO EXTRAER DATOS DEL TEXTO...")
    patron = r"\|\|DATA_START\|\|(.*)\|\|DATA_END\|\|"
    match = re.search(patron, texto_ai, re.DOTALL)

    if match:
        print("✅ ETIQUETAS ENCONTRADAS")
        json_str = match.group(1).strip()

        if json_str.startswith("```json"):
            json_str = json_str.replace("```json", "").replace("```", "")
        elif json_str.startswith("```"):
            json_str = json_str.replace("```", "")

        json_str = json_str.strip()

        try:
            datos = json.loads(json_str)
            print(f"📦 JSON DECODIFICADO EXITOSAMENTE: {datos.keys()}")
            texto_limpio = texto_ai.replace(match.group(0), "").strip()
            return datos, texto_limpio
        except json.JSONDecodeError as e:
            print(f"❌ ERROR JSON: No se pudo leer el JSON.\nError: {e}\nContenido: {json_str}")
            return None, texto_ai
    else:
        print("⚠️ ALERTA: No se encontraron las etiquetas ||DATA_START|| en la respuesta.")
        return None, texto_ai


async def process_conversation(user_id: str, user_text: str, message_id: str):
    if user_text.startswith("/"):
        if user_text.lower().strip() == "/reset":
            reset_user_memory(user_id)
            await send_whatsapp_message(user_id, "🔄 Memoria reiniciada.")
            return
        elif user_text.lower().strip() == "/ayuda":
            await send_interactive_list(user_id)
            return

    await mark_as_read_and_typing(message_id)

    print(f"🤖 CONSULTANDO A GROK (User: {user_id})...")
    ai_raw_response = await generate_grok_reply(user_id, user_text)
    print(f"📝 RESPUESTA CRUDA DE GROK:\n{ai_raw_response}\n--------------------------------")

    datos_pdf, mensaje_final = extraer_datos_pdf(ai_raw_response)

    await send_whatsapp_message(user_id, mensaje_final)

    if datos_pdf:
        print(f"🚀 INICIANDO GENERACIÓN DE PDF LOCAL...")
        filename = f"Calculo_{user_id}_{int(time.time())}.pdf"

        try:
            ruta_pdf = generar_pdf_pension(
                nombre_archivo=filename,
                salario=f"${datos_pdf.get('salario', '0')}",
                hijos=datos_pdf.get('hijos', '0'),
                porcentaje=f"{datos_pdf.get('porcentaje', datos_pdf.get('porcentaje_base', '0%'))}",
                total_estimado=f"${datos_pdf.get('total', '0.00')}",
                nivel=datos_pdf.get('nivel_tabla', 'N/A')
            )
            print(f"✅ PDF CREADO EN: static/{filename}")
        except Exception as e:
            print(f"❌ ERROR EN FPDF: {e}")
            return

        ngrok_url = os.getenv("NGROK_URL")
        public_url = os.getenv("PUBLIC_URL")
        base_url = ngrok_url if ngrok_url else public_url

        if base_url:
            if base_url.endswith("/"): base_url = base_url[:-1]
            pdf_link = f"{base_url}/static/{filename}"
            print(f"🔗 ENVIANDO A WHATSAPP: {pdf_link}")

            await send_whatsapp_pdf(
                to_number=user_id,
                pdf_url=pdf_link,
                caption="📄 Reporte Oficial",
                filename="Reporte_Legal.pdf"
            )
        else:
            print("❌ ERROR URL: No se encontró NGROK_URL ni PUBLIC_URL.")
    else:
        print("🛑 PROCESO DETENIDO: No hay datos_pdf (Grok no envió JSON o falló la extracción).")