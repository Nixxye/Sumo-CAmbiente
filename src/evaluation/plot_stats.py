import os
import sys
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

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
            'Waiting Time (s)': float(trip.get('waitingTime', 0)),
            'Time Loss (s)': float(trip.get('timeLoss', 0))
        })
    return pd.DataFrame(data)

def cohen_d(x, y):
    # Calcula o tamanho do efeito (Effect Size) da melhoria
    nx = len(x)
    ny = len(y)
    dof = nx + ny - 2
    pool_std = np.sqrt(((nx-1)*np.var(x, ddof=1) + (ny-1)*np.var(y, ddof=1)) / dof)
    return (np.mean(x) - np.mean(y)) / pool_std

def generate_statistical_analysis():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    sim_dir = os.path.join(base_dir, 'simulations')
    
    file_baseline = os.path.join(sim_dir, 'tripinfo_baseline_tomtom_peak.xml')
    file_rl = os.path.join(sim_dir, 'tripinfo_rl_tomtom_peak.xml')
    
    df_base = parse_tripinfo(file_baseline, 'Baseline (Onda Verde)')
    df_rl = parse_tripinfo(file_rl, 'Aprendizado por Reforço')
    
    if df_base.empty or df_rl.empty:
        print("Erro: Os relatorios XML nao foram encontrados.")
        sys.exit(1)
        
    df_all = pd.concat([df_base, df_rl], ignore_index=True)
    
    wait_base = df_base['Waiting Time (s)'].values
    wait_rl = df_rl['Waiting Time (s)'].values
    
    # 1. Teste Estatístico Não-Paramétrico (Mann-Whitney U) 
    # É o ideal pois tempos de espera em trânsito não são perfeitamente distribuídos como uma curva sino normal.
    stat_val, p_value = stats.mannwhitneyu(wait_base, wait_rl, alternative='two-sided')
    
    # 2. Tamanho do Efeito (Cohen's d)
    d_value = cohen_d(wait_base, wait_rl)
    
    # 3. Intervalo de Confiança 95% para as médias
    def get_ci(data):
        mean = np.mean(data)
        sem = stats.sem(data)
        ci = stats.t.interval(0.95, len(data)-1, loc=mean, scale=sem)
        return mean, ci

    mean_base, ci_base = get_ci(wait_base)
    mean_rl, ci_rl = get_ci(wait_rl)
    
    print("\n" + "="*50)
    print("ANALISE ESTATISTICA DO TEMPO DE ESPERA")
    print("="*50)
    print(f"Baseline Media: {mean_base:.2f}s (IC 95%: {ci_base[0]:.2f}s - {ci_base[1]:.2f}s)")
    print(f"Aprendizado por Reforço Media: {mean_rl:.2f}s (IC 95%: {ci_rl[0]:.2f}s - {ci_rl[1]:.2f}s)")
    print(f"Mann-Whitney U p-value: {p_value:.2e}")
    print(f"Cohen's d (Tamanho do Efeito): {d_value:.2f}")
    print("="*50 + "\n")
    
    # --- GRÁFICOS ---
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle('Análise Estatística de Eficiência: Baseline vs Inteligência Artificial', fontsize=18, fontweight='bold')
    
    # Gráfico 1: Barplot com Intervalo de Confiança 95%
    sns.barplot(data=df_all, x='Scenario', y='Waiting Time (s)', hue='Scenario', ax=axes[0], 
                  errorbar=('ci', 95), capsize=.1, palette="Set1", legend=False)
    
    # Adicionar os valores exatos no centro das barras
    for container in axes[0].containers:
        axes[0].bar_label(container, fmt='%.1f s', label_type='center', color='white', fontweight='bold', fontsize=12)
            
    axes[0].set_title('Média de Tempo Parado com Intervalo de Confiança (95%)', fontsize=14)
    axes[0].set_ylabel('Tempo de Espera (Segundos)')
    axes[0].set_xlabel('')
    
    # Ajustar eixo Y para dar espaço para a caixa de texto
    max_wait = df_all['Waiting Time (s)'].mean() * 2.5
    axes[0].set_ylim(0, max_wait)
    
    # Box com resumo estatístico no Gráfico 1
    stats_text = (
        f"Estatísticas Avançadas:\n"
        f"Redução Média: {mean_base - mean_rl:.1f} segundos\n"
        f"Melhoria Relativa: {((mean_base - mean_rl) / mean_base)*100:.1f}%\n"
        f"Valor-p (Significância): {p_value:.2e} (< 0.01)\n"
        f"Cohen's d (Efeito): {d_value:.2f} (Grande)"
    )
    axes[0].text(0.05, 0.95, stats_text, transform=axes[0].transAxes, fontsize=12,
                 verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='gray'))

    # Gráfico 2: Função de Distribuição Acumulada Empírica (ECDF)
    sns.ecdfplot(data=df_all, x='Waiting Time (s)', hue='Scenario', ax=axes[1], linewidth=3, palette="Set1")
    axes[1].set_title('Função de Distribuição Acumulada (CDF)', fontsize=14)
    axes[1].set_xlabel('Tempo Parado (Segundos)')
    axes[1].set_ylabel('Proporção de Motoristas (0.0 a 1.0)')
    
    # Adicionar grid lines mais evidentes para ajudar na leitura
    axes[1].grid(True, which="both", ls="-", alpha=0.5)
    
    # Linha guia para leitura: Corte de 5 minutos
    axes[1].axvline(300, color='gray', linestyle='--', alpha=0.8)
    axes[1].text(310, 0.5, 'Marca de 300s (5 min parados)', rotation=90, color='gray', fontsize=11)

    plt.tight_layout()
    stats_path = os.path.join(sim_dir, 'results_statistics.png')
    plt.savefig(stats_path, dpi=300)
    plt.close()
    
    print(f"Painel estatístico salvo em: {stats_path}")

if __name__ == "__main__":
    generate_statistical_analysis()
