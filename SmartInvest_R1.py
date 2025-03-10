import requests
import pandas as pd
from datetime import datetime
import time
import tkinter as tk
from tkinter import ttk

# Configuración inicial
output_file = "SmartInvest_Historical.xlsx"  # Nuevo nombre del archivo
ALPHA_VANTAGE_API_KEY = "R6OWK1GTYJY1JDH6"  # Tu clave API

# Función para obtener precios de criptomonedas (CoinGecko)
def get_crypto_prices():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"
    response = requests.get(url)
    data = response.json()
    return {
        "BTC": data["bitcoin"]["usd"],
        "ETH": data["ethereum"]["usd"]
    }

# Función para obtener precios Forex (Alpha Vantage)
def get_forex_prices(api_key):
    symbols = ["EURUSD", "GBPUSD", "USDJPY"]
    forex_data = {}
    
    for symbol in symbols:
        url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={symbol[:3]}&to_currency={symbol[3:]}&apikey={api_key}"
        response = requests.get(url)
        data = response.json()
        if "Realtime Currency Exchange Rate" in data:
            forex_data[f"{symbol[:3]}/{symbol[3:]}"] = float(data["Realtime Currency Exchange Rate"]["5. Exchange Rate"])
        else:
            print(f"Error al obtener {symbol}: {data.get('Note', 'Datos no disponibles')}")
        time.sleep(12)  # Pausa para respetar límite de API
    
    return forex_data

# Guardar datos en Excel
def save_to_excel(crypto_data, forex_data):
    # Fecha y hora actual
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Combinar datos
    all_data = {
        "Fecha": timestamp,
        "BTC": crypto_data["BTC"],
        "ETH": crypto_data["ETH"],
        "EUR/USD": forex_data.get("EUR/USD", None),
        "GBP/USD": forex_data.get("GBP/USD", None),
        "USD/JPY": forex_data.get("USD/JPY", None)
    }
    
    # Crear DataFrame
    df = pd.DataFrame([all_data], columns=["Fecha", "BTC", "ETH", "EUR/USD", "GBP/USD", "USD/JPY"])
    
    # Cargar archivo existente o crear uno nuevo
    try:
        existing_df = pd.read_excel(output_file)
        df = pd.concat([existing_df, df]).reset_index(drop=True)
    except FileNotFoundError:
        pass
    
    # Guardar en Excel
    df.to_excel(output_file, index=False, engine='xlsxwriter')
    print(f"Datos guardados en {output_file}")
    return df

# Interfaz gráfica
class SmartInvestGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SmartInvest - Precios de Monedas")
        
        # Crear Treeview para mostrar datos
        self.tree = ttk.Treeview(root, columns=("Fecha", "BTC", "ETH", "EUR/USD", "GBP/USD", "USD/JPY"), show="headings")
        self.tree.heading("Fecha", text="Fecha")
        self.tree.heading("BTC", text="BTC")
        self.tree.heading("ETH", text="ETH")
        self.tree.heading("EUR/USD", text="EUR/USD")
        self.tree.heading("GBP/USD", text="GBP/USD")
        self.tree.heading("USD/JPY", text="USD/JPY")
        self.tree.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Botón para actualizar datos
        self.update_button = tk.Button(root, text="Actualizar Datos", command=self.update_data)
        self.update_button.pack(pady=10)
        
        # Cargar datos iniciales
        self.update_data()

    def update_data(self):
        # Obtener datos
        crypto_prices = get_crypto_prices()
        forex_prices = get_forex_prices(ALPHA_VANTAGE_API_KEY)
        df = save_to_excel(crypto_prices, forex_prices)
        
        # Limpiar Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Insertar datos en Treeview
        for _, row in df.iterrows():
            self.tree.insert("", "end", values=(
                row["Fecha"], row["BTC"], row["ETH"], 
                row["EUR/USD"], row["GBP/USD"], row["USD/JPY"]
            ))

# Ejecución principal
if __name__ == "__main__":
    root = tk.Tk()
    app = SmartInvestGUI(root)
    root.mainloop()