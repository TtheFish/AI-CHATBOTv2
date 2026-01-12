# OpenAI API Key Nasıl Set Edilir

## 1. OpenAI API Key Nasıl Alınır?

1. **OpenAI Platform'a gidin:** https://platform.openai.com/api-keys
2. **Login olun** (hesabınız yoksa ücretsiz hesap oluşturun)
3. **"Create new secret key"** butonuna tıklayın
4. **Key'i kopyalayın** - ÖNEMLİ: Bu key sadece bir kez gösterilir, kaydedin!

## 2. Windows'ta API Key Set Etme Yöntemleri

### Yöntem 1: Otomatik Script (Önerilen)

Proje klasöründe bulunan `SET_API_KEY.bat` dosyasını çift tıklayın ve key'inizi girin.

### Yöntem 2: PowerShell ile Kalıcı Set Etme

PowerShell'i **Yönetici olarak çalıştırın** ve şu komutu çalıştırın:

```powershell
[System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "your-api-key-here", "User")
```

**NOT:** `your-api-key-here` yerine gerçek API key'inizi yazın.

### Yöntem 3: Geçici Set Etme (Sadece Mevcut Terminal İçin)

Mevcut PowerShell veya CMD penceresinde:

**PowerShell:**
```powershell
$env:OPENAI_API_KEY="your-api-key-here"
```

**CMD:**
```cmd
set OPENAI_API_KEY=your-api-key-here
```

**NOT:** Bu yöntemle set edilen key sadece o terminal penceresi için geçerlidir. Terminal kapanınca kaybolur.

### Yöntem 4: Windows GUI ile

1. **Windows tuşu + R** basın
2. `sysdm.cpl` yazıp Enter'a basın
3. **"Advanced"** sekmesine tıklayın
4. **"Environment Variables"** butonuna tıklayın
5. **"User variables"** bölümünde **"New"** butonuna tıklayın
6. **Variable name:** `OPENAI_API_KEY`
7. **Variable value:** API key'inizi yapıştırın
8. **OK** butonlarına tıklayarak çıkın

## 3. API Key'in Doğru Set Edildiğini Kontrol Etme

PowerShell'de kontrol edin:

```powershell
$env:OPENAI_API_KEY
```

Eğer key gözüküyorsa başarılı!

## 4. Backend'i Yeniden Başlatma

API key'i set ettikten sonra:

1. **Backend terminal penceresini kapatın** (Ctrl+C)
2. **Yeni bir terminal açın** (veya mevcut terminali yeniden başlatın)
3. Backend'i tekrar başlatın:
   ```bash
   cd backend
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

## 5. Önemli Notlar

- ⚠️ **API key'inizi kimseyle paylaşmayın!**
- ⚠️ **API key'inizi git'e commit etmeyin!** (`.gitignore` dosyası bunu engeller)
- 💰 OpenAI API ücretlidir, kullanımınızı kontrol edin
- 🆓 Yeni hesaplara genellikle ücretsiz kredi verilir ($5 gibi)

## 6. Sorun Giderme

### "API Key set edildi ama çalışmıyor"

1. Terminal'i kapatıp yeniden açın
2. Backend'i yeniden başlatın
3. PowerShell'de kontrol edin: `$env:OPENAI_API_KEY`

### "API Key'i nerede bulabilirim?"

https://platform.openai.com/api-keys adresinden yeni key oluşturabilirsiniz.

### "API Key olmadan çalışır mı?"

Evet, sistem sentence-transformers kullanarak çalışır ama:
- Daha yavaş olabilir
- Daha düşük kalitede cevaplar verebilir
- OpenAI'in gelişmiş özelliklerini kullanamaz

