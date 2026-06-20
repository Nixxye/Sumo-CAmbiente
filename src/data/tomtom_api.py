import os
import json
import requests
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()
TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY")

CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "traffic", "tomtom_cache.json")
# Data histórica baseada na limitação do seu token (Agosto/2024, horário de pico da tarde)
DEPART_AT = "2024-08-15T18:00:00Z"

def fetch_traffic_data():
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    
    # Prevenção: Se o cache existir, não gasta tokens
    if os.path.exists(CACHE_FILE):
        print(f"Cache de tráfego histórico encontrado em {CACHE_FILE}.")
        print("Pulando a requisição HTTP para economizar seus tokens!")
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
            
    print("Nenhum cache encontrado. Consultando a API da TomTom (dados históricos de Ago/2024)...")
    if not TOMTOM_API_KEY or TOMTOM_API_KEY == "sua_chave_gratuita_aqui":
        print("Erro: Chave da TomTom não configurada no .env.")
        return None

    # Vamos amostrar o trânsito do quadrilátero de Curitiba usando a Routing API com data histórica
    # Rota 1: Cortando de Oeste a Leste
    # Rota 2: Cortando de Norte a Sul
    routes = [
        {"start": "-25.4310,-49.2780", "end": "-25.4380,-49.2650", "name": "Rota Oeste-Leste"},
        {"start": "-25.4250,-49.2700", "end": "-25.4400,-49.2600", "name": "Rota Norte-Sul"}
    ]
    
    traffic_data = {"routes": [], "average_congestion": 0.0}
    total_congestion = 0.0
    
    for route in routes:
        url = f"https://api.tomtom.com/routing/1/calculateRoute/{route['start']}:{route['end']}/json"
        params = {
            "key": TOMTOM_API_KEY,
            "departAt": DEPART_AT,
            "traffic": "true" # Considerar tráfego
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Extrair tempo de viagem e atraso
            summary = data['routes'][0]['summary']
            travel_time = summary.get('travelTimeInSeconds', 1)
            traffic_delay = summary.get('trafficDelayInSeconds', 0)
            free_flow_time = max(1, travel_time - traffic_delay)
            
            congestion_ratio = traffic_delay / free_flow_time
            total_congestion += congestion_ratio
            
            traffic_data["routes"].append({
                "name": route["name"],
                "travel_time_seconds": travel_time,
                "traffic_delay_seconds": traffic_delay,
                "free_flow_time": free_flow_time,
                "congestion_ratio": congestion_ratio
            })
            print(f"Sucesso ao buscar rota '{route['name']}': Atraso de {traffic_delay}s devido ao trânsito.")
            
        except Exception as e:
            print(f"Erro ao consultar TomTom para a rota '{route['name']}': {e}")
            if response is not None:
                print(f"Detalhes: {response.text}")
            
    if traffic_data["routes"]:
        traffic_data["average_congestion"] = total_congestion / len(traffic_data["routes"])
        
    # Salvar o resultado no cache para não usar a API de novo
    with open(CACHE_FILE, 'w') as f:
        json.dump(traffic_data, f, indent=4)
        
    print(f"Dados salvos no cache. Nível médio de congestionamento: {traffic_data.get('average_congestion', 0):.2f}")
    return traffic_data

if __name__ == "__main__":
    fetch_traffic_data()
