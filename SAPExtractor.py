import time
import sys
import threading
import pandas as pd
import pyperclip  # Requiere: pip install pyperclip
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys  # Importación corregida
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver import ActionChains
import logging

# Reducir logs de Selenium
logging.getLogger('selenium').setLevel(logging.WARNING)

# Variables globales
animacion_activa = True
ultimo_mensaje = ""  # Almacena el mensaje actual (sin el spinner)

def format_error(e):
    """Devuelve solo la primera línea del error."""
    return str(e).splitlines()[0]

def animar_puntos():
    """
    Muestra el efecto de "En proceso..." al final del mensaje actual,
    sobrescribiendo la misma línea sin saltos de línea adicionales.
    Si el mensaje actual comienza con "Etapa 7.3:" se sale sin seguir animando.
    """
    global ultimo_mensaje, animacion_activa
    i = 0
    while animacion_activa:
        if ultimo_mensaje.startswith("Etapa 7.3:"):
            break
        spinner = "." * i + " " * (4 - i)
        sys.stdout.write("\r" + (ultimo_mensaje + " En proceso" + spinner).ljust(100))
        sys.stdout.flush()
        time.sleep(0.5)
        i = (i + 1) % 5
    # Limpia la línea final
    sys.stdout.write("\r" + " " * 100 + "\r")
    sys.stdout.flush()

def imprimir_etapa(etapa, descripcion):
    """
    Actualiza la variable global 'ultimo_mensaje' con el mensaje de la etapa y
    sobrescribe la línea actual sin agregar salto de línea.
    """
    global ultimo_mensaje
    ultimo_mensaje = f"Etapa {etapa}: {descripcion}"
    sys.stdout.write("\r" + ultimo_mensaje.ljust(100))
    sys.stdout.flush()

def configurar_navegador():
    """Configura y devuelve una instancia del navegador Edge con reducción de logs."""
    imprimir_etapa("1.1", "Configurando navegador...")
    options = webdriver.EdgeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_argument("--log-level=3")
    # Para modo headless, descomenta la siguiente línea:
    # options.add_argument("--headless")
    driver = webdriver.Edge(options=options,
                            service=EdgeService(EdgeChromiumDriverManager().install(), log_path="NUL"))
    driver.maximize_window()
    driver.get('https://saps4p.fal.hec.ondemand.com/sap/bc/ui2/flp#Shell-home')
    imprimir_etapa("1.2", "Página principal cargada.")
    return driver

def iniciar_sesion(driver, usuario, contrasena):
    """Inicia sesión en la plataforma (SAP a través de Microsoft)."""
    imprimir_etapa("2.1", "Iniciando sesión...")
    wait = WebDriverWait(driver, 5)
    try:
        usuario_input = wait.until(EC.element_to_be_clickable((By.ID, 'i0116')))
        usuario_input.clear()
        usuario_input.send_keys(usuario)
        usuario_input.send_keys(Keys.RETURN)
        imprimir_etapa("2.2", "Usuario ingresado.")
        contrasena_input = wait.until(EC.element_to_be_clickable((By.ID, 'i0118')))
        contrasena_input.clear()
        contrasena_input.send_keys(contrasena)
        contrasena_input.send_keys(Keys.RETURN)
        imprimir_etapa("2.3", "Contraseña ingresada.")
    except Exception as e:
        imprimir_etapa("2.E", f"Error en inicio de sesión: {format_error(e)}")

def acceder_facturacion_protocolo(driver):
    """Accede a la transacción de Facturación Protocolo."""
    imprimir_etapa("3.1", "Accediendo a la transacción de Facturación Protocolo...")
    driver.get('https://saps4p.fal.hec.ondemand.com/sap/bc/ui2/flp?appState=lean#ZSD_FACT_PROTOCOLO-display?sap-ui-tech-hint=GUI')
    wait = WebDriverWait(driver, 20)
    try:
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        imprimir_etapa("3.2", "Transacción cargada. Esperando 5 segundos...")
        time.sleep(1)
    except Exception as e:
        imprimir_etapa("3.E", f"Error al cargar la transacción: {format_error(e)}")

def configurar_reporte(driver):
    """
    Configura el reporte:
      - Ingresa fechas
      - Presiona F8
      - Espera 5 segundos para que aparezcan los resultados
    """
    imprimir_etapa("4.1", "Configurando reporte de facturas...")
    wait = WebDriverWait(driver, 20)
    try:
        time.sleep(5)
        iframes = driver.find_elements(By.TAG_NAME, 'iframe')
        if iframes:
            imprimir_etapa("4.2", "Cambiando al iframe...")
            driver.switch_to.frame(iframes[0])
        imprimir_etapa("4.3", "Localizando campo 'Fecha del pedido' (desde)...")
        campo_fecha_desde = wait.until(EC.element_to_be_clickable((By.ID, 'M0:46:::3:34')))
        campo_fecha_desde.clear()
        campo_fecha_desde.send_keys("01.01.2024")
        campo_fecha_desde.send_keys(Keys.TAB)
        imprimir_etapa("4.4", "Fecha del pedido (desde) actualizada a 01.01.2024.")
        imprimir_etapa("4.5", "Localizando campo 'Fecha del pedido' (hasta)...")
        campo_fecha_hasta = wait.until(EC.element_to_be_clickable((By.ID, 'M0:46:::3:59')))
        campo_fecha_hasta.clear()
        campo_fecha_hasta.send_keys("31.12.9999")
        campo_fecha_hasta.send_keys(Keys.TAB)
        imprimir_etapa("4.6", "Fecha del pedido (hasta) actualizada a 31.12.9999.")
        time.sleep(2)
        driver.execute_script("arguments[0].setAttribute('value','31.12.9999');", campo_fecha_hasta)
        imprimir_etapa("4.7", 'Atributo HTML "value" forzado a "31.12.9999".')
        if iframes:
            driver.switch_to.default_content()
        imprimir_etapa("4.8", "Ejecutando reporte presionando F8...")
        actions = ActionChains(driver)
        actions.send_keys(Keys.F8).perform()
        imprimir_etapa("4.9", "F8 presionado. Esperando 15 segundos para resultados...")
        time.sleep(15)
    except Exception as e:
        imprimir_etapa("4.E", f"Error en configuración del reporte: {format_error(e)}")

def exportar_excel(driver):
    """
    Usa el atajo Ctrl+Shift+F9 para abrir la ventana "Grabar lista fichero..."
      - Presiona 4 veces la flecha hacia abajo y luego la tecla ENTER.
    """
    imprimir_etapa("5.1", "Exportando a Excel usando Ctrl+Shift+F9...")
    try:
        actions = ActionChains(driver)
        actions.key_down(Keys.CONTROL).key_down(Keys.SHIFT).send_keys(Keys.F9)\
               .key_up(Keys.SHIFT).key_up(Keys.CONTROL).perform()
        imprimir_etapa("5.2", "Atajo enviado. Esperando 5 segundos...")
        time.sleep(5)
        for _ in range(4):
            actions.send_keys(Keys.ARROW_DOWN).perform()
            time.sleep(0.5)
        imprimir_etapa("5.3", "Se presionó la flecha hacia abajo 4 veces.")
        actions.send_keys(Keys.ENTER).perform()
        imprimir_etapa("5.4", "Tecla ENTER presionada.")
        time.sleep(1)
    except Exception as e:
        imprimir_etapa("5.E", f"Error al exportar a Excel con atajo: {format_error(e)}")

def extraer_portapapeles():
    """
    Extrae el contenido del portapapeles,
      asumiendo que los datos están separados por nuevas líneas y el carácter "|" como delimitador.
      - Se ignora la primera fila y se conserva la segunda como encabezados (quitándole la primera columna y espacios).
      - Para las filas restantes, elimina la primera columna y quita espacios en cada campo.
    """
    imprimir_etapa("6.1", "Extrayendo datos desde el portapapeles...")
    data = pyperclip.paste()
    if not data:
        imprimir_etapa("6.E", "ADVERTENCIA: El portapapeles está vacío.")
        return []
    rows = data.splitlines()
    if len(rows) < 2:
        imprimir_etapa("6.E", "No se encontraron suficientes filas en el portapapeles.")
        return []
    header = [col.strip() for col in rows[1].split("|")[1:]]
    data_rows = [
        [col.strip() for col in row.split("|")[1:]]
        for row in rows[2:] if "|" in row and len(row.split("|")) > 1
    ]
    datos = [header] + data_rows
    imprimir_etapa("6.2", f"Se extrajeron {len(datos)} filas de datos desde el portapapeles (incluyendo encabezados).")
    return datos

def guardar_excel(datos, ruta_excel):
    """
    Guarda los datos en un archivo Excel y convierte a número las columnas 
      "Monto Neto", "Monto Iva" y "Monto Total" luego de eliminar los puntos.
    Además, convierte las columnas "Fec.Pedido" y "Fec.Emisio" a formato fecha corta (dd-mm-yyyy)
    y renombra la columna "Fec.Emisio" a "Fec.Emision".
    Antes de escribir el archivo, se conservan solo las primeras 15 columnas.
    """
    imprimir_etapa("7.1", "Guardando datos en Excel...")
    if datos:
        df = pd.DataFrame(datos[1:], columns=datos[0])
        # Elimina todas las columnas a partir de la columna 16 (solo se conservan 15 columnas)
        df = df.iloc[:, :15]
        df = df.apply(lambda col: col.str.strip() if col.dtype == object else col)
        # Renombrar la columna "Fec.Emisio" a "Fec.Emision"
        if "Fec.Emisio" in df.columns:
            df.rename(columns={"Fec.Emisio": "Fec.Emision"}, inplace=True)
            imprimir_etapa("7.2", "Columna 'Fec.Emisio' renombrada a 'Fec.Emision'.")
        # Convertir columnas de fecha a formato corto (dd-mm-yyyy)
        for col in ["Fec.Pedido", "Fec.Emision"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col].str.replace('.', '-', regex=False),
                                           format="%d-%m-%Y", errors="coerce").dt.strftime('%d-%m-%Y')
        # Convertir columnas monetarias eliminando puntos y convirtiéndolas a numérico
        for col in ["Monto Neto", "Monto Iva", "Monto Total"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace('.', '', regex=False), errors="coerce")
        df.to_excel(ruta_excel, index=False)
        # Se imprime la etapa 7.3; el spinner ya dejó de actualizar la línea
        imprimir_etapa("7.3", f"Datos guardados en Correctamente: {ruta_excel}")
    else:
        imprimir_etapa("7.E", "No se encontraron datos para guardar.")

def main():
    global animacion_activa
    usuario = "jorge.castros@falp.org"
    contrasena = "101211Jf@@"
    # Actualizado: la ruta de salida se establece en la carpeta BASE
    ruta_excel = r'C:\Users\jorge.castros\Documents\FACT_PROTOCOLO\BASE\ZSD_FACT_PROTOCOLO.xlsx'
    start_time = time.time()

    # Iniciar animación en un hilo separado
    animacion_thread = threading.Thread(target=animar_puntos, daemon=True)
    animacion_thread.start()

    driver = configurar_navegador()
    try:
        iniciar_sesion(driver, usuario, contrasena)
        acceder_facturacion_protocolo(driver)
        configurar_reporte(driver)
        time.sleep(5)
        exportar_excel(driver)
        # Se han eliminado las funciones de portapapeles y continuar, se extraen los datos directamente.
        datos = extraer_portapapeles()
        guardar_excel(datos, ruta_excel)
        time.sleep(5)
    finally:
        animacion_activa = False
        animacion_thread.join()
        duration = time.time() - start_time
        time_str = f"{duration:.2f} seg" if duration < 60 else f"{(duration/60):.2f} min"
        # Mover el cursor una línea arriba y limpiar dicha línea para borrar el mensaje de la etapa 7.3
        sys.stdout.write("\033[F")  # Mueve el cursor una línea arriba
        sys.stdout.write("\r" + " " * 100 + "\r")
        sys.stdout.flush()
        imprimir_etapa("8.1", f"Extracción de SAP Realizada Correctamente. =) Tiempo: {time_str}")
        driver.quit()

if __name__ == "__main__":
    # Ejecuta la operación principal en background
    op_thread = threading.Thread(target=main, daemon=True)
    op_thread.start()
    while op_thread.is_alive():
        time.sleep(1)