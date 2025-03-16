import httpcore
# Parche para que googletrans encuentre SyncHTTPTransport
if not hasattr(httpcore, "SyncHTTPTransport"):
    if hasattr(httpcore, "SyncBackend"):
        httpcore.SyncHTTPTransport = httpcore.SyncBackend
    else:
        raise Exception("googletrans requiere que httpcore tenga SyncHTTPTransport. Instala una versión anterior: pip install httpcore==0.16.1")

import logging
import gradio as gr
from gtts import gTTS
import speech_recognition as sr
from googletrans import Translator
import os

# Configuración de logging para ver el proceso interno
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

recognizer = sr.Recognizer()
translator = Translator()

target_languages = {
    "Inglés": "en",
    "Francés": "fr",
    "Alemán": "de",
    "Italiano": "it",
    "Portugués": "pt"
}

def process_audio(audio):
    try:
        logger.info("Procesando archivo de audio: %s", audio)
        with sr.AudioFile(audio) as source:
            # Se registra la duración del audio
            duration = source.DURATION if hasattr(source, "DURATION") else "desconocida"
            logger.info("Duración del audio: %s segundos", duration)
            audio_data = recognizer.record(source)
        try:
            texto_es = recognizer.recognize_google(audio_data, language="es-ES")
        except sr.UnknownValueError:
            logger.error("No se pudo reconocer el audio. Verifica que el audio contenga voz clara y sin mucho ruido.")
            return {"error": "No se pudo reconocer el audio. Asegúrate de que el audio contenga voz clara y sin ruido."}, None, None, None, None, None

        logger.info("Transcripción obtenida: %s", texto_es)
        resultados = {"Texto original (Español)": texto_es}
        audios = {}

        for lang_name, lang_code in target_languages.items():
            logger.info("Traduciendo al %s...", lang_name)
            traduccion = translator.translate(texto_es, dest=lang_code).text
            logger.info("Resultado de la traducción para %s: %s", lang_name, traduccion)
            tts = gTTS(text=traduccion, lang=lang_code, slow=False)
            audio_path = f"output_{lang_code}.mp3"
            tts.save(audio_path)
            resultados[f"Texto en {lang_name}"] = traduccion
            audios[lang_name] = audio_path

        return (
            resultados,
            audios["Inglés"],
            audios["Francés"],
            audios["Alemán"],
            audios["Italiano"],
            audios["Portugués"]
        )

    except Exception as e:
        logger.exception("Error procesando el audio")
        return {"error": str(e)}, None, None, None, None, None

with gr.Blocks(title="Convertidor de Audio Multilingüe") as demo:
    gr.Markdown("# Convertidor de Audio Multilingüe")
    gr.Markdown("Sube un archivo de audio en español y obtén traducciones y audio en varios idiomas")

    # Se elimina el argumento 'source' para compatibilidad con versiones anteriores de Gradio
    audio_input = gr.Audio(type="filepath", label="Sube tu audio en español")
    submit_btn = gr.Button("Procesar")

    text_output = gr.JSON(label="Textos traducidos")
    audio_en = gr.Audio(label="Audio en Inglés")
    audio_fr = gr.Audio(label="Audio en Francés")
    audio_de = gr.Audio(label="Audio en Alemán")
    audio_it = gr.Audio(label="Audio en Italiano")
    audio_pt = gr.Audio(label="Audio en Portugués")

    submit_btn.click(
        fn=process_audio,
        inputs=audio_input,
        outputs=[text_output, audio_en, audio_fr, audio_de, audio_it, audio_pt]
    )

demo.launch()
