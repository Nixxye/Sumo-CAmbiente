# Roteiro de Apresentação: CAmbiente - Otimização Semafórica

> [!TIP]
> **Dica para os apresentadores:** Façam a transição entre as falas de forma natural. O roteiro abaixo sugere uma divisão lógica, mas sintam-se à vontade para adaptar ao estilo de vocês. Lembrem-se de falar com entusiasmo, pausar para dar peso aos números e apontar para os gráficos nas telas quando estiverem explicando os visuais.

---

## Slide 1: Capa (Título e Equipe)
**Apresentador 1:**
"Bom dia a todos. Nós somos a equipe composta pelo Felipe Costa, Felipe Domingos, Jean Carlos, Vitor Isaias e Yago Menin. Hoje viemos apresentar o nosso projeto da disciplina de Ciências de Ambiente, que busca resolver um dos problemas mais invisíveis, porém mais danosos da vida urbana: o congestionamento de trânsito e o seu impacto direto na poluição atmosférica."

"Nosso projeto foca no Quadrilátero Central de Curitiba. Em vez de simplesmente propormos a construção de novas vias, nós decidimos aplicar a Inteligência Artificial — especificamente o Aprendizado por Reforço — para criar uma intervenção inteligente e otimizar os semáforos existentes."

---

## Slide 2 e 3: Arquitetura e Integração Interdisciplinar
**Apresentador 2:**
"Para construir essa solução, nós não ficamos restritos apenas ao código. Este é um esforço multidisciplinar."

*(Passar o slide)*

"Nossa stack tecnológica e arquitetura refletem isso perfeitamente:
1. Da **Engenharia de Computação**, nós trouxemos o algoritmo PPO rodando sobre o *Gymnasium*.
2. Da **Engenharia Elétrica e Automação**, nós modelamos a infraestrutura de sensores simulados via *TraCI* (Traffic Control Interface), que nos permite coletar dados e atuar nos semáforos em tempo real.
3. Da **Engenharia Mecânica e Ambiental**, nós avaliamos a eficiência dos motores. Carros parados ou no ciclo infinito de 'para-e-anda' queimam combustível à toa. 
4. E para orquestrar tudo isso de forma realista, usamos o simulador microscópico de tráfego *Eclipse SUMO*, validando tudo matematicamente com *SciPy* e *Matplotlib*."

---

## Slide 4 e 5: Dados e Realismo
**Apresentador 3:**
"Um dos maiores problemas de trabalhos acadêmicos de tráfego é usar dados aleatórios, o que gera resultados que não se sustentam na prática. Nós queríamos resolver um problema **real**."

*(Passar o slide)*

"Por isso, extraímos relatórios oficiais de lentidão da **TomTom** de agosto de 2024, englobando as artérias críticas de Curitiba: Mariano Torres, Calçadão da XV, Marechal Floriano e Presidente Kennedy. Com base nisso, fizemos uma Engenharia de Pesos: convertemos esses índices reais de congestionamento em probabilidade de inserção de veículos no nosso simulador. Assim, nós forçamos o nosso algoritmo a lidar com o caos de um horário de pico autêntico do centro de Curitiba."

---

## Slide 6: Metodologia (Do Ciclo Fixo ao Algoritmo Adaptativo)
**Apresentador 1:**
"Mas como nós resolvemos o problema? Precisamos entender como a cidade funciona hoje e como propomos mudar."

"A nossa linha de base (o *Baseline*) é a famosa **Onda Verde**. Ela funciona por **Ciclos Rígidos** (por exemplo, 40 segundos aberto e 20 segundos fechado). O problema da Onda Verde é que ela é **míope** e **estática**. Se houver um acidente, ou se for madrugada e a rua estiver vazia, ela vai continuar fechando o cruzamento e forçando os motoristas a pararem."

"A nossa solução é o **Aprendizado por Reforço**. Diferente de um sistema programado por regras, esse é um Agente que aprende interagindo com o ambiente por 'tentativa e erro'. O algoritmo observa o comprimento das filas através dos sensores, analisa o momento atual e decide ativamente: *'devo manter o semáforo verde ou trocá-lo agora?'*. Se a decisão que ele tomou reduziu a fila, ele recebe uma **Recompensa Matemática**. Se ele piorou o trânsito, ele é punido. Ao longo de milhares de simulações, o algoritmo descobre a política perfeita: abrir as vias estritamente sob demanda."

---

## Slide 7: A Prova Científica (Impacto)
**Apresentador 2:**
"E o resultado prático disso não foi apenas uma pequena melhora, foi uma mudança de paradigma."

*(Apontar para os números no slide)*

"Nós reduzimos o tempo médio parado de cada motorista de impressionantes **519 segundos** (quase 9 minutos perdidos em filas) para apenas **265 segundos**. Isso representa um corte de aproximadamente 49% do tempo de espera, de forma geral. Além disso, caímos a média de paradas forçadas de 11 para 8 vezes por viagem."

"E para a banca avaliadora, nós não confiamos apenas no acaso. Aplicamos o rigoroso teste estatístico não-paramétrico de Mann-Whitney U, que nos retornou um **p-value de 1.14 elevado a -13** (praticamente zero). Cientificamente, isso comprova que essa melhoria brutal é mérito exclusivo da intervenção do algoritmo, e não variação aleatória de dados."

---

## Slides 8 e 9: Distribuição de Dados e Análise de Outliers
**Apresentador 3:**
"Olhando agora para os gráficos de violino, nós conseguimos ver *como* essa melhora aconteceu. Esses gráficos mostram a 'silhueta' de onde a maior parte dos motoristas se concentra."

"Reparem na figura da esquerda (Onda Verde): percebam como ela possui uma cauda fina e muito longa, esticando-se lá para cima. Esses são os **outliers** — os motoristas extremamente azarados que pegaram um sincronismo ruim da Onda Verde e chegaram a ficar até 8 mil, 9 mil segundos parados em loops infinitos de congestionamento."

"Ao mudarmos para o Aprendizado por Reforço, na figura da direita, aquela 'cauda longa do azar' simplesmente desaparece. O algoritmo achatou e encolheu a distribuição dos tempos, garantindo que o tempo de trânsito se tornasse **consistente, compacto e justo** para quase todo mundo no sistema."

---

## Slides 10 e 11: Eficiência do Roteamento (Dispersão)
**Apresentador 1:**
"O gráfico de Dispersão *(Scatter Plot)* nos ajuda a derrubar um mito do trânsito. No eixo X temos a distância da viagem e, no Y, o tempo parado. No sistema normal (pontos vermelhos), nós vemos que os carros mais parados não eram necessariamente os que viajavam as maiores distâncias. O trânsito era caótico e o tempo parado era imprevisível."

"Com o nosso algoritmo (pontos verdes), nós colapsamos essa nuvem para o chão do gráfico. Independentemente se a pessoa dirige 2 km ou 8 km, o tempo máximo em que ela fica parada em semáforos forma um limite rígido. Nós devolvemos a previsibilidade para o motorista."

---

## Slides 12 a 15: Análise Estatística (CDF e Comparativos)
**Apresentador 2:**
*(No gráfico CDF - Slide 13)*
"A maneira mais didática de ler esse gráfico CDF (Função de Distribuição Acumulada) é reparar como a linha azul do Algoritmo sobe muito rápido e bate no teto logo no início. Isso significa que quase 100% dos nossos motoristas concluem suas viagens sofrendo pouco atraso. A linha vermelha da Onda Verde, por outro lado, sobe devagar, mostrando que uma parcela significativa da população sofre tempos astronômicos de lentidão."

*(No mosaico de gráficos de barra - Slide 15)*
"Nesse painel, os 4 pilares de um bom trânsito foram vencidos pelo Reforço. Quedas expressivas em: Tempo Parado, Tempo Perdido (Lentidão), Paradas Bruscas (que deterioram freios e motor), e consequentemente, Duração da Viagem inteira."

---

## Slide 16: Melhoria Ambiental e Consumo
**Apresentador 3:**
"Mas este é um projeto de Ciências de Ambiente. E toda essa otimização semafórica não foi feita apenas para as pessoas chegarem mais cedo em casa, mas para a cidade **respirar melhor**."

"Nós usamos o motor físico interno do SUMO para contabilizar a emissão exata baseada na curva de aceleração de cada carro. O ciclo de ficar em marcha lenta com o motor ligado no farol vermelho, seguido de uma arrancada forte quando abre, é o pico da emissão veicular."

"As barras falam por si só: o Aprendizado por Reforço derrubou a emissão de Dióxido de Carbono (CO2) e Consumo de Combustível fóssil em **24%**, e as emissões de Óxidos de Nitrogênio (NOx), que são altamente tóxicos para o sistema respiratório, em mais de **25%**. Ao organizarmos a matemática do tráfego, mitigamos drasticamente a Pegada de Carbono do centro urbano."

---

## Slide 17: Conclusão
**Apresentador 1:**
"Para concluir, a mensagem central do nosso trabalho é **'O Fim do Azar no Trânsito'**. O método do Aprendizado por Reforço ceifou a injustiça semafórica que prendia as pessoas por desalinhamento. 

E, finalmente, uma das reflexões mais importantes que trazemos nesta disciplina: A engenharia não serve apenas para construir máquinas complexas ou algoritmos geniais de IA. Ela serve, fundamentalmente, para desenhar cidades onde as pessoas possam viver com qualidade, chegar mais cedo em casa para as suas famílias e respirar um ar muito mais limpo.

Muito obrigado!"
