# CAmbiente: Otimização Semafórica com Inteligência Artificial

Este projeto simula o trânsito da região central de Curitiba utilizando dados reais de satélite (TomTom) e emprega técnicas avançadas de **Aprendizado por Reforço (Reinforcement Learning)** para otimizar os semáforos em tempo real, reduzindo gargalos e melhorando o fluxo veicular.

---

## 🛠️ Passo a Passo: Como rodar em outra máquina

Para executar este projeto em um novo computador (seja para apresentação ou desenvolvimento), siga rigorosamente os passos abaixo.

### 1. Pré-requisitos do Sistema (Instalando o SUMO no Windows)
Antes de rodar o código em Python, você precisa instalar o simulador físico de trânsito (Eclipse SUMO) e informar ao seu computador onde ele está instalado. **Siga este passo a passo com muita atenção, pois é onde a maioria dos erros acontece.**

#### A) Instalando o Simulador
1. Acesse o site oficial: [sumo.dlr.de/docs/Downloads.php](https://sumo.dlr.de/docs/Downloads.php).
2. Procure pela seção **Windows** e baixe o instalador (geralmente nomeado como `sumo-win64-1.xx.x.msi`).
3. Execute o instalador baixado. Pode ir clicando em "Next" deixando as configurações padrão. Anote o caminho onde ele será instalado (geralmente `C:\Program Files (x86)\Eclipse\Sumo`).

#### B) Configurando as Variáveis de Ambiente (Obrigatório)
O nosso código em Python precisa saber onde o simulador está para conseguir controlá-lo (via TraCI). Para isso, criamos uma "Variável de Ambiente":
1. No seu Windows, abra o Menu Iniciar, digite **"Editar as variáveis de ambiente do sistema"** e aperte Enter.
2. Na janela que se abriu (Propriedades do Sistema), clique na aba "Avançado" e depois no botão **"Variáveis de Ambiente..."** (fica no canto inferior direito).
3. Na metade de baixo dessa nova tela (na caixinha chamada "Variáveis do sistema"), clique no botão **"Novo..."**.
4. Em *Nome da variável*, digite exatamente e em letras maiúsculas: `SUMO_HOME`
5. Em *Valor da variável*, cole o caminho da pasta onde o SUMO foi instalado (exemplo: `C:\Program Files (x86)\Eclipse\Sumo`). Clique em OK.

#### C) Adicionando o SUMO ao "Path" do Sistema
Isso permite que você rode comandos do simulador em qualquer lugar do seu computador.
1. Ainda na tela de "Variáveis de Ambiente", na caixinha de baixo ("Variáveis do sistema"), procure por uma variável chamada **`Path`** ou **`PATH`**.
2. Selecione ela e clique no botão **"Editar..."**.
3. Clique no botão **"Novo"** no lado direito.
4. Digite o caminho da pasta `bin` que fica dentro do seu SUMO. Geralmente é: `%SUMO_HOME%\bin` ou `C:\Program Files (x86)\Eclipse\Sumo\bin`
5. Dê OK em todas as três janelas abertas para salvar. 
**Importante:** Se você estiver com algum terminal aberto (como o do VSCode ou o CMD), feche-o e abra novamente para que o seu computador carregue as novas configurações!

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
