import os
import logging
import requests
import pandas as pd
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, CallbackContext
import re

# Configurar el token del bot
TOKEN = "8173112467:AAFrOZQFH0mhqRkqQ0I1kjeyTMAFPLbn5B0"

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Función auxiliar para transformar un texto relativo (ej. "hace 7 horas") a un objeto datetime
def transform_relative_time(text):
    now = datetime.now()
    text = text.lower().strip()
    if "hace" in text:
        if "hora" in text or "horas" in text:
            try:
                hours = int(''.join(filter(str.isdigit, text)))
                return now - timedelta(hours=hours)
            except ValueError:
                return now
        elif "minuto" in text or "minutos" in text:
            try:
                minutes = int(''.join(filter(str.isdigit, text)))
                return now - timedelta(minutes=minutes)
            except ValueError:
                return now
        elif "día" in text or "dia" in text or "dias" in text:
            try:
                days = int(''.join(filter(str.isdigit, text)))
                return now - timedelta(days=days)
            except ValueError:
                return now
    elif "ayer" in text:
        return now - timedelta(days=1)
    return now

# Función para extraer el valor numérico del tiempo relativo para ordenar y filtrar
def get_time_value(text):
    text = text.lower().strip()
    if "hace" in text:
        if "hora" in text or "horas" in text:
            try:
                return int(''.join(filter(str.isdigit, text))) * 60
            except ValueError:
                return float('inf')
        elif "minuto" in text or "minutos" in text:
            try:
                return int(''.join(filter(str.isdigit, text)))
            except ValueError:
                return float('inf')
        elif "día" in text or "dia" in text or "dias" in text:
            try:
                return int(''.join(filter(str.isdigit, text))) * 1440
            except ValueError:
                return float('inf')
    elif "ayer" in text:
        return 1440
    return float('inf')

# Función para limpiar el nombre de la empresa
def clean_company_name(company):
    if pd.isna(company):
        return "No especificada"
    company = str(company).strip()
    parts = company.split('\n')
    cleaned_name = parts[-1].strip() if parts else company
    cleaned_name = cleaned_name.replace("_x000D_", "").strip()
    return cleaned_name if cleaned_name else "No especificada"

# Nueva función para extraer detalles adicionales de la página de la oferta
def extract_offer_details(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            logger.error(f"Error {response.status_code} al acceder a {url}")
            return "No especificado", "No especificado", "No especificado", "No especificado"

        soup = BeautifulSoup(response.content, "html.parser")
        description = soup.find("div", class_="box_detail") or soup.find("div", class_="fs18")
        description_text = description.get_text(separator=" ") if description else soup.get_text(separator=" ")

        # Tipo de Contrato
        tipo_contrato = "No especificado"
        if "indefinido" in description_text.lower():
            tipo_contrato = "Indefinido"
        elif "temporal" in description_text.lower():
            tipo_contrato = "Temporal"
        elif "práctica" in description_text.lower() or "practica" in description_text.lower():
            tipo_contrato = "Práctica"

        # Jornada
        jornada = "No especificado"
        jornada_match = re.search(r"(\d{1,2}\s*(?:hrs|horas)|part\s*time|full\s*time)", description_text.lower())
        if jornada_match:
            jornada = jornada_match.group(0).replace("horas", "hrs").capitalize()

        # Modalidad
        modalidad = "No especificado"
        if "presencial" in description_text.lower():
            modalidad = "Presencial"
        elif "remota" in description_text.lower() or "remoto" in description_text.lower():
            modalidad = "Remota"
        elif "híbrida" in description_text.lower() or "hibrida" in description_text.lower():
            modalidad = "Híbrida"

        # Sueldo
        sueldo = "No especificado"
        sueldo_match = re.search(r"(?:sueldo|base|líquido|liquido)\s*[:$]?\s*(\d{1,3}(?:\.\d{3})*(?:\s*líquido|\s*liquido)?)", description_text.lower())
        if sueldo_match:
            sueldo = sueldo_match.group(1).replace(".", "") + " CLP"
        else:
            sueldo_alt = re.search(r"(\d{1,3}(?:\.\d{3})*)\s*(?:líquidos|liquido)", description_text.lower())
            if sueldo_alt:
                sueldo = sueldo_alt.group(1).replace(".", "") + " CLP"

        return tipo_contrato, jornada, modalidad, sueldo

    except Exception as e:
        logger.error(f"Error al extraer detalles de {url}: {str(e)}")
        return "No especificado", "No especificado", "No especificado", "No especificado"

# Definir regiones de Computrabajo a buscar
REGIONS = {
    "rmetropolitana": "Región Metropolitana",
    # Opcional: descomenta o agrega más regiones según necesites
    # "valparaiso": "Valparaíso",
    # "biobio": "Biobío",
}

# Función para buscar trabajos en una región específica de Computrabajo
def scrape_jobs(region, keyword, max_pages, max_minutes, all_jobs):
    page = 1
    while page <= max_pages:
        url = f"https://cl.computrabajo.com/trabajo-de-{keyword}-en-{region}?p={page}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        logger.info(f"Buscando en {url}")
        print(f"🔍 Buscando en Computrabajo - {region} - {keyword} - Página {page}")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            logger.info(f"Respuesta recibida para {url}: {response.status_code}")
            if response.status_code != 200:
                logger.error(f"Error {response.status_code} para {keyword} en {region} - página {page}")
                return False

            soup = BeautifulSoup(response.content, "html.parser")
            resultados = soup.find_all("a", class_="js-o-link fc_base")
            logger.info(f"Resultados encontrados: {len(resultados)} en página {page}")
            print(f"✅ Resultados: {len(resultados)}")
            
            if not resultados:
                logger.info(f"No hay más resultados para {keyword} en {region} - página {page}")
                break

            for result in resultados:
                titulo = result.text.strip()
                link = "https://cl.computrabajo.com" + result["href"]
                container = result.find_parent("article")
                if container:
                    empresa_elem = container.find("p", class_="dIB fs16 fc_base mt5")
                    empresa = empresa_elem.text.strip() if empresa_elem else "No especificada"
                    fecha_elem = container.find("p", class_="fs13 fc_aux mt15")
                    fecha_text = fecha_elem.text.strip() if fecha_elem else "No especificada"
                    fecha_dt = transform_relative_time(fecha_text)
                    fecha_calculada = fecha_dt.strftime("%d-%m-%Y")
                    time_value = get_time_value(fecha_text)
                else:
                    empresa = "No especificada"
                    fecha_text = "No especificada"
                    fecha_calculada = datetime.today().strftime("%d-%m-%Y")
                    time_value = 0
                
                # Extraer detalles adicionales de la oferta
                tipo_contrato, jornada, modalidad, sueldo = extract_offer_details(link)
                
                if time_value <= max_minutes:
                    job_data = [
                        fecha_calculada, titulo, empresa, fecha_text, keyword.replace("-", " "), REGIONS[region],
                        tipo_contrato, jornada, modalidad, sueldo, "Computrabajo", link
                    ]
                    all_jobs.append(job_data)
                    logger.info(f"Empleo añadido: {titulo} - {tipo_contrato}, {jornada}, {modalidad}, {sueldo}")
                    print(f"📌 Empleo: {titulo} - {tipo_contrato}, {jornada}, {modalidad}, {sueldo}")

            page += 1

        except Exception as e:
            logger.error(f"Excepción en {keyword} - {region} - página {page}: {str(e)}")
            return False
    return True

# Función principal para buscar trabajos
async def buscar_trabajo(update: Update, context: CallbackContext) -> None:
    logger.info("Función buscar_trabajo iniciada")
    if len(context.args) == 0:
        await update.message.reply_text("Por favor, escribe palabras clave después de /trabajo. Ejemplo: /trabajo analista 7 [páginas]")
        logger.info("No se proporcionaron argumentos")
        return

    args = context.args
    max_days = 30
    max_pages = 10
    
    if len(args) >= 2 and args[-1].isdigit() and args[-2].isdigit():
        max_pages = int(args[-1])
        max_days = int(args[-2])
        keywords = args[:-2]
    elif args[-1].isdigit():
        max_days = int(args[-1])
        keywords = args[:-1]
    else:
        keywords = args

    if not keywords:
        await update.message.reply_text("Por favor, proporciona al menos una palabra clave. Ejemplo: /trabajo analista 7 5")
        logger.info("No se proporcionaron palabras clave válidas")
        return

    # Enviar mensaje inicial de espera
    await update.message.reply_text("☕ Tómate un café mientras se procesa tu solicitud...")

    keywords = [kw.lower().replace(" ", "-") for kw in keywords]
    today = datetime.today().strftime("%d%m%Y")
    file_name = f"WorkFinder_{today}.xlsx"
    all_jobs = []
    max_minutes = max_days * 1440
    
    logger.info(f"Iniciando búsqueda: {keywords}, max_days={max_days}, max_pages={max_pages}")
    print(f"🔎 Iniciando búsqueda: {keywords}")
    
    for keyword in keywords:
        for region in REGIONS.keys():
            success = scrape_jobs(region, keyword, max_pages, max_minutes, all_jobs)
            if not success:
                await update.message.reply_text(f"⚠ Error al procesar Computrabajo en {REGIONS[region]} para '{keyword}'")

    if all_jobs:
        logger.info(f"Total empleos recolectados: {len(all_jobs)}")
        print(f"📊 Total empleos recolectados: {len(all_jobs)}")
        df = pd.DataFrame(all_jobs, columns=[
            "Fecha Publicación", "Título", "Empresa", "Fecha", "Palabra Clave", "Ubicación",
            "Tipo Contrato", "Jornada", "Modalidad", "Sueldo", "Página", "Link"
        ])
        
        df["Empresa"] = df["Empresa"].apply(clean_company_name)
        df = df.drop_duplicates(subset=["Fecha Publicación", "Título", "Empresa", "Fecha", "Palabra Clave"])
        df = df.drop_duplicates(subset=["Link"])
        
        df['Time_Value'] = df['Fecha'].apply(get_time_value)
        df = df.sort_values(by='Time_Value', ascending=True)
        df = df.drop(columns=['Time_Value'])  # Corrección aquí: usar drop() en lugar de drop_columns()
        df = df[[
            "Fecha Publicación", "Título", "Empresa", "Fecha", "Palabra Clave", "Ubicación",
            "Tipo Contrato", "Jornada", "Modalidad", "Sueldo", "Página", "Link"
        ]]
        
        df.to_excel(file_name, index=False)
        logger.info(f"Archivo guardado: {file_name}")
        print(f"💾 Archivo guardado: {file_name}")

        total_jobs = len(df)
        keyword_counts = df["Palabra Clave"].value_counts()
        keyword_percentages = (keyword_counts / total_jobs * 100).round(2)
        
        message = f"📊 Total empleos {total_jobs} en los últimos {max_days} días.\n\nArchivo con los resultados\n\n"
        for keyword, percentage in keyword_percentages.items():
            message += f"{percentage}% empleos {keyword}\n"
        
        await update.message.reply_text(message)
        with open(file_name, "rb") as f:
            await update.message.reply_document(document=InputFile(f), filename=file_name)
        logger.info("Mensaje y archivo enviados")
    else:
        await update.message.reply_text(f"⚠ No se encontraron ofertas de empleo en los últimos {max_days} días en las regiones especificadas.")
        logger.info("No se encontraron empleos")

# Funciones básicas originales
async def start(update: Update, context: CallbackContext) -> None:
    logger.info("Comando /start ejecutado")
    await update.message.reply_text("¡Hola! Soy tu bot actualizado para buscar empleos en Chile. Usa /trabajo <palabras clave> [días] [páginas]")

async def help_command(update: Update, context: CallbackContext) -> None:
    logger.info("Comando /help ejecutado")
    help_text = (
        "📚 Comandos disponibles:\n\n"
        "/start - Inicia el bot y muestra un mensaje de bienvenida.\n"
        "/help - Muestra esta lista de comandos.\n"
        "/ping - Verifica si el bot está activo.\n"
        "/trabajo <palabras clave> [días] [páginas] - Busca empleos en Computrabajo. Ejemplo: /trabajo analista 7 5\n"
        "/bienvenida - Recibe un mensaje de bienvenida personalizado."
    )
    await update.message.reply_text(help_text)

async def ping(update: Update, context: CallbackContext) -> None:
    logger.info("Comando /ping ejecutado")
    await update.message.reply_text("¡Pong! 🏓 El bot está activo.")

# Nuevo comando /bienvenida
async def bienvenida(update: Update, context: CallbackContext) -> None:
    logger.info("Comando /bienvenida ejecutado")
    await update.message.reply_text("🎉 ¡Bienvenido(a) a WorkFinder! Soy tu asistente para encontrar las mejores ofertas de empleo en Chile. Usa /trabajo para empezar a buscar o /help para más información. ¡Éxito en tu búsqueda! 🚀")

# Comandos opcionales (descomenta para activarlos)
# async def acerca(update: Update, context: CallbackContext) -> None:
#     logger.info("Comando /acerca ejecutado")
#     await update.message.reply_text("ℹ Soy WorkFinder, creado para ayudarte a encontrar empleo en Chile. Versión 1.0 - Desarrollado por [tu nombre]. ¡Contáctame si necesitas ayuda!")

# async def regiones(update: Update, context: CallbackContext) -> None:
#     logger.info("Comando /regiones ejecutado")
#     regiones_lista = ", ".join(REGIONS.values())
#     await update.message.reply_text(f"🌍 Regiones disponibles para búsqueda: {regiones_lista}")

# async def estado(update: Update, context: CallbackContext) -> None:
#     logger.info("Comando /estado ejecutado")
#     await update.message.reply_text(f"✅ Bot activo desde {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}. ¡Listo para buscar empleos!")

# Iniciar el bot
def main():
    logger.info("Iniciando el bot...")
    print("🚀 Bot iniciado")
    application = Application.builder().token(TOKEN).build()

    # Comandos originales y nuevos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ping", ping))
    application.add_handler(CommandHandler("trabajo", buscar_trabajo))
    application.add_handler(CommandHandler("bienvenida", bienvenida))
    
    # Comandos opcionales (descomenta para activarlos)
    # application.add_handler(CommandHandler("acerca", acerca))
    # application.add_handler(CommandHandler("regiones", regiones))
    # application.add_handler(CommandHandler("estado", estado))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()