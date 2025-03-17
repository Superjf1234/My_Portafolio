import requests
import json

def generate_content(prompt, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error {response.status_code}: {response.text}"

def main():
    print("Bienvenido al chat con Gemini-2.0 Flash")
    api_key = "AIzaSyAmeKGuGsSu9h71ItjwCL9U9IIfzBfz-dY"  # Reemplaza con tu API key
    while True:
        prompt = input("\nTú: ")
        if prompt.lower() in ['salir', 'exit', 'quit']:
            print("Chat finalizado. ¡Hasta luego!")
            break
        result = generate_content(prompt, api_key)
        
        # Si se obtuvo un error, se imprime tal cual.
        if isinstance(result, str):
            print("\nRespuesta de Gemini:", result)
        else:
            # Extraemos el texto de la primera respuesta y removemos espacios adicionales.
            try:
                respuesta = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                print("\nIA:", respuesta)
            except Exception as e:
                print("\nError al procesar la respuesta:", e)
                print("Respuesta completa:", json.dumps(result, indent=2))

if __name__ == "__main__":
    main()