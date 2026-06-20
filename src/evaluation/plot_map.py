import os
import sys
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import matplotlib.colors as colors

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

def parse_edgedata(filepath):
    if not os.path.exists(filepath):
        print(f"Arquivo no encontrado: {filepath}")
        return {}
        
    tree = ET.parse(filepath)
    root = tree.getroot()
    
    edge_metrics = {}
    for interval in root.findall('interval'):
        for edge in interval.findall('edge'):
            edge_id = edge.get('id')
            waiting_time = float(edge.get('waitingTime', 0))
            edge_metrics[edge_id] = waiting_time
            
    return edge_metrics

def plot_traffic_map(net_file, edgedata_file, output_file, title):
    print(f"Gerando mapa de calor: {title}")
    net = sumolib.net.readNet(net_file)
    edge_metrics = parse_edgedata(edgedata_file)
    
    lines = []
    colors_array = []
    
    # Encontrar valor maximo para normalizar a escala de cores. Se passar de 500s já consideramos engarrafamento critico.
    max_wait = max(edge_metrics.values()) if edge_metrics else 1.0
    if max_wait == 0:
        max_wait = 1.0
        
    # Cap do maximo para a cor não ficar lavada por causa de 1 rua super congestionada
    max_wait = min(max_wait, 1000.0) 
        
    norm = colors.Normalize(vmin=0, vmax=max_wait)
    cmap = plt.cm.RdYlGn_r # Verde = bom, Vermelho = ruim (tempo de espera alto)
    
    # Desenhar todas as vias
    for edge in net.getEdges():
        shape = edge.getShape()
        if not shape:
            continue
            
        lines.append(shape)
        wait_time = edge_metrics.get(edge.getID(), 0)
        colors_array.append(cmap(norm(wait_time)))
        
    fig, ax = plt.subplots(figsize=(14, 12))
    fig.patch.set_facecolor('#1a1a2e') # Fundo escuro premium
    ax.set_facecolor('#1a1a2e')
    
    lc = LineCollection(lines, colors=colors_array, linewidths=1.5, alpha=0.9)
    ax.add_collection(lc)
    
    ax.autoscale()
    ax.set_aspect('equal')
    ax.axis('off')
    
    plt.title(title, color='white', fontsize=18, pad=20, fontweight='bold')
    
    # Adicionar barra de cores
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Tempo de Espera Acumulado (s)', color='white', fontsize=12)
    cbar.ax.yaxis.set_tick_params(color='white')
    cbar.outline.set_edgecolor('white')
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
    
    plt.tight_layout()
    plt.savefig(output_file, facecolor=fig.get_facecolor(), dpi=300)
    plt.close()
    print(f"Salvo em {output_file}")

def generate_maps():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    net_file = os.path.join(base_dir, 'data', 'map', 'curitiba.net.xml')
    sim_dir = os.path.join(base_dir, 'simulations')
    
    baseline_data = os.path.join(sim_dir, 'edgedata_baseline_tomtom_peak.xml')
    rl_data = os.path.join(sim_dir, 'edgedata_rl_tomtom_peak.xml')
    
    if not os.path.exists(baseline_data) or not os.path.exists(rl_data):
        print("Erro: Arquivos edgedata XML no encontrados. Rode a simulacao com '--edgedata-output'.")
        sys.exit(1)
        
    plot_traffic_map(
        net_file, 
        baseline_data, 
        os.path.join(sim_dir, 'map_heatmap_baseline.png'), 
        "Onda Verde Convencional (Horrio de Pico TomTom)"
    )
    
    plot_traffic_map(
        net_file, 
        rl_data, 
        os.path.join(sim_dir, 'map_heatmap_rl.png'), 
        "Inteligncia Artificial RL (Horrio de Pico TomTom)"
    )

if __name__ == "__main__":
    generate_maps()
