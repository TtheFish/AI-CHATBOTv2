# 🚀 Hızlı Başlangıç: API Key Set Etme

## En Kolay Yöntem: .env Dosyası Kullanma

### Adım 1: API Key'i Alın
1. https://platform.openai.com/api-keys adresine gidin
2. Login olun
3. "Create new secret key" butonuna tıklayın
4. Key'i kopyalayın

### Adım 2: .env Dosyası Oluşturun

**Backend klasöründe** (backend/.env) bir dosya oluşturun:

```
backend/
  ├── .env          ← Bu dosyayı oluşturun
  ├── app/
  └── ...
```

### Adım 3: İçeriğini Yazın

`.env` dosyasının içine şunu yazın:

```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**ÖNEMLİ:** `sk-proj-...` kısmını gerçek API key'inizle değiştirin!

### Adım 4: Backend'i Yeniden Başlatın

Backend'i durdurup yeniden başlatın. Artık çalışacak!

## Alternatif: Batch Dosyası Kullanma

Proje kök klasöründeki `SET_API_KEY.bat` dosyasını çift tıklayın ve key'inizi girin.

## Kontrol

Backend başladıktan sonra chat'e "Hello" yazın. Artık daha iyi cevaplar alacaksınız!

