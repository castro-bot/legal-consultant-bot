import os
import httpx
import logging

token = os.getenv("ACCESS_TOKEN")
phone_id = os.getenv("PHONE_NUMBER_ID")
version = os.getenv("VERSION")

async def send_whatsapp_message(to_number: str, text: str):

    if not token or not phone_id:
        logging.error("Missing ACCESS_TOKEN or PHONE_NUMBER_ID in .env")
        return

    url = f"https://graph.facebook.com/{version}/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text},
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=data, headers=headers)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logging.error(f"Failed to send message: {e.response.text}")


async def mark_as_read_and_typing(message_id: str):
    """
    Marks the message as read and triggers the typing indicator.
    Payload source: User provided curl syntax.
    """

    if not token or not phone_id:
        logging.error("Missing credentials in .env")
        return

    url = f"https://graph.facebook.com/{version}/{phone_id}/messages"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Exact payload from your instructions
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
        "typing_indicator": {
            "type": "text" # This triggers the "typing..." animation
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            # We log it but don't crash the app if this UX feature fails
            logging.error(f"Failed to send typing/read status: {e.response.text}")



async def send_whatsapp_pdf(to_number: str, pdf_url: str, caption: str, filename: str):

    url = f"https://graph.facebook.com/{version}/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "document",
        "document": {
            "link": pdf_url,
            "caption": caption,
            "filename": filename
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logging.error(f"Failed to send PDF: {e.response.text}")


async def send_interactive_list(to_number: str):

    url = f"https://graph.facebook.com/{version}/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": "⚖️ Directorio Legal"
            },
            "body": {
                "text": "Selecciona el área legal para tu consulta:"
            },
            "footer": {
                "text": "AbogadoEC - Asistencia Inteligente"
            },
            "action": {
                "button": "Ver Opciones",
                "sections": [
                    {
                        "title": "Áreas Comunes",
                        "rows": [
                            {
                                "id": "menu_laboral",
                                "title": "Laboral / Trabajo",
                                "description": "Despidos, Liquidaciones, Acoso"
                            },
                            {
                                "id": "menu_transito",
                                "title": "Tránsito / Multas",
                                "description": "Impugnaciones, Licencias"
                            },
                            {
                                "id": "menu_familia",
                                "title": "Familia / Pensiones",
                                "description": "Tabla 2025, Juicios"
                            }
                        ]
                    }
                ]
            }
        }
    }

    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload, headers=headers)