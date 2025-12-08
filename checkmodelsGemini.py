import google.generativeai as genai
from config import GEMINI_API_KEY # Asegúrate de que importe tu key
import requests

genai.configure(api_key=GEMINI_API_KEY)

print("🔍 Buscando modelos disponibles...")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"✅ {m.name}")

def get_dolar_ccl(self) -> float:
        """Obtiene la cotización del Dólar CCL (o Blue) para convertir pesos."""
        try:
            # DolarApi.com es gratuita y muy usada en Arg
            r = requests.get("https://dolarapi.com/v1/dolares/contadoconliqui", timeout=3)
            if r.status_code == 200:
                data = r.json()
                price = float(data['venta']) # Usamos punta vendedora
                print(f"💵 Dólar CCL detectado: ${price}")
                return price
        except Exception as e:
            print(f"⚠️ Error obteniendo Dólar CCL: {e}")
        
        return 1200.0 # Fallback de emergencia (Actualizar según economía real)
print("💲 Obteniendo cotización del Dólar CCL...")
valorpesos = 24444
print(f"💰 Valor en pesos: ${valorpesos}")
valordolares =  get_dolar_ccl(valorpesos)
print(f"💵 Valor en dólares: ${valordolares / valorpesos:.2f}"  )

