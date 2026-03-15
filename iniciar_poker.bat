@echo off
title PokerExcel - Automação Total
cls

echo ======================================================
echo           INICIANDO CICLO POKEREXCEL 1.0
echo ======================================================
echo.

echo [1/3]  Rodando o Bot Hunter...
py src/bot_excel.py
if %errorlevel% neq 0 (
    echo.
    echo  Erro no Bot! Verifique se o Chrome está aberto corretamente.
    pause
    exit
)

echo.
echo [2/3]  Processando dados para o Formato GTO...
py src/processar_dados.py
if %errorlevel% neq 0 (
    echo.
    echo  Erro no Processador! Verifique o arquivo tabela_bruta.json.
    pause
    exit
)

echo.
echo [3/3]  Iniciando servidor e abrindo PokerExcel...
start "PokerExcel Server" py src/main.py
timeout /t 3 /nobreak >nul
start http://127.0.0.1:8000

echo.
echo ======================================================
echo        CONCLUIDO! PODE VOLTAR AO JOGO.
echo ======================================================
pause