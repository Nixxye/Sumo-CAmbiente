# -*- coding: utf-8 -*-
"""
Comparação dos 3 métodos de controle semafórico no corredor da Av. Kennedy:

    1. baseline   -> lógica padrão do SUMO (programas fixos do curitiba.net.xml)
    2. rl         -> agente de Aprendizado por Reforço (PPO) já existente
    3. green_wave -> Onda Verde com offsets fixos (novo controlador)

O script roda os três cenários com o MESMO perfil de tráfego, coleta métricas
comparáveis (tempo de espera médio por viagem via tripinfo, velocidade média e
throughput) e gera um relatório com gráficos comparativos.

Uso:
    python compare_methods.py --traffic random_peak
    python compare_methods.py --traffic random_peak --end 1800
    python compare_methods.py --traffic random_peak --skip-rl   # ignora o RL
"""

import os
import sys
import json
import argparse
import xml.etree.ElementTree as ET

import sumolib

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)

import traci  # noqa: E402
from src.controllers.greenwave_controller import GreenWaveController  # noqa: E402

NET_FILE = os.path.join(BASE_DIR, "data", "map", "curitiba.net.xml")
RESULTS_DIR = os.path.join(BASE_DIR, "results")

# Cores por método (consistentes em todos os gráficos).
CORES = {"baseline": "#1f77b4", "rl": "#ff7f0e", "green_wave": "#2ca02c"}
ROTULOS = {"baseline": "Baseline (SUMO)", "rl": "RL (PPO)", "green_wave": "Onda Verde"}


def parse_tripinfo(tripinfo_file):
    """Devolve (espera_total, espera_media_por_viagem, n_viagens, tempo_viagem_medio)."""
    if not os.path.exists(tripinfo_file):
        return None
    try:
        root = ET.parse(tripinfo_file).getroot()
    except ET.ParseError:
        # Recupera arquivos truncados (ex.: simulação interrompida): mantém apenas
        # as entradas <tripinfo .../> completas e fecha a raiz manualmente.
        with open(tripinfo_file, "r", encoding="utf-8") as f:
            linhas = [ln for ln in f if ln.strip().startswith("<tripinfo ")]
        xml = "<tripinfos>\n" + "".join(linhas) + "</tripinfos>"
        try:
            root = ET.fromstring(xml)
        except Exception as e:
            print(f"Erro ao ler {tripinfo_file}: {e}")
            return None
    total_espera = 0.0
    total_duracao = 0.0
    n = 0
    for trip in root.findall("tripinfo"):
        total_espera += float(trip.get("waitingTime", 0))
        total_duracao += float(trip.get("duration", 0))
        n += 1
    if n == 0:
        return 0.0, 0.0, 0, 0.0
    return total_espera, total_espera / n, n, total_duracao / n


def _sumo_cmd(route_file, tripinfo_file, use_gui=False):
    return [
        sumolib.checkBinary("sumo-gui" if use_gui else "sumo"),
        "-n", NET_FILE,
        "-r", route_file,
        "--tripinfo-output", tripinfo_file,
        "--no-step-log", "true",
        "--no-warnings", "true",
        "--waiting-time-memory", "10000",
    ]


def _finalizar(collector, tripinfo_file, metodo):
    """Monta o dicionário de métricas de um método a partir do collector + tripinfo."""
    m = collector.get_metrics()
    m["metodo"] = metodo
    trip = parse_tripinfo(tripinfo_file)
    if trip:
        espera_total, espera_media, n_viagens, dur_media = trip
        m["tripinfo_tempo_espera_total_s"] = round(espera_total, 2)
        m["tripinfo_tempo_espera_medio_por_viagem_s"] = round(espera_media, 2)
        m["tripinfo_viagens_concluidas"] = n_viagens
        m["tripinfo_tempo_viagem_medio_s"] = round(dur_media, 2)
    return m


def run_baseline(route_file, end_time=None):
    tripinfo = os.path.join(RESULTS_DIR, "tripinfo_baseline_cmp.xml")
    print("\n>>> [1/3] Executando BASELINE (SUMO padrão)...")
    traci.start(_sumo_cmd(route_file, tripinfo))
    collector = GreenWaveController(verbose=False)
    collector._discover_traffic_lights()  # apenas para registrar os semáforos
    # NÃO aplica offsets: este é o comportamento padrão do SUMO.
    while traci.simulation.getMinExpectedNumber() > 0:
        if end_time and traci.simulation.getTime() >= end_time:
            break
        traci.simulationStep()
        collector.collect_step_metrics()
    traci.close()
    return _finalizar(collector, tripinfo, "baseline")


def run_green_wave(route_file, end_time=None):
    tripinfo = os.path.join(RESULTS_DIR, "tripinfo_green_wave_cmp.xml")
    print("\n>>> [3/3] Executando ONDA VERDE (offsets fixos)...")
    traci.start(_sumo_cmd(route_file, tripinfo))
    collector = GreenWaveController(verbose=True)
    collector.apply_offsets()  # aplica offsets fixos no início
    while traci.simulation.getMinExpectedNumber() > 0:
        if end_time and traci.simulation.getTime() >= end_time:
            break
        traci.simulationStep()
        collector.collect_step_metrics()
    traci.close()
    return _finalizar(collector, tripinfo, "green_wave")


def run_rl(route_file, end_time=None):
    """Executa o cenário RL (PPO). Retorna None se o modelo não existir."""
    model_path = os.path.join(BASE_DIR, "src", "rl", "model_ppo.zip")
    if not os.path.exists(model_path):
        print("\n>>> [2/3] RL IGNORADO: modelo não encontrado em src/rl/model_ppo.zip")
        print("    Treine o modelo com: python src/rl/train.py")
        return None
    try:
        from stable_baselines3 import PPO
        from src.rl.env import SumoTrafficEnv
    except Exception as e:
        print(f"\n>>> [2/3] RL IGNORADO: dependências indisponíveis ({e})")
        return None

    tripinfo = os.path.join(RESULTS_DIR, "tripinfo_rl_cmp.xml")
    print("\n>>> [2/3] Executando RL (PPO)...")
    model = PPO.load(model_path)
    env = SumoTrafficEnv(net_file=NET_FILE, route_file=route_file,
                         tripinfo_file=tripinfo, render_mode="none")
    obs, _ = env.reset()
    # Reaproveita o coletor de métricas usando a conexão TraCI do ambiente.
    collector = GreenWaveController(conn=env.conn, verbose=False)
    done = False
    while not done:
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, _ = env.step(action)
        collector.collect_step_metrics()
        done = terminated or truncated
        if end_time and env.conn.simulation.getTime() >= end_time:
            break
    env.close()
    return _finalizar(collector, tripinfo, "rl")


def gerar_graficos(resultados, traffic):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("[Aviso] matplotlib não instalado; gráficos não gerados.")
        return

    metodos = [m for m in ("baseline", "rl", "green_wave") if m in resultados]

    # --- Gráfico 1: tempo de espera ao longo do tempo ---
    fig, ax = plt.subplots(figsize=(11, 5))
    for met in metodos:
        serie = resultados[met].get("serie_temporal", [])
        if serie:
            ax.plot([a["tempo"] for a in serie], [a["tempo_espera_total_s"] for a in serie],
                    label=ROTULOS[met], color=CORES[met], linewidth=1.8)
    ax.set_xlabel("Tempo de simulação (s)")
    ax.set_ylabel("Tempo de espera total (s)")
    ax.set_title(f"Comparação — Tempo de espera ao longo do tempo ({traffic})")
    ax.legend(); ax.grid(True, alpha=0.3)
    fig.tight_layout()
    p1 = os.path.join(RESULTS_DIR, f"comparacao_espera_{traffic}.png")
    fig.savefig(p1, dpi=120); plt.close(fig)
    print(f"[OK] Gráfico salvo: {p1}")

    # --- Gráfico 2: velocidade média ao longo do tempo ---
    fig, ax = plt.subplots(figsize=(11, 5))
    for met in metodos:
        serie = resultados[met].get("serie_temporal", [])
        if serie:
            ax.plot([a["tempo"] for a in serie], [a["velocidade_media_kmh"] for a in serie],
                    label=ROTULOS[met], color=CORES[met], linewidth=1.8)
    ax.set_xlabel("Tempo de simulação (s)")
    ax.set_ylabel("Velocidade média (km/h)")
    ax.set_title(f"Comparação — Velocidade média ao longo do tempo ({traffic})")
    ax.legend(); ax.grid(True, alpha=0.3)
    fig.tight_layout()
    p2 = os.path.join(RESULTS_DIR, f"comparacao_velocidade_{traffic}.png")
    fig.savefig(p2, dpi=120); plt.close(fig)
    print(f"[OK] Gráfico salvo: {p2}")

    # --- Gráfico 3: barras (espera média por viagem) ---
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(12, 5))
    rotulos = [ROTULOS[m] for m in metodos]
    cores = [CORES[m] for m in metodos]

    esperas = [resultados[m].get("tripinfo_tempo_espera_medio_por_viagem_s", 0) for m in metodos]
    axA.bar(rotulos, esperas, color=cores)
    axA.set_ylabel("Espera média por viagem (s)")
    axA.set_title("Tempo de espera médio por viagem")
    for i, v in enumerate(esperas):
        axA.text(i, v, f"{v:.1f}", ha="center", va="bottom")

    viagens = [resultados[m].get("tripinfo_viagens_concluidas", 0) for m in metodos]
    axB.bar(rotulos, viagens, color=cores)
    axB.set_ylabel("Viagens concluídas")
    axB.set_title("Throughput (viagens concluídas)")
    for i, v in enumerate(viagens):
        axB.text(i, v, f"{v}", ha="center", va="bottom")

    fig.suptitle(f"Comparação de métodos ({traffic})")
    fig.tight_layout()
    p3 = os.path.join(RESULTS_DIR, f"comparacao_barras_{traffic}.png")
    fig.savefig(p3, dpi=120); plt.close(fig)
    print(f"[OK] Gráfico salvo: {p3}")


def imprimir_relatorio(resultados):
    print("\n" + "=" * 78)
    print("  RELATÓRIO COMPARATIVO DE MÉTODOS")
    print("=" * 78)
    cab = f"  {'Método':<18}{'Espera/viagem(s)':>18}{'Vel.média(km/h)':>18}{'Viagens':>12}"
    print(cab)
    print("  " + "-" * 74)
    for met in ("baseline", "rl", "green_wave"):
        if met not in resultados:
            continue
        m = resultados[met]
        espera = m.get("tripinfo_tempo_espera_medio_por_viagem_s", float("nan"))
        vel = m.get("velocidade_media_kmh", float("nan"))
        viagens = m.get("tripinfo_viagens_concluidas", 0)
        print(f"  {ROTULOS[met]:<18}{espera:>18.2f}{vel:>18.2f}{viagens:>12}")
    print("=" * 78)

    # Destaque do ganho da Onda Verde frente ao baseline.
    if "baseline" in resultados and "green_wave" in resultados:
        eb = resultados["baseline"].get("tripinfo_tempo_espera_medio_por_viagem_s")
        eg = resultados["green_wave"].get("tripinfo_tempo_espera_medio_por_viagem_s")
        if eb and eb > 0:
            ganho = (eb - eg) / eb * 100
            sinal = "redução" if ganho >= 0 else "aumento"
            print(f"  Onda Verde vs Baseline: {sinal} de {abs(ganho):.1f}% na espera média por viagem.")
    print("=" * 78 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Compara baseline, RL e Onda Verde (SUMO).")
    parser.add_argument("--traffic", default="random_peak", help="Prefixo do arquivo de tráfego.")
    parser.add_argument("--end", type=int, default=None, help="Tempo-limite de simulação (s).")
    parser.add_argument("--skip-rl", action="store_true", help="Não executa o cenário RL.")
    args = parser.parse_args()

    os.makedirs(RESULTS_DIR, exist_ok=True)
    route_file = os.path.join(BASE_DIR, "data", "traffic", f"{args.traffic}.rou.xml")
    if not os.path.exists(NET_FILE) or not os.path.exists(route_file):
        print("ERRO: rede ou arquivo de tráfego não encontrado. Veja COMO_USAR.md.")
        sys.exit(1)

    resultados = {}
    resultados["baseline"] = run_baseline(route_file, args.end)
    if not args.skip_rl:
        rl = run_rl(route_file, args.end)
        if rl is not None:
            resultados["rl"] = rl
    resultados["green_wave"] = run_green_wave(route_file, args.end)

    # Salva o JSON comparativo (sem as séries volumosas no console).
    out_json = os.path.join(RESULTS_DIR, f"comparacao_metodos_{args.traffic}.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Comparação salva em: {out_json}")

    imprimir_relatorio(resultados)
    gerar_graficos(resultados, args.traffic)


if __name__ == "__main__":
    main()
