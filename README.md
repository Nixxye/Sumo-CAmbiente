# CAmbiente: Otimização Semafórica com Inteligência Artificial

Este projeto simula o trânsito da região central de Curitiba utilizando dados reais de satélite (TomTom) e emprega técnicas avançadas de **Aprendizado por Reforço (Reinforcement Learning)** para otimizar os semáforos em tempo real, reduzindo gargalos e melhorando o fluxo veicular.

---

## 🛠️ Passo a Passo: Como rodar em outra máquina

Para executar este projeto em um novo computador (seja para apresentação ou desenvolvimento), siga rigorosamente os passos abaixo.

### 1. Pré-requisitos do Sistema
Antes de rodar o código em Python, você precisa instalar o simulador físico de trânsito (Eclipse SUMO).

* **Baixe e instale o SUMO:** Acesse [sumo.dlr.de](https://sumo.dlr.de/docs/Downloads.php) e baixe a versão para Windows (ou seu respectivo sistema operacional).
* **Variável de Ambiente (MUITO IMPORTANTE):** O SUMO precisa estar mapeado no seu sistema. 
  1. No Windows, pesquise por "Variáveis de Ambiente" no menu iniciar.
  2. Adicione uma nova variável de sistema chamada `SUMO_HOME` apontando para a pasta onde o SUMO foi instalado (Geralmente `C:\Program Files (x86)\Eclipse\Sumo` ou `C:\Program Files\Eclipse\Sumo`).
  3. Garanta que a pasta `bin` do SUMO esteja no `PATH` do sistema para que os comandos do SUMO funcionem no terminal.

### 2. Clonando o Repositório
Abra o terminal e baixe o código-fonte do projeto:
```bash
git clone https://github.com/Nixxye/Sumo-CAmbiente.git
cd Sumo-CAmbiente
```

### 3. Configurando o Ambiente Python
É necessário ter o **Python (versão 3.8 a 3.11)** instalado. 

Recomendamos criar um ambiente virtual para não poluir o seu computador com bibliotecas globais:
```bash
# 1. Criar o ambiente virtual (venv)
python -m venv venv

# 2. Ativar o ambiente (No Windows)
venv\Scripts\activate
# (Se estiver no Linux/Mac, use: source venv/bin/activate)

# 3. Instalar todas as bibliotecas de Inteligência Artificial e Data Science
pip install -r requirements.txt
```

### 4. Configurando a Chave da TomTom (Opcional)
Se você for gerar *novos* dados ou interagir com a API da TomTom, precisará da chave de acesso.
1. Na raiz do projeto, existe um arquivo chamado `.env.example`.
2. Renomeie ele para `.env`.
3. Abra o arquivo `.env` e cole a sua chave `TOMTOM_API_KEY=sua_chave_aqui`.
*(Nota: Para rodar as simulações já configuradas para a apresentação, essa etapa não é estritamente necessária, pois a topologia de peso já foi processada).*

### 5. Rodando o Projeto (A Mágica)

#### Opção A: Execução Automática (Geração de Relatórios e Gráficos)
Para rodar a simulação completa no modo "silencioso" (sem renderizar os carrinhos), rodar a avaliação estatística e gerar todos os mapas de calor, basta rodar o nosso script em lote:

```cmd
# No Windows
run_all.bat
```
Ao final do processo, todos os gráficos (`results_comparison.png`, `map_heatmap_baseline.png`, etc.) estarão disponíveis dentro da pasta `simulations/`.

#### Opção B: Execução Interativa (Visual e Manual)
Se você quiser abrir o simulador na tela (o mapa rodando) para mostrar para a banca os carros andando e o semáforo reagindo:

**Ver o problema (Semáforo Convencional / Onda Verde):**
```bash
python main.py --scenario baseline --traffic tomtom_peak --gui
```

**Ver a solução (Semáforo com Inteligência Artificial):**
```bash
python main.py --scenario rl --traffic tomtom_peak --gui
```
*(No simulador que se abrirá, basta clicar no botão de "Play" verde na parte superior para iniciar o fluxo do tempo).*

---

## 💻 Stack Tecnológico
* **Eclipse SUMO / TraCI:** Microssimulação física de tráfego.
* **Stable Baselines3 (PPO):** Algoritmo de Inteligência Artificial para treinamento.
* **Gymnasium:** Ambiente de tradução para Reinforcement Learning.
* **SciPy & Seaborn:** Validação estatística e plotagem de dados.
