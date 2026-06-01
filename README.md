# SUMO Curitiba: Otimização Semafórica com IA

Este projeto consiste em um ambiente de simulação de tráfego focado na região central de Curitiba (quadrilátero das ruas Pres. Kennedy, Calçadão da XV, Mal. Floriano Peixoto, Martim Afonso, Mariano Torres e Mário Tourinho).
O objetivo é comparar o cenário de semáforos convencionais (Onda Verde gerada pelo simulador) com um controlador semafórico inteligente operado por **Machine Learning (Reinforcement Learning)**.

---

## Como Rodar o Projeto

### Pré-requisitos
Certifique-se de ter o Python instalado e de ter configurado o ambiente virtual:
```bash
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

### Executando a Simulação
Utilize o `main.py` para rodar a simulação e o script avaliará o tempo parado dos veículos. Você pode escolher qual **cenário** e qual **tráfego** rodar.

1. **Rodar a Baseline (Onda Verde Padrão do SUMO):**
```bash
venv\Scripts\python main.py --scenario baseline --traffic random_peak --gui
```

2. **Rodar a Inteligência Artificial (Modelo ML/RL):**
```bash
venv\Scripts\python main.py --scenario rl --traffic random_peak --gui
```
*(Nota: Se quiser rodar rapidamente no terminal sem interface visual para captar resultados brutos, basta omitir a flag `--gui`).*

---

## Visualização Personalizada (SUMO-GUI)
O arquivo de configuração de visualização `viewsettings.xml` já se encontra na pasta `simulations/`. O script `main.py` carrega essa configuração automaticamente sempre que a flag `--gui` for usada.

---

## Onde Modificar os Algoritmos

A arquitetura foi projetada para ser modular. Se você quiser mexer no "cérebro" das simulações, procure os seguintes arquivos:

### 1. Inteligência Artificial (Machine Learning)
Se quiser mudar a lógica de recompensa, ações ou treinar um algoritmo diferente:
- **`src/rl/env.py`**: Este é o Ambiente *Gymnasium*. Nele, você pode alterar o `_get_obs()` para fornecer mais dados ao modelo (ex: velocidade média da via), alterar o `_get_reward()` para mudar a recompensa/punição da IA, e alterar o `step_length` (frequência com que a IA toma decisões).
- **`src/rl/train.py`**: Este é o script de treinamento. Aqui você pode trocar o algoritmo (ex: mudar de `PPO` para `DQN`), alterar hiperparâmetros de rede neural, e o número de `total_timesteps`. **Sempre que alterar o código, rode este script para gerar um novo `model_ppo.zip`**.

### 2. Baseline (Simulação Convencional)
Se quiser mexer no algoritmo padrão de cruzamentos (Onda Verde):
- **`src/evaluation/evaluate.py`**: Na função que roda a `baseline`, você pode inserir comandos TraCI customizados, como forçar fases semafóricas estáticas para imitar perfeitamente o tempo da URBS.
- O SUMO também carrega automaticamente lógicas semafóricas que estão dentro de `data/map/curitiba.net.xml`.

---

## Como Modificar o Trânsito

Você pode criar dezenas de cenários de trânsito (ex: *madrugada*, *domingo*, *chuva*) e rodá-los sem precisar alterar os algoritmos. O roteamento fica totalmente desacoplado!

1. **Para alterar o volume do trânsito atual:**
   Abra o arquivo **`src/controllers/generate_traffic.py`**.
   Na função `generate_traffic(...)`, procure o parâmetro **`period`**.
   - `period=1.0` -> 1 carro a cada segundo (Trânsito Médio-Pesado).
   - `period=0.5` -> 2 carros por segundo (Trânsito Caótico).
   - `period=5.0` -> 1 carro a cada 5 segundos (Trânsito Leve).
   
2. **Para gerar um novo arquivo de fluxo:**
   Após ajustar os números no Python, rode o gerador de tráfego informando nomes diferentes de arquivos dentro do script:
   ```bash
   venv\Scripts\python src\controllers\generate_traffic.py
   ```
   
3. **Como usar o tráfego novo:**
   Se o gerador salvou o tráfego como `data/traffic/madrugada.rou.xml`, basta rodar a simulação apontando para esse novo perfil usando o parâmetro `--traffic`:
   ```bash
   venv\Scripts\python main.py --scenario rl --traffic madrugada --gui
   ```
