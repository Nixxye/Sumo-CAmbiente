# -*- coding: utf-8 -*-
"""
Gerador de tráfego FOCADO no corredor da Av. Presidente Kennedy.

O gerador padrão (generate_traffic.py / randomTrips) espalha viagens por TODA a
rede de Curitiba, de modo que pouquíssimos veículos percorrem o corredor da
Av. Kennedy no sentido SW->NE. Como a Onda Verde só coordena os 13 semáforos
desse corredor, o ganho fica "diluído" em meio ao tráfego aleatório.

Este script cria um perfil de tráfego em que a MAIORIA dos veículos viaja ao
longo da Av. Kennedy (nos dois sentidos), permitindo observar o efeito real da
Onda Verde. As rotas são calculadas pelo próprio SUMO a partir das arestas de
entrada/saída dos 13 semáforos do corredor.

Uso:
    python src/controllers/generate_corridor_traffic.py
    python src/controllers/generate_corridor_traffic.py --period 1.5 --end 1800
"""

import os
import sys
import argparse

import sumolib
import traci

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Semáforos do corredor, ordenados SW -> NE (ver analise_semaforos.md).
CORRIDOR_TLS = [
    "cluster_1228396488_1228396496_12383681474_12383681477_#13more",
    "cluster_12233610671_12383681489_2381179437_2381179438_#2more",
    "cluster_2381177128_2381177130_3632225112_3632225115",
    "cluster_12383681492_12383681493_12383681495_12383681496_#2more",
    "joinedS_1975204388_cluster_1362816445_6923680624",
    "cluster_613858201_6923680625",
    "cluster_10250042714_12383691010_12383691011_12383691012_#3more",
    "cluster_12383691014_12383691015_12383691016_12383691017_#4more",
    "cluster_12383691020_12383691021_12383691022_12383691023_#2more",
    "cluster_12383691026_12383691027_12383691028_12383691029_#2more",
    "cluster_12379246807_12379246808_12379246809_12379246810_#2more",
    "cluster_12379246811_12379246812_12379246813_12379246814_#2more",
    "joinedS_267193384_267419701_267419930_cluster_1227009262_8479003389",
]


def _edges_por_semaforo(net_file):
    """Para cada semáforo do corredor, devolve o conjunto de arestas controladas."""
    traci.start([sumolib.checkBinary("sumo"), "-n", net_file,
                 "--no-step-log", "true", "--no-warnings", "true"])
    node_edges = {}
    for tid in CORRIDOR_TLS:
        edges = set()
        for ln in traci.trafficlight.getControlledLanes(tid):
            try:
                eid = traci.lane.getEdgeID(ln)
                if not eid.startswith(":"):
                    edges.add(eid)
            except Exception:
                pass
        node_edges[tid] = edges
    traci.close()
    return node_edges


def _edge_de(net, tid, node_edges):
    """Escolhe uma aresta normal (drivável por carro) associada ao semáforo."""
    for eid in node_edges[tid]:
        try:
            e = net.getEdge(eid)
            if e.allows("passenger"):
                return e
        except Exception:
            continue
    return None


def gerar(net_file=None, route_file=None, period=6.0, end_time=600,
          fracao_reverso=0.3):
    net_file = net_file or os.path.join(BASE_DIR, "data", "map", "curitiba.net.xml")
    route_file = route_file or os.path.join(BASE_DIR, "data", "traffic", "kennedy_corridor.rou.xml")
    os.makedirs(os.path.dirname(route_file), exist_ok=True)

    print("Lendo a rede (pode levar alguns segundos)...")
    net = sumolib.net.readNet(net_file)
    node_edges = _edges_por_semaforo(net_file)

    e_sw = _edge_de(net, CORRIDOR_TLS[0], node_edges)    # extremo SW
    e_ne = _edge_de(net, CORRIDOR_TLS[-1], node_edges)   # extremo NE
    if not e_sw or not e_ne:
        print("ERRO: não foi possível localizar as arestas extremas do corredor.")
        sys.exit(1)

    # Pontos intermediários (via) para forçar o trajeto pela avenida.
    vias_sw_ne = []
    for tid in CORRIDOR_TLS[1:-1]:
        e = _edge_de(net, tid, node_edges)
        if e:
            vias_sw_ne.append(e.getID())

    sw_id, ne_id = e_sw.getID(), e_ne.getID()
    via_attr = " ".join(vias_sw_ne)

    # Frequência: corredor recebe a maior parte; fundo aleatório é leve.
    veiculos_por_hora_corr = int(3600 / period)

    print(f"Corredor: {sw_id} (SW) -> {ne_id} (NE), {len(vias_sw_ne)} pontos intermediários.")
    print(f"Gerando fluxos (~{veiculos_por_hora_corr} veíc/h por sentido)...")

    vph_reverso = int(veiculos_por_hora_corr * fracao_reverso)
    flow_reverso = ""
    if vph_reverso > 0:
        flow_reverso = (
            f'\n    <!-- Fluxo no sentido oposto NE -> SW (rotas calculadas pelo SUMO) -->\n'
            f'    <flow id="kennedy_ne_sw" type="carro" begin="0" end="{end_time}" '
            f'vehsPerHour="{vph_reverso}" from="{ne_id}" to="{sw_id}" '
            f'departLane="best" departSpeed="max"/>\n'
        )

    conteudo = f"""<?xml version="1.0" encoding="UTF-8"?>
<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">

    <vType id="carro" vClass="passenger" maxSpeed="16.7" accel="2.6" decel="4.5" sigma="0.5"/>

    <!-- Fluxo principal SW -> NE ao longo da Av. Kennedy (beneficiado pela Onda Verde) -->
    <flow id="kennedy_sw_ne" type="carro" begin="0" end="{end_time}" vehsPerHour="{veiculos_por_hora_corr}"
          from="{sw_id}" to="{ne_id}" via="{via_attr}" departLane="best" departSpeed="max"/>
{flow_reverso}</routes>
"""
    # Escreve um arquivo temporário de fluxos e usa o duarouter para validar/expandir.
    flows_file = route_file.replace(".rou.xml", ".flows.xml")
    with open(flows_file, "w", encoding="utf-8") as f:
        f.write(conteudo)

    duarouter = sumolib.checkBinary("duarouter")
    import subprocess
    cmd = [duarouter, "-n", net_file, "-r", flows_file, "-o", route_file,
           "--ignore-errors", "true", "--no-step-log", "true",
           "--repair", "true"]
    print("Validando e expandindo rotas com duarouter...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("duarouter stderr:\n", res.stderr[-1500:])
        # fallback: usa o arquivo de fluxos diretamente (SUMO roteia em tempo real)
        print(f"[Fallback] Usando o arquivo de fluxos diretamente: {flows_file}")
        return flows_file

    print(f"[OK] Tráfego do corredor gerado em: {route_file}")
    return route_file


def main():
    parser = argparse.ArgumentParser(description="Gera tráfego focado no corredor da Av. Kennedy.")
    parser.add_argument("--period", type=float, default=6.0,
                        help="Intervalo médio entre veículos no corredor (s). Menor = mais tráfego. "
                             "Use valores altos (>=5) para manter o corredor sem saturação.")
    parser.add_argument("--end", type=int, default=600, help="Tempo final de geração (s).")
    parser.add_argument("--reverso", type=float, default=0.3,
                        help="Fração do fluxo no sentido oposto (NE->SW). 0 = só SW->NE.")
    args = parser.parse_args()
    gerar(period=args.period, end_time=args.end, fracao_reverso=args.reverso)


if __name__ == "__main__":
    main()
