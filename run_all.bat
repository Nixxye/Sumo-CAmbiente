@echo off
title CAmbiente - Bateria de Testes Automatica
echo ========================================================
echo INICIANDO BATERIA DE TESTES - CAMBIENTE (TOMTOM TRAFFIC)
echo ========================================================

echo.
echo [1/3] Rodando o cenario Baseline (Onda Verde)...
call venv\Scripts\python main.py --scenario baseline --traffic tomtom_peak

echo.
echo [2/3] Rodando o cenario com Inteligencia Artificial (RL)...
call venv\Scripts\python main.py --scenario rl --traffic tomtom_peak

echo.
echo [3/4] Processando dados e gerando os graficos de barras...
call venv\Scripts\python src\evaluation\plot_results.py

echo.
echo [4/4] Pintando os Mapas de Calor de Curitiba...
call venv\Scripts\python src\evaluation\plot_map.py

echo.
echo ========================================================
echo TUDO PRONTO! Verifique a pasta simulations/ para o grafico
echo ========================================================
pause
