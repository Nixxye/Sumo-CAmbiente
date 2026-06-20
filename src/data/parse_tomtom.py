import os
import json
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    import sumolib
except ImportError:
    sumo_home = os.environ.get("SUMO_HOME")
    if sumo_home:
        sys.path.append(os.path.join(sumo_home, "tools"))
        import sumolib
    else:
        print("Erro: SUMO_HOME environment variable not set.")
        sys.exit(1)

def generate_weights_from_geojson(geojson_file, net_file, output_file):
    print(f"Carregando a rede do SUMO: {net_file}")
    net = sumolib.net.readNet(net_file, withGeo=True)
    
    print(f"Lendo os dados da TomTom: {geojson_file}")
    with open(geojson_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    edge_weights = {}
    features = data.get('features', [])
    
    print("Processando segmentos de via...")
    for feat in features:
        geom = feat.get('geometry')
        props = feat.get('properties', {})
        
        if not geom or geom.get('type') != 'LineString':
            continue
            
        speed_limit = props.get('speedLimit', 0)
        results = props.get('segmentTimeResults', [])
        if not results:
            continue
            
        avg_speed = results[0].get('averageSpeed', 0)
        
        if avg_speed > 0 and speed_limit > 0:
            # Peso proporcional à redução de velocidade. Se limite=50 e avg=25, weight=2.0
            weight = min(10.0, max(1.0, speed_limit / avg_speed))
        else:
            weight = 1.0
            
        coords = geom.get('coordinates', [])
        if coords:
            # Pega o ponto médio do segmento
            mid_idx = len(coords) // 2
            lon, lat = coords[mid_idx]
            
            x, y = net.convertLonLat2XY(lon, lat)
            edges = net.getNeighboringEdges(x, y, r=50) # raio de 50 metros
            
            if edges:
                closest_edge, dist = sorted(edges, key=lambda e: e[1])[0]
                edge_id = closest_edge.getID()
                
                if edge_id not in edge_weights:
                    edge_weights[edge_id] = []
                edge_weights[edge_id].append(weight)

    print(f"Criando arquivo de pesos em {output_file} ({len(edge_weights)} vias mapeadas)")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('<edgedata>\n')
        f.write('    <interval begin="0" end="3600">\n')
        for edge_id, weights in edge_weights.items():
            avg_weight = sum(weights) / len(weights)
            f.write(f'        <edge id="{edge_id}" value="{avg_weight:.2f}"/>\n')
        f.write('    </interval>\n')
        f.write('</edgedata>\n')
        
    print("Mapeamento concluído com sucesso!")
    return output_file

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    geojson = os.path.join(base_dir, "data", "tomtom", "jobs_9420849_results_Curitiba.geojson")
    net = os.path.join(base_dir, "data", "map", "curitiba.net.xml")
    out = os.path.join(base_dir, "data", "traffic", "tomtom_weights.src.xml")
    generate_weights_from_geojson(geojson, net, out)
