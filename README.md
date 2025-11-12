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

## Teknolojiler

- **Frontend**: React + TypeScript + Tailwind CSS + Vite
- **Backend**: Python + FastAPI + Groq API
- **AI Model**: openai/gpt-oss-120b (Groq)
- **Veri**: JSON tabanlı CV, İş İlanı ve Q&A verileri

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
Frontend: http://localhost:5173

## Mülakat Akışı

1. **Scheduling** - Mülakat zamanlaması (hemen başla veya randevu al)
2. **Waiting Room** - Randevu zamanı gelene kadar bekleme (5 dk kala quiz hazırlanır)
3. **Chatbot** - Starting Agent ile ısınma sohbeti (2-4 soru)
4. **Interview** - Interview Agent ile video mülakat (teknik sorun nedeniyle atlanır)
5. **Quiz** - Quiz Agent tarafından oluşturulan 10 soruluk kişilik testi
6. **QnA** - Ending Agent ile adayın sorularını yanıtlama
7. **Completion** - Sonuçlar ve transkript kaydı
