import os
import zipfile
import smtplib
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time
import schedule

# 1. CONFIGURACIÓN DE RUTAS
print("1. Configurando las Rutas...")
FOLDERS_TO_BACKUP = [
    "C:/Users/jorge.castros/Documents/Estudios",
    "C:/Users/jorge.castros/Documents/FACT_PROTOCOLO/BASE"
]
FILES_TO_BACKUP = [
    "C:/Users/jorge.castros/Documents/Reporte Mensual/BBDD_BUDGET_FOLIO.xlsx",
    "C:/Users/jorge.castros/Documents/Reporte Mensual/BBDD_BUDGET_IMG.xlsx",
    "C:/Users/jorge.castros/Documents/Reporte Mensual/BBDD_BUDGET_LAB.xlsx"
]
BACKUP_LOCATION = "C:/Users/jorge.castros/Documents/Backup"

# Configuración oficial correo Mailtrap (para pruebas)
EMAIL_SENDER = "hello@demomailtrap.co"
EMAIL_RECEIVER = "jorgefcs.1988@gmail.com"
SMTP_SERVER = "live.smtp.mailtrap.io"
SMTP_PORT = 587
SMTP_USER = "api"
SMTP_PASSWORD = "eed5822f4c7797f580b347fc39678c86"

# 2. GENERAR NOMBRE DEL BACKUP
def create_backup_filename():
    print("2. Iniciando generación del nombre del backup...")
    date_str = datetime.datetime.now().strftime("%d.%m.%Y")
    return f"Backup_{date_str}.zip"

# 3. CREAR BACKUP
def create_backup():
    backup_filename = create_backup_filename()
    print("3. Iniciando creación del backup...")
    backup_path = os.path.join(BACKUP_LOCATION, backup_filename)

    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Respaldar carpetas
        for folder in FOLDERS_TO_BACKUP:
            for root, _, files in os.walk(folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(folder))
                    zipf.write(file_path, arcname)
        # Respaldar archivos específicos
        for file in FILES_TO_BACKUP:
            if os.path.isfile(file):
                zipf.write(file, os.path.basename(file))

    print("Backup creado exitosamente.")
    return backup_path

# 3. ENVIAR CORREO DE CONFIRMACIÓN
def send_email(backup_path):
    print("4. Iniciando envío de correo...")
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = "Backup Diario Completado"

    body = f"El backup se ha completado exitosamente.\n\nUbicación: {backup_path}\nFecha: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        server.quit()
        print("Correo enviado exitosamente.")
    except Exception as e:
        print("Error al enviar correo:", e)

# 4. PROCESO DE BACKUP Y ENVÍO DE CORREO
def job():
    start_time = time.time()
    backup_path = create_backup()
    send_email(backup_path)
    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"Proceso completado. {elapsed_time:.2f} segundos.")

# Ejecutar inmediatamente una vez al iniciar
job()

# 6. EJECUCIÓN RECURRENTE DIARIA A LAS 3 AM (Lunes a Viernes)
schedule.every().monday.at("03:00").do(job)
schedule.every().tuesday.at("03:00").do(job)
schedule.every().wednesday.at("03:00").do(job)
schedule.every().thursday.at("03:00").do(job)
schedule.every().friday.at("03:00").do(job)

print("Scheduler activado, esperando ejecución...")
while True:
    schedule.run_pending()
    time.sleep(60)
