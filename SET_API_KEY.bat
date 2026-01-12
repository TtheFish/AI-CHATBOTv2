@echo off
echo ============================================
echo OPENAI API KEY SET ETME
echo ============================================
echo.
echo Bu script OPENAI_API_KEY'i kalici olarak set edecek.
echo.
echo ONEMLI: OpenAI API key'inizi almak icin:
echo 1. https://platform.openai.com/api-keys adresine gidin
echo 2. Login olun (hesap yoksa olusturun)
echo 3. "Create new secret key" butonuna tiklayin
echo 4. Olusan key'i kopyalayin (sadece bir kez gosterilir!)
echo.
echo ============================================
set /p API_KEY="API Key'inizi girin: "

if "%API_KEY%"=="" (
    echo Hata: API Key girilmedi!
    pause
    exit /b 1
)

echo.
echo API Key set ediliyor...
setx OPENAI_API_KEY "%API_KEY%"

echo.
echo ============================================
echo Basarili! API Key set edildi.
echo ============================================
echo.
echo NOT: Yeni terminal penceresi acmaniz gerekebilir.
echo Backend'i yeniden baslatmak icin terminal'i kapatip acin.
echo.
pause

