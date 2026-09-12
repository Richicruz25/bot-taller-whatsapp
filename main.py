import os
import requests
from fastapi import FastAPI, Request, Response
from google import genai

app = FastAPI()

# Inicializar el cliente de Gemini utilizando la variable de entorno para la API Key
client = genai.Client()

# Token de verificación que configuraste en Meta para el Webhook (GET y POST)
VERIFY_TOKEN = "mi_token_secreto_123"

# Prompt del sistema para definir la personalidad o contexto del bot
PROMPT_SISTEMA = (
    "Eres un asistente virtual experto para un taller automotriz."
)


@app.get("/")
def home():
  return {"mensaje": "Bot del taller funcionando correctamente"}


# 1. Verificación del Webhook de WhatsApp (GET)
@app.get("/webhook")
async def verify_webhook(request: Request):
  hub_mode = request.query_params.get("hub.mode")
  hub_verify_token = request.query_params.get("hub.verify_token")
  hub_challenge = request.query_params.get("hub.challenge")

  if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
    return Response(content=hub_challenge, media_type="text/plain")
  return Response(content="Token de verificación inválido", status_code=403)


# 2. Recepción y respuesta de mensajes de WhatsApp (POST)
@app.post("/webhook")
async def receive_message(request: Request):
  data = await request.json()

  try:
    entry = data["entry"][0]
    changes = entry["changes"][0]
    value = changes["value"]

    if "messages" in value:
      message_body = value["messages"][0]["text"]["body"]
      sender_number = value["messages"][0]["from"]
      
      # Imprimir en los logs de Render quién está escribiendo y qué dice
      print(f"Mensaje recibido de {sender_number}: {message_body}")

      # Generar respuesta con Gemini usando gemini-3.6-flash
      response = client.models.generate_content(
          model="gemini-3.6-flash",
          contents=f"{PROMPT_SISTEMA}\n\nCliente pregunta: {message_body}",
      )

      respuesta_texto = response.text

      # Tus datos oficiales de Meta
      phone_number_id = "1343467358843046"
      whatsapp_token = "EAARmbMZC3PHwBSQE7OAxddOkSjdbhByk5w5SZAYLZAj17ZA8wCzQZBxadvlkwyknZAxeGVqmDt5zrEjjPUndwdZAtHi3pXb3lcfwb8iF1OTxZAncTxHjHJ7FTE4DqPRZB6v6DB0pVhzgvm5RpIeGBXRYVbiLlGglUvsyOKLkmt6OXbqkVzwgZA7CRd9YqVvgZB6CZAar3u9RqnNLtLDVruGIfKpaqSCH6qJEzBNeVcXkeEUYNYm1tam3AMq4h8ygesjfTddJDHuEoNndnxY5TY146O5HjGPc"

      whatsapp_url = f"https://graph.facebook.com/v20.0/{phone_number_id}/messages"
      headers = {
          "Authorization": f"Bearer {whatsapp_token}",
          "Content-Type": "application/json",
      }
      payload = {
          "messaging_product": "whatsapp",
          "to": sender_number,
          "text": {"body": respuesta_texto},
      }

      # Enviar la respuesta de vuelta a WhatsApp e imprimir el resultado en consola
      res = requests.post(whatsapp_url, json=payload, headers=headers)
      print(f"Estado de Meta al responder: {res.status_code} - Respuesta: {res.text}")

  except Exception as e:
    print(f"Error procesando el mensaje: {e}")

  return {"status": "ok"}