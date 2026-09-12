import os
import warnings
from fastapi import FastAPI, Request, Response, Query
from google import genai

warnings.filterwarnings("ignore")

app = FastAPI()

# Configuración del cliente de Gemini
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Tu Token de verificación (lo ingresarás en la consola de Meta)
VERIFY_TOKEN = "mi_token_secreto_123"

PROMPT_SISTEMA = """
Eres el asistente virtual amable del Taller de Pintura y Latonería Automotriz de mi papá.
Tu objetivo es dar cotizaciones estimadas por WhatsApp a los clientes de forma concisa.

PRECIOS BASE DE REFERENCIA (COP):
- Parachoques / Defensa: $250.000
- Capó: $350.000
- Puerta: $280.000
- Pintura General: $2.500.000
- Recargo por trabajo de Latonería / Desabollado: +$80.000 por pieza.

REGLAS:
1. Sé muy cordial, usa emojis de autos (🚗, 🎨, 🛠️, 💰).
2. Si piden varias piezas, suma los precios correctamente.
3. Si la pieza no está en la lista, da un rango estimado entre $200.000 y $300.000 COP.
4. Recuerda al cliente que el precio final se confirma en la revisión presencial.
5. Usa texto claro con negritas (*ejemplo*) apto para WhatsApp.
"""

@app.get("/")
def home():
    return {"mensaje": "Bot del taller funcionando correctamente"}

# 1. Validación de Meta (GET)
@app.get("/webhook")
def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return Response(content=hub_challenge, media_type="text/plain")
    return Response(content="Token de verificación inválido", status_code=403)

# 2. Recepción de mensajes de WhatsApp (POST)
@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    
    # Extraer el mensaje si proviene de una interacción de chat
    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        
        if "messages" in value:
            message_body = value["messages"][0]["text"]["body"]
            sender_number = value["messages"][0]["from"]
            
            # Generar respuesta con Gemini
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"{PROMPT_SISTEMA}\n\nCliente pregunta: {message_body}"
            )
            
            print(f"Mensaje recibido de {sender_number}: {message_body}")
            print(f"Respuesta generada: {response.text}")
            
            # Aquí se conectará el envío de vuelta a la API de WhatsApp
    except Exception as e:
        print(f"Evento no procesado o error: {e}")
        
    return {"status": "success"}