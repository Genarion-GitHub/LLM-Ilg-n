import json
import os
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any
from groq import AsyncGroq
from deepgram import DeepgramClient
from agents.starting_agent import starting_agent
from agents.interview_agent import interview_agent
from agents.quiz_agent import quiz_agent
from agents.ending_agent import ending_agent

# --- Path Düzeltmesi ---
from dotenv import load_dotenv
base_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(base_dir, '.env')
load_dotenv(dotenv_path=dotenv_path)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    groq_api_key = os.getenv("GROQ_API_KEY")
    deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")

    if not groq_api_key or not deepgram_api_key:
        raise ValueError("API anahtarları .env dosyasında bulunamadı.")

    client = AsyncGroq(api_key=groq_api_key)
    deepgram_client = DeepgramClient(api_key=deepgram_api_key)
    print("✅ Groq ve Deepgram istemcileri başarıyla başlatıldı.")

except Exception as e:
    print(f"❌ HATA: İstemciler başlatılamadı: {e}")
    client = None
    deepgram_client = None
    
class TTSRequest(BaseModel):
    text: str
    
class STTRequest(BaseModel):
    audio: UploadFile = File(...)
    
def load_json_data(filename):
    try:
        data_path = os.path.join(base_dir, 'data', filename)
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ Uyarı: {filename} dosyası bulunamadı.")
        return {}

cv_data = load_json_data('cv.json')
job_ad_data = load_json_data('jobad.json')
qna_data = load_json_data('qna.json')

class ChatRequest(BaseModel):
    sessionId: str
    userMessage: str

sessions: Dict[str, Dict[str, Any]] = {}

def get_session(session_id: str):
    if session_id not in sessions:
        sessions[session_id] = {
            "stage": "starting",
            "full_conversation": []  # TÜM konuşmaları sakla (UI için)
        }
    return sessions[session_id]

@app.get('/api/health')
async def health_check():
    return {"status": "ok", "message": "Backend is running!"}

@app.get('/api/chat/history/{session_id}')
async def get_conversation_history(session_id: str):
    """Frontend'in tüm konuşma geçmişini çekmesi için endpoint"""
    session = sessions.get(session_id)
    if not session:
        return {"conversation_history": []}
    return {"conversation_history": session["full_conversation"]}

@app.post('/api/chat')
async def handle_chat(request: ChatRequest):
    if not client:
        raise HTTPException(status_code=500, detail="Groq client not initialized")

    session = get_session(request.sessionId)
    stage = session["stage"]
    user_message = request.userMessage
    full_conversation = session["full_conversation"]

    print(f"🔵 Chat Request - SessionID: {request.sessionId}, Stage: {stage}, Message: '{user_message}'")

    # Ajanlara gönderilecek string formatındaki konuşma geçmişi
    history_str = "\n".join(
        [f"{'Aday' if msg['sender'] == 'user' else 'Asistan'}: {msg['text']}" for msg in full_conversation]
    )

    try:
        response_text = ""
        action = None

        if stage == "starting":
            # Eğer konuşma yeni başlıyorsa (ilk mesaj boş), agent'ı ilk mesajı üretmesi için tetikle.
            # Bu, frontend'deki fallback (yedek) mesaj sorununu çözer.
            if not user_message:
                print("🚀 Initializing conversation with starting_agent...")
                user_message = "Merhaba, mülakat için hazırım. Başlayabiliriz." # Agent'ı tetikleyecek gizli mesaj

            agent_result = await starting_agent(client, history_str, user_message, cv_data, job_ad_data)
            response_text = agent_result.get("response", "")
            print(f"🟢 Starting Agent Response: {response_text}")
            
            if agent_result.get("is_complete"):
                action = "START_INTERVIEW"
                session["stage"] = "interview"
                print(f"✅ Stage değişti: starting -> interview")

        elif stage == "interview":
            response_text = await interview_agent(client, history_str, user_message, cv_data, job_ad_data)
            print(f"🎤 Interview Agent Response: {response_text}")

            if "INTERVIEW_COMPLETE" in response_text: # interview_agent'dan gelen sinyal
                response_text = response_text.replace("INTERVIEW_COMPLETE", "").strip()
                action = "START_QUIZ"
                session["stage"] = "quiz"
                print(f"✅ Stage değişti: interview -> quiz")

        elif stage == "quiz":
            # Bu blok, quiz tamamlandıktan sonra frontend'den gelen ilk mesajla tetiklenir.
            if user_message == "QUIZ_COMPLETED":
                session["stage"] = "ending"
                print(f"✅ Stage değişti: quiz -> ending")
                # ending_agent'ı ilk mesajıyla başlat
                response_text = await ending_agent(client, history_str, "", qna_data)
                print(f"🟣 Ending Agent (Initial) Response: {response_text}")
            else:
                # Quiz sırasında chat isteği gelirse görmezden gel
                response_text = ""

        elif stage == "ending":
            response_text = await ending_agent(client, history_str, user_message, qna_data)
            print(f"🟣 Ending Agent Response: {response_text}")
            
            if "POST_INTERVIEW_COMPLETE" in response_text:
                response_text = response_text.replace("POST_INTERVIEW_COMPLETE", "").strip()
                action = "FINISH_INTERVIEW"
                if request.sessionId in sessions:
                    del sessions[request.sessionId]
                    print(f"✅ Oturum sonlandırıldı: {request.sessionId}")

        # Konuşma geçmişini her zaman güncelle
        if user_message and user_message not in ["QUIZ_COMPLETED", "Merhaba, mülakat için hazırım. Başlayabiliriz."]:
            session["full_conversation"].append({"sender": "user", "text": user_message})
        if response_text:
            session["full_conversation"].append({"sender": "assistant", "text": response_text})

        result = {
            "response": response_text, 
            "action": action,
            "conversation_history": session["full_conversation"]  # Frontend'e tüm konuşmayı gönder
        }
        print(f"📤 Returning to frontend: {result}")
        return result
        
    except Exception as e:
        print(f"❌ Chat Error (Stage: {stage}): {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ajanla iletişimde hata: {str(e)}")

@app.post('/api/agents/quiz')
async def handle_quiz_agent_route():
    if not client:
        raise HTTPException(status_code=500, detail="Groq client not initialized")
    try:
        questions = await quiz_agent(client, qna_data, job_ad_data)
        return questions
    except Exception as e:
        print(f"❌ Quiz Agent Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to generate quiz")

@app.post("/api/speech-to-text")
async def speech_to_text(audio: UploadFile = File(...)):
    if not deepgram_client:
        raise HTTPException(status_code=500, detail="Deepgram client not initialized")
    try:
        audio_data = await audio.read()
        source = {"buffer": audio_data}
        options = {"model": "nova-2", "smart_format": True, "language": "tr"}
        
        response = deepgram_client.listen.prerecorded.v("1").transcribe_file(source, options)
        transcription = response["results"]["channels"][0]["alternatives"][0]["transcript"]
        
        print(f"🎤 STT Transcription: {transcription}")
        return {"transcription": transcription}
        
    except Exception as e:
        print(f"❌ STT Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ses dönüştürme hatası: {str(e)}")

@app.post("/api/text-to-speech")
async def text_to_speech(request: TTSRequest):    
    if not deepgram_client:
        raise HTTPException(status_code=500, detail="Deepgram client not initialized")
    try:
        options = {"model": "aura-asteria-tr"}
        
        response = deepgram_client.speak.v("1").stream({"text": request.text}, options)
        
        print(f"🔊 TTS Request: {request.text[:50]}...")
        return StreamingResponse(response.stream, media_type="audio/mpeg")

    except Exception as e:
        print(f"❌ TTS Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Metin okuma hatası: {str(e)}")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)