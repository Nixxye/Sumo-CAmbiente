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
    
    file_baseline = os.path.join(sim_dir, 'tripinfo_baseline_tomtom_peak.xml')
    file_rl = os.path.join(sim_dir, 'tripinfo_rl_tomtom_peak.xml')
    
    df_base = parse_tripinfo(file_baseline, 'Baseline (Onda Verde)')
    df_rl = parse_tripinfo(file_rl, 'IA (Reinforcement Learning)')
    
    if df_base.empty or df_rl.empty:
        print("Erro: Os relatórios XML ainda não foram gerados. Rode as simulações primeiro.")
        sys.exit(1)
        
    df_all = pd.concat([df_base, df_rl], ignore_index=True)
    
    print("\n" + "="*50)
    print("RELATÓRIO DE TRÁFEGO: TOMTOM PEAK HOUR")
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
    
    sns.set_theme(style="whitegrid")
    
    # ---------------------------------------------------------
    # 1. GRÁFICOS DE BARRAS (MÉDIAS)
    # ---------------------------------------------------------
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Comparativo de Performance Média: Baseline vs IA', fontsize=16, fontweight='bold')
    
    sns.barplot(data=df_all, x='Scenario', y='Waiting Time (s)', hue='Scenario', ax=axes[0,0], palette="viridis", legend=False)
    axes[0,0].set_title('Tempo Parado Médio por Carro')
    axes[0,0].set_ylabel('Segundos')
    
    sns.barplot(data=df_all, x='Scenario', y='Time Loss (s)', hue='Scenario', ax=axes[0,1], palette="magma", legend=False)
    axes[0,1].set_title('Tempo Total Perdido (Lentidão + Paradas)')
    axes[0,1].set_ylabel('Segundos')
    
    sns.barplot(data=df_all, x='Scenario', y='Duration (s)', hue='Scenario', ax=axes[1,0], palette="coolwarm", legend=False)
    axes[1,0].set_title('Duração Média da Viagem')
    axes[1,0].set_ylabel('Segundos')
    
    sns.barplot(data=df_all, x='Scenario', y='Waiting Count', hue='Scenario', ax=axes[1,1], palette="crest", legend=False)
    axes[1,1].set_title('Média de Paradas (Freia e Arranca)')
    axes[1,1].set_ylabel('Quantidade de Paradas')
    
    plt.tight_layout()
    plot_path = os.path.join(sim_dir, 'results_comparison.png')
    plt.savefig(plot_path, dpi=300)
    plt.close()
    
    # ---------------------------------------------------------
    # 2. GRÁFICOS DE DISTRIBUIÇÃO (VIOLIN PLOTS - OUTLIERS)
    # ---------------------------------------------------------
    fig2, axes2 = plt.subplots(1, 2, figsize=(14, 6))
    fig2.suptitle('Distribuição e Dispersão de Dados (Análise de Outliers)', fontsize=16, fontweight='bold')
    
    sns.violinplot(data=df_all, x='Scenario', y='Waiting Time (s)', hue='Scenario', ax=axes2[0], palette="viridis", inner="quartile", legend=False)
    axes2[0].set_title('Distribuição do Tempo Parado')
    axes2[0].set_ylabel('Segundos')
    
    sns.violinplot(data=df_all, x='Scenario', y='Time Loss (s)', hue='Scenario', ax=axes2[1], palette="magma", inner="quartile", legend=False)
    axes2[1].set_title('Distribuição do Tempo Perdido')
    axes2[1].set_ylabel('Segundos')
    
    plt.tight_layout()
    dist_path = os.path.join(sim_dir, 'results_distribution.png')
    plt.savefig(dist_path, dpi=300)
    plt.close()
    
    # ---------------------------------------------------------
    # 3. GRÁFICO DE DISPERSÃO (DISTÂNCIA VS TEMPO PARADO)
    # ---------------------------------------------------------
    fig3, ax3 = plt.subplots(figsize=(10, 6))
    sns.scatterplot(data=df_all, x='Route Length (m)', y='Waiting Time (s)', hue='Scenario', alpha=0.5, palette=['#e74c3c', '#2ecc71'])
    ax3.set_title('Distância da Viagem vs Tempo Parado (Eficiência do Roteamento)', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Distância Percorrida (metros)')
    ax3.set_ylabel('Tempo Parado (s)')
    
    plt.tight_layout()
    scatter_path = os.path.join(sim_dir, 'results_scatter.png')
    plt.savefig(scatter_path, dpi=300)
    plt.close()
    
    print(f"Gráficos gerados com sucesso na pasta 'simulations/':")
    print(f"- {os.path.basename(plot_path)}")
    print(f"- {os.path.basename(dist_path)}")
    print(f"- {os.path.basename(scatter_path)}")

if __name__ == "__main__":
    generate_report_and_plots()
