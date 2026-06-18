# -*- coding: utf-8 -*-
"""
Controlador de Onda Verde (Green Wave) para a Av. Presidente Kennedy - Curitiba.

Este módulo implementa um controlador TraCI que aplica OFFSETS FIXOS (defasagens)
nos 13 semáforos da Av. Kennedy no início da simulação, criando uma "Onda Verde"
coordenada no sentido SW -> NE a uma velocidade-alvo de 50 km/h.

Princípio (ver analise_semaforos.md):
    v_alvo      = 50 km/h = 13,889 m/s
    t_viagem(i) = dist_acumulada(i) / v_alvo      # tempo até o semáforo i
    offset(i)   = t_viagem(i) MOD ciclo(i)        # defasagem dentro do ciclo

Como o offset é aplicado:
    Cada semáforo da rede roda um programa estático próprio (o SUMO mantém o ciclo
    girando automaticamente). Para impor a defasagem, no instante t=0 posicionamos
    cada semáforo dentro do seu ciclo de forma que a sua FASE VERDE de referência
    (movimento SW->NE) comece exatamente `offset(i)` segundos após o início da
    simulação. A partir daí o SUMO mantém todos os ciclos sincronizados sozinho,
    pois nenhum outro comando de fase é enviado.

Uso típico:
    from greenwave_controller import GreenWaveController
    controller = GreenWaveController()           # usa a conexão TraCI padrão
    controller.apply_offsets()                   # aplica no início (t=0)
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        controller.collect_step_metrics()
    resultado = controller.get_metrics()
"""

import traci


# ---------------------------------------------------------------------------
# Offsets de Onda Verde (segundos) por programa de semáforo.
# Calculados para 50 km/h, sentido SW -> NE. Fonte: analise_semaforos.md (Seção 4).
# ---------------------------------------------------------------------------
GREEN_WAVE_OFFSETS = {
    "cluster_1228396488_1228396496_12383681474_12383681477_#13more": 0.0,
    "cluster_12233610671_12383681489_2381179437_2381179438_#2more": 14.9,
    "cluster_2381177128_2381177130_3632225112_3632225115": 30.3,
    "cluster_12383681492_12383681493_12383681495_12383681496_#2more": 38.3,
    "joinedS_1975204388_cluster_1362816445_6923680624": 47.1,
    "cluster_613858201_6923680625": 49.7,
    "cluster_10250042714_12383691010_12383691011_12383691012_#3more": 62.0,
    "cluster_12383691014_12383691015_12383691016_12383691017_#4more": 53.6,
    "cluster_12383691020_12383691021_12383691022_12383691023_#2more": 67.3,
    "cluster_12383691026_12383691027_12383691028_12383691029_#2more": 86.0,
    "cluster_12379246807_12379246808_12379246809_12379246810_#2more": 2.9,
    "cluster_12379246811_12379246812_12379246813_12379246814_#2more": 18.9,
    "joinedS_267193384_267419701_267419930_cluster_1227009262_8479003389": 31.8,
}


class GreenWaveController:
    """Aplica offsets fixos de Onda Verde e coleta métricas durante a simulação."""

    def __init__(self, conn=None, offsets=None, verbose=True):
        """
        Args:
            conn: conexão TraCI (objeto retornado por traci.getConnection()).
                  Se None, usa o módulo `traci` global (conexão padrão).
            offsets: dicionário {id_semaforo: offset_segundos}. Se None usa
                     GREEN_WAVE_OFFSETS.
            verbose: imprime mensagens de progresso.
        """
        self.conn = conn if conn is not None else traci
        self.offsets = dict(offsets) if offsets is not None else dict(GREEN_WAVE_OFFSETS)
        self.verbose = verbose

        # Semáforos efetivamente presentes na rede carregada.
        self.controlled_tls = []
        # Guarda o ciclo (s) de cada semáforo controlado, para conferência.
        self.tls_cycle = {}

        # --- Estruturas de métricas ---
        self._applied = False
        self.time_series = []          # lista de dicts por amostra (t, espera, velocidade...)
        self._counted_vehicles = set() # veículos já vistos (para throughput)
        self._arrived_total = 0        # total acumulado de veículos que chegaram ao destino
        self._sample_interval = 10     # segundos entre amostras da série temporal
        self._last_sample_time = -1e9

    # ------------------------------------------------------------------ #
    #  Identificação dos semáforos da Av. Kennedy presentes na rede
    # ------------------------------------------------------------------ #
    def _discover_traffic_lights(self):
        rede = set(self.conn.trafficlight.getIDList())
        self.controlled_tls = [tid for tid in self.offsets if tid in rede]
        ausentes = [tid for tid in self.offsets if tid not in rede]
        if self.verbose:
            print(f"[OndaVerde] Semáforos da Av. Kennedy encontrados na rede: "
                  f"{len(self.controlled_tls)}/{len(self.offsets)}")
            for tid in ausentes:
                print(f"[OndaVerde]   AVISO: semáforo ausente na rede -> {tid}")
        return self.controlled_tls

    # ------------------------------------------------------------------ #
    #  Aplicação dos offsets fixos (início da simulação, t=0)
    # ------------------------------------------------------------------ #
    def _reference_green_phase(self, logic):
        """Retorna o índice da fase de VERDE PRINCIPAL (movimento arterial SW->NE).

        Heurística: a fase do movimento principal da avenida costuma ser a fase
        de maior duração que contém verde "forte" ('G'). Usamos o número de 'G'
        como critério de desempate (mais aproximações verdes = via principal).
        É o início dessa fase que deve ser defasado pelo offset da Onda Verde.
        """
        melhor_idx = 0
        melhor_score = -1.0
        for idx, phase in enumerate(logic.phases):
            n_G = phase.state.count("G")
            if n_G == 0:
                continue
            # Pontuação: prioriza duração (verde mais longo) e nº de 'G'.
            score = phase.duration + 0.1 * n_G
            if score > melhor_score:
                melhor_score = score
                melhor_idx = idx
        return melhor_idx

    def apply_offsets(self):
        """Posiciona cada semáforo no seu ciclo para impor o offset da Onda Verde.

        Deve ser chamado UMA vez, logo após o início da simulação (t=0) e antes
        do primeiro simulationStep da coleta (ou imediatamente após o reset).
        """
        self._discover_traffic_lights()

        for tid in self.controlled_tls:
            offset = float(self.offsets[tid])
            logic = self.conn.trafficlight.getAllProgramLogics(tid)[0]
            phases = logic.phases
            cycle = sum(p.duration for p in phases)
            self.tls_cycle[tid] = cycle
            if cycle <= 0:
                continue

            # Índice da fase verde de referência (início do verde principal).
            green_idx = self._reference_green_phase(logic)

            # Tempo, dentro do ciclo, em que a fase verde de referência começa.
            green_start = sum(p.duration for p in phases[:green_idx])

            # Queremos que a fase verde comece em t = offset (mod ciclo).
            # Logo, no instante t=0, a "posição" do programa dentro do ciclo deve ser:
            #   pos0 = (green_start - offset) mod ciclo
            pos0 = (green_start - offset) % cycle

            # Descobre em qual fase cai pos0 e quanto tempo resta nela.
            acumulado = 0.0
            destino_fase = 0
            tempo_restante = phases[0].duration
            for idx, p in enumerate(phases):
                if acumulado <= pos0 < acumulado + p.duration:
                    destino_fase = idx
                    decorrido = pos0 - acumulado
                    tempo_restante = p.duration - decorrido
                    break
                acumulado += p.duration

            # Aplica: define a fase atual e o tempo restante dela.
            # A partir daqui o SUMO segue o programa estático sozinho, mantendo
            # o ciclo sincronizado durante toda a simulação.
            self.conn.trafficlight.setPhase(tid, destino_fase)
            self.conn.trafficlight.setPhaseDuration(tid, max(tempo_restante, 0.1))

        self._applied = True
        if self.verbose:
            print(f"[OndaVerde] Offsets fixos aplicados em {len(self.controlled_tls)} "
                  f"semáforos (Onda Verde SW->NE @ 50 km/h).")
        return self.controlled_tls

    # ------------------------------------------------------------------ #
    #  Coleta de métricas durante a simulação
    # ------------------------------------------------------------------ #
    def collect_step_metrics(self):
        """Coleta métricas no passo atual. Deve ser chamado após cada simulationStep().

        Métricas registradas (série temporal, a cada `_sample_interval` segundos):
            - tempo de simulação
            - número de veículos em circulação
            - velocidade média (m/s e km/h)
            - tempo de espera acumulado total (s)
            - throughput acumulado (veículos que chegaram ao destino)
        """
        # Acumula veículos que chegaram ao destino (throughput acumulado real).
        try:
            self._arrived_total += self.conn.simulation.getArrivedNumber()
        except Exception:
            pass

        veic_ids = self.conn.vehicle.getIDList()
        for vid in veic_ids:
            self._counted_vehicles.add(vid)

        t = self.conn.simulation.getTime()

        # Amostra a cada intervalo para não inflar a série temporal.
        if t - self._last_sample_time < self._sample_interval:
            return

        self._last_sample_time = t

        n = len(veic_ids)
        if n > 0:
            soma_vel = sum(self.conn.vehicle.getSpeed(v) for v in veic_ids)
            soma_espera = sum(self.conn.vehicle.getWaitingTime(v) for v in veic_ids)
            vel_media = soma_vel / n
        else:
            soma_espera = 0.0
            vel_media = 0.0

        amostra = {
            "tempo": round(t, 1),
            "veiculos_circulando": n,
            "velocidade_media_ms": round(vel_media, 3),
            "velocidade_media_kmh": round(vel_media * 3.6, 3),
            "tempo_espera_total_s": round(soma_espera, 2),
            "throughput_acumulado": self._arrived_total,
        }
        self.time_series.append(amostra)

    # ------------------------------------------------------------------ #
    #  Métricas finais agregadas
    # ------------------------------------------------------------------ #
    def get_metrics(self):
        """Retorna um dicionário com métricas agregadas e a série temporal."""
        if self.time_series:
            velocidades = [a["velocidade_media_kmh"] for a in self.time_series]
            esperas = [a["tempo_espera_total_s"] for a in self.time_series]
            vel_media_global = sum(velocidades) / len(velocidades)
            espera_media_amostral = sum(esperas) / len(esperas)
        else:
            vel_media_global = 0.0
            espera_media_amostral = 0.0
        throughput_total = self._arrived_total

        return {
            "metodo": "green_wave",
            "semaforos_controlados": len(self.controlled_tls),
            "offsets_aplicados": self._applied,
            "velocidade_media_kmh": round(vel_media_global, 3),
            "tempo_espera_total_medio_s": round(espera_media_amostral, 2),
            "throughput_total_veiculos": int(throughput_total),
            "veiculos_distintos_vistos": len(self._counted_vehicles),
            "serie_temporal": self.time_series,
        }
