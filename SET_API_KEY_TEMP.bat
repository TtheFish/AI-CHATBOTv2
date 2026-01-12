@echo off
echo ============================================
echo OPENAI API KEY GECICI SET ETME
echo ============================================
echo.
echo Bu script OPENAI_API_KEY'i sadece bu terminal icin set eder.
echo Backend'i bu terminal'de baslatirsaniz calisir.
echo.
set /p API_KEY="API Key'inizi girin: "

if "%API_KEY%"=="" (
    echo Hata: API Key girilmedi!
    pause
    exit /b 1
)

set OPENAI_API_KEY=%API_KEY%
echo.
echo API Key bu terminal icin set edildi: %OPENAI_API_KEY:~0,10%...
echo Backend'i bu terminal'de baslatabilirsiniz.
echo.
pause

