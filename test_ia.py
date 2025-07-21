import os
from dotenv import load_dotenv
import google.generativeai as genai

# Carga las claves desde .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: No se encontró la GEMINI_API_KEY.")
else:
    # Configura la IA
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Envía una pregunta de prueba
    prompt = "Eres un cronista deportivo. Escribe una frase ingeniosa sobre un mánager que siempre se queja."
    print("Preguntando a la IA...")
    response = model.generate_content(prompt)

    # Imprime la respuesta
    print("\nRespuesta de la IA:")
    print(response.text)