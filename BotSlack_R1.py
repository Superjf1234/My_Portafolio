import slack_sdk
import requests
import schedule
import time
from datetime import datetime

# Configuración de Slack
SLACK_TOKEN = "xoxb-8580561490082-8581843165539-rOTJAQMyXKsNpDpIitK1BCVx"
CHANNEL = "#chat_joke"

# Inicializar cliente de Slack
client = slack_sdk.WebClient(token=SLACK_TOKEN)

# Función para obtener un chiste
def get_joke():
    try:
        response = requests.get("https://v2.jokeapi.dev/joke/Any?lang=es")
        data = response.json()
        if data["type"] == "single":
            return data["python"]
        else:
            return f"{data['setup']}\n{data['delivery']}"
    except Exception as e:
        return f"¡Error al obtener chiste: {e}!"

# Función para enviar el chiste
def send_daily_joke():
    joke = get_joke()
    current_time = datetime.now().strftime("%H:%M:%S")
    message = f"Chiste del día ({current_time}):\n{joke}"
    
    try:
        response = client.chat_postMessage(
            channel=CHANNEL,
            text=message
        )
        print(f"Chiste enviado a {CHANNEL} a las {current_time}")
    except slack_sdk.errors.SlackApiError as e:
        print(f"Error al enviar el mensaje: {e.response['error']}")
        print(f"Detalles: {e.response}")

# Función principal
def main():
    print("Bot de chistes iniciado...")
    
    # Verificar autenticación
    try:
        client.auth_test()
        print("Autenticación exitosa con Slack!")
    except slack_sdk.errors.SlackApiError as e:
        print(f"Error de autenticación: {e.response['error']}")
        return
    
    # Enviar chiste inmediatamente
    print("Enviando chiste inicial...")
    send_daily_joke()
    
    # Programar envíos diarios a las 9:00 AM
    schedule.every().day.at("09:00").do(send_daily_joke)
    print("Programación diaria a las 9:00 AM establecida.")
    
    # Mantener el script corriendo
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
