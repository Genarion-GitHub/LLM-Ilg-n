# Video Mülakat Platformu

AI destekli video mülakat ve işe alım platformu. Adayları planlama, sohbet asistanı, kişilik değerlendirmesi ve soru-cevap süreçlerinden geçirir.

## Özellikler

- **Mülakat Planlaması**: Hemen başlama veya randevu alma seçenekleri
- **Ön Mülakat Sohbeti**: AI asistan ile ısınma konuşması (Starting Agent)
- **Video Mülakat**: Simüle edilmiş video görüşme (Interview Agent)
- **Kişilik Değerlendirmesi**: Big Five kişilik testine dayalı 10 soruluk quiz (Quiz Agent)
- **Soru-Cevap**: Mülakat sonrası interaktif Q&A (Ending Agent)
- **Groq API Entegrasyonu**: Güçlü AI model desteği
- **Otomatik Transkript**: Tüm konuşmaların kaydedilmesi
- **Çoklu Şirket Desteği**: GENAR klasör yapısı ile birden fazla şirket ve pozisyon yönetimi

## Teknolojiler

### Frontend
- React 19.2.0
- TypeScript 5.8.2
- Vite 6.2.0
- UUID (session yönetimi)

### Backend
- Python 3.8+
- FastAPI (REST API)
- Uvicorn (ASGI server)
- Groq API (AI model entegrasyonu)
- Pydantic (veri validasyonu)
- Python-dotenv (ortam değişkenleri)

### AI Model
- openai/gpt-oss-120b (Groq üzerinden)

### Veri Yapısı
- JSON tabanlı CV, İş İlanı ve Q&A verileri
- Şirket profilleri ve pozisyon bazlı organizasyon
- UUID ile race condition korumalı aday ID'leri

### Mimari
- **Mikroservis Mimarisi**: 4 bağımsız agent (Starting, Interview, Quiz, Ending)
- **Interface Segregation**: FileReader (okuma), FileWriter (yazma), FileManagerOps (yönetim)
- **Session-based State Management**: Her aday için ayrı session
- **Agent Özerkliği**: Her agent kendi verisini FileManager ile çeker
- **Async/Await**: Performans optimizasyonu

## Kurulum

**Gereksinimler:** Python 3.8+

1. **Frontend Kurulumu:**
   ```bash
   npm install
   ```

2. **Backend Kurulumu (Python venv ile):**
   ```bash
   cd backend/api
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Ortam Değişkenleri:**
   `backend/api/.env` dosyası oluşturun:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

## Çalıştırma

**2 terminal açın:**

**Terminal 1 - Backend:**
```bash
cd backend/api
venv\Scripts\activate
python app.py
```
Backend: http://localhost:5001

**Terminal 2 - Frontend:**
```bash
npm run dev
```

## Erişim Adresleri

### Genel Erişim
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5001
- **Kişisel Host (Frontend)**: http://192.168.1.103:3000
- **Kişisel Host (Backend)**: http://192.168.1.103:5001

### Örnek Mülakat URL'leri (Session ID Bazlı)
- **Melis Kaya (Dijital Pazarlama)**: http://localhost:3000?sessionId=Genar-00001-00001
- **Ahmet Yılmaz (Yazılım Geliştirici)**: http://localhost:3000?sessionId=Genar-00002-00001

**Not:** Yeni adaylar için UUID ile otomatik ID oluşturulur (örn: Genar-00001-a1b2c3d4)

## Mülakat Akışı

1. **Scheduling** - Mülakat zamanlaması (hemen başla veya randevu al)
2. **Waiting Room** - Randevu zamanı gelene kadar bekleme (5 dk kala quiz hazırlanır)
3. **Chatbot** - Starting Agent ile ısınma sohbeti (2-4 soru)
4. **Interview** - Interview Agent ile video mülakat (teknik sorun nedeniyle atlanır)
5. **Quiz** - Quiz Agent tarafından oluşturulan 10 soruluk kişilik testi
6. **QnA** - Ending Agent ile adayın sorularını yanıtlama
7. **Completion** - Sonuçlar ve transkript kaydı
