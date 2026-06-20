import os
import subprocess
import sys

def generate_tomtom_traffic(net_file="data/map/curitiba.net.xml", route_file="data/traffic/tomtom_peak.rou.xml", end_time=3600):
    """
    Gera tráfego baseado nos pesos extraídos offline do GeoJSON da TomTom.
    """
    sumo_home = os.environ.get("SUMO_HOME")
    if not sumo_home:
        print("Erro: SUMO_HOME environment variable not set.")
        sys.exit(1)
        
    random_trips_script = os.path.join(sumo_home, "tools", "randomTrips.py")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    # 1. Rodar parser para mapear o GeoJSON para as vias e criar os pesos
    parser_script = os.path.join(base_dir, "src", "data", "parse_tomtom.py")
    print("Mapeando dados da TomTom (GeoJSON) para a rede do SUMO...")
    subprocess.run([sys.executable, parser_script], check=True)
    
    # 2. Executar gerador de tráfego usando os pesos calculados
    net_path = os.path.join(base_dir, net_file)
    route_path = os.path.join(base_dir, route_file)
    weights_path = os.path.join(base_dir, "data", "traffic", "tomtom_weights.src.xml")
    
    cmd = [
        sys.executable,
        random_trips_script,
        "-n", net_path,
        "-r", route_path,
        "-e", str(end_time),
        "-p", "1.0", # Tráfego de pico denso
        "--weights-prefix", weights_path.replace(".src.xml", ""),
        "--validate"
    ]
    
    print("Gerando arquivo de rotas com pesos de congestionamento TomTom...")
    try:
        subprocess.run(cmd, check=True)
        print(f"Tráfego TomTom gerado com sucesso em {route_file}")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao rodar randomTrips.py: {e}")

if __name__ == "__main__":
    generate_tomtom_traffic()
