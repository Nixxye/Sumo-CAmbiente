import os
import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys

def parse_tripinfo(filepath, scenario_name):
    if not os.path.exists(filepath):
        print(f"Arquivo não encontrado: {filepath}")
        return pd.DataFrame()
        
    tree = ET.parse(filepath)
    root = tree.getroot()
    
    data = []
    for trip in root.findall('tripinfo'):
        data.append({
            'Scenario': scenario_name,
            'Duration (s)': float(trip.get('duration', 0)),
            'Waiting Time (s)': float(trip.get('waitingTime', 0)),
            'Time Loss (s)': float(trip.get('timeLoss', 0)),
            'Route Length (m)': float(trip.get('routeLength', 0)),
            'Waiting Count': int(trip.get('waitingCount', 0))
        })
        
    return pd.DataFrame(data)

def generate_report_and_plots():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    sim_dir = os.path.join(base_dir, 'simulations')
    
    # Arquivos baseados no tráfego da TomTom
    file_baseline = os.path.join(sim_dir, 'tripinfo_baseline_tomtom_peak.xml')
    file_rl = os.path.join(sim_dir, 'tripinfo_rl_tomtom_peak.xml')
    
    df_base = parse_tripinfo(file_baseline, 'Baseline (Onda Verde)')
    df_rl = parse_tripinfo(file_rl, 'IA (Reinforcement Learning)')
    
    if df_base.empty or df_rl.empty:
        print("Erro: Os relatórios XML ainda não foram gerados. Rode as simulações primeiro.")
        sys.exit(1)
        
    df_all = pd.concat([df_base, df_rl], ignore_index=True)
    
    # --- ANÁLISE DETALHADA NO TERMINAL ---
    print("\n" + "="*50)
    print("🚦 RELATÓRIO DE TRÁFEGO: TOMTOM PEAK HOUR")
    print("="*50)
    
    summary = df_all.groupby('Scenario').agg({
        'Duration (s)': ['count', 'mean'],
        'Waiting Time (s)': 'mean',
        'Time Loss (s)': 'mean',
        'Waiting Count': 'mean'
    }).round(2)
    
    summary.columns = ['Total Viagens', 'Duração Média', 'Tempo Parado Médio', 'Tempo Perdido Médio', 'Paradas por Viagem']
    print(summary.to_string())
    print("="*50 + "\n")
    
    # --- GERAÇÃO DOS GRÁFICOS ---
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Comparativo de Performance: Baseline vs IA (Tráfego TomTom)', fontsize=16, fontweight='bold')
    
    # 1. Tempo Parado
    sns.barplot(data=df_all, x='Scenario', y='Waiting Time (s)', ax=axes[0,0], palette="viridis", errorbar='sd')
    axes[0,0].set_title('Tempo Parado Médio por Carro')
    axes[0,0].set_ylabel('Segundos')
    
    # 2. Tempo Perdido (Time Loss)
    sns.barplot(data=df_all, x='Scenario', y='Time Loss (s)', ax=axes[0,1], palette="magma", errorbar='sd')
    axes[0,1].set_title('Tempo Total Perdido (Lentidão + Paradas)')
    axes[0,1].set_ylabel('Segundos')
    
    # 3. Duração Total da Viagem
    sns.barplot(data=df_all, x='Scenario', y='Duration (s)', ax=axes[1,0], palette="coolwarm", errorbar='sd')
    axes[1,0].set_title('Duração Média da Viagem')
    axes[1,0].set_ylabel('Segundos')
    
    # 4. Número de vezes que o carro teve que parar
    sns.barplot(data=df_all, x='Scenario', y='Waiting Count', ax=axes[1,1], palette="crest", errorbar='sd')
    axes[1,1].set_title('Média de Paradas (Freia e Arranca)')
    axes[1,1].set_ylabel('Quantidade de Paradas')
    
    plt.tight_layout()
    plot_path = os.path.join(sim_dir, 'results_comparison.png')
    plt.savefig(plot_path, dpi=300)
    print(f"Gráfico de barras gerado e salvo em: {plot_path}")

if __name__ == "__main__":
    generate_report_and_plots()
