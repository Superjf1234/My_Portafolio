import os
import sys
import time
import threading
import pandas as pd
from datetime import datetime

# Flag global para detener el spinner
spinner_done = False

def spinner():
    spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    i = 0
    while not spinner_done:
        sys.stdout.write(f"\rProcesando solicitud {spinner_chars[i % len(spinner_chars)]}")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1

def generar_adherencia():
    global spinner_done

    # Iniciamos el spinner en un hilo separado
    spinner_thread = threading.Thread(target=spinner)
    spinner_thread.start()
    
    # Medimos el tiempo de ejecución
    start_time = time.time()
    
    # Ruta base donde se encuentran los archivos
    ruta_base = r"C:\Users\jorge.castros\Desktop\BASE"
    
    # Archivo de entrada "Protocolos.xlsx"
    nombre_archivo_entrada = "Protocolos.xlsx"
    ruta_entrada = os.path.join(ruta_base, nombre_archivo_entrada)
    
    # Leemos el archivo de Protocolos
    df = pd.read_excel(ruta_entrada)
    
    # Definimos las columnas deseadas
    columnas_deseadas = [
        "FECHA", "MES", "AÑO", "folio", "RUT_PACIENTE", "PRESTACION", "CANTIDAD",
        "EXENTO", "AFECTO", "IVA", "NETO", "TOTAL", "CONVENIO", "TRANSACCION",
        "TIPO_PRESTACION", "ORIGEN", "MOTIVOINGRESO"
    ]
    df_filtrado = df[columnas_deseadas].copy()
    
    # Rellenamos la columna PEDIDO SAP
    df_filtrado["PEDIDO SAP"] = df_filtrado.apply(
        lambda row: f"{row['TRANSACCION']}A" if row["ORIGEN"] == "CAJA"
                    else (f"{int(row['folio'])}A" if row["ORIGEN"] == "FOLIO" else ""),
        axis=1
    )
    
    # Leemos el archivo "Pedidos de cliente.xlsx"
    nombre_pedidos_cliente = "Pedidos de cliente.xlsx"
    ruta_pedidos = os.path.join(ruta_base, nombre_pedidos_cliente)
    df_pedidos = pd.read_excel(ruta_pedidos)
    
    # Convertimos la columna "Pedido de cliente" a un conjunto
    pedidos_set = set(df_pedidos["Pedido de cliente"].astype(str).str.strip())
    
    # Función que cruza la información
    def check_status(pedido):
        if not pedido:
            return "NO_SAP"
        pedido = str(pedido).strip()
        pedido_sin_A = pedido[:-1] if pedido.endswith("A") else pedido
        return "SAP" if pedido in pedidos_set or pedido_sin_A in pedidos_set else "NO_SAP"
    
    # Asignamos la columna STATUS_SAP
    df_filtrado["STATUS_SAP"] = df_filtrado["PEDIDO SAP"].apply(check_status)
    
    # Generamos el nombre de salida con la fecha actual
    fecha_actual = datetime.now().strftime("%d_%m_%Y")
    nombre_archivo_salida = f"Adherencia_{fecha_actual}.xlsx"
    
    # Ruta de salida
    ruta_salida = os.path.join(r"C:\Users\jorge.castros\Documents\FACT_PROTOCOLO", nombre_archivo_salida)
    
    # Exportamos el DataFrame
    df_filtrado.to_excel(ruta_salida, index=False)
    
    # Calculamos el tiempo de ejecución
    elapsed_time = time.time() - start_time
    
    # Detenemos el spinner
    spinner_done = True
    spinner_thread.join()
    
    # Limpiamos la línea y mostramos el mensaje final
    sys.stdout.write("\r" + " " * 40 + "\r")
    
    # Ajustamos el formato del tiempo: segundos si < 60, minutos si >= 60
    if elapsed_time < 60:
        tiempo_str = f"{elapsed_time:.2f} segundos"
    else:
        minutos = elapsed_time / 60
        tiempo_str = f"{minutos:.2f} minutos"
    
    sys.stdout.write(f"Archivo generado: {nombre_archivo_salida} ({tiempo_str})\n")
    sys.stdout.flush()

if __name__ == "__main__":
    generar_adherencia()