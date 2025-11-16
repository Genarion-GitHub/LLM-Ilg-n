import json
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
from groq import AsyncGroq
from dotenv import load_dotenv
from agents.starting_agent import starting_agent
from agents.interview_agent import interview_agent
from agents.quiz_agent import quiz_agent
from agents.ending_agent import ending_agent
from utils.file_manager import FileManager

base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(base_dir, '.env'))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY bulunamadı")

client = AsyncGroq(api_key=groq_api_key)

DATA_PATH = os.getenv("DATA_PATH", "../../GENAR")
file_manager = FileManager(base_dir=DATA_PATH)

class ChatRequest(BaseModel):
    sessionId: str
    userMessage: str

sessions: Dict[str, Dict[str, Any]] = {}

def get_session(session_id: str):
    """
    Session ID'nin kendisi candidate_id'dir.
    Bu ID'den job_id'yi çıkarırız.
    """
    if session_id not in sessions:
        candidate_id = session_id  # örn: "Genar-00001-00001"
        
        # Aday ID'sinden Job ID'yi çıkar
        parts = candidate_id.split("-")
        if len(parts) < 3:
            print(f"HATA: Geçersiz session_id formatı: {session_id}")
            job_id = "Genar-00001"
            candidate_id = "Genar-00001-00001"
        else:
            job_id = f"{parts[0]}-{parts[1]}"  # örn: "Genar-00001"
        
        sessions[session_id] = {
            "stage": "starting",
            "job_id": job_id,
            "candidate_id": candidate_id,
            "full_conversation": [],
            "starting_conversation": [],
            "ending_conversation": []
        }
    return sessions[session_id]

@app.get('/api/health')
async def health_check():
    return {"status": "ok"}

@app.delete('/api/session/{session_id}')
async def clear_session(session_id: str):
    """Session'ı temizle"""
    if session_id in sessions:
        del sessions[session_id]
        return {"status": "success", "message": f"Session {session_id} cleared"}
    return {"status": "not_found", "message": f"Session {session_id} not found"}

@app.get('/api/debug/{session_id}')
async def debug_session(session_id: str):
    """Session bilgilerini debug et"""
    session = get_session(session_id)
    job_id = session.get('job_id')
    candidate_id = session.get('candidate_id')
    
    candidate_cv = file_manager.reader.get_cv_data(candidate_id)
    job_data = file_manager.reader.get_job_ad_data(job_id)
    
    return {
        "session_id": session_id,
        "parsed_job_id": job_id,
        "parsed_candidate_id": candidate_id,
        "cv_found": bool(candidate_cv),
        "cv_name": candidate_cv.get('name', 'CV bulunamadı'),
        "job_found": bool(job_data),
        "job_position": job_data.get('position', 'İş ilanı bulunamadı'),
        "stage": session.get('stage')
    }

@app.post('/api/chat')
async def handle_chat(request: ChatRequest):
    session = get_session(request.sessionId)
    stage = session["stage"]
    user_message = request.userMessage

    if not user_message:
        conversation_to_send = session["starting_conversation"] + session["ending_conversation"] if stage == "ending" else session["full_conversation"]
        return {"response": "", "action": None, "conversation_history": conversation_to_send}

    history_str = "\n".join([f"{'Aday' if msg['sender']=='user' else 'Asistan'}: {msg['text']}" for msg in session["full_conversation"]])
    response_text = ""
    action = None

    if user_message == "INTERVIEW_STARTED":
        session["stage"] = "interview"
        response_text = "Teknik nedenlerle video mülakatı atlanıyor. Şimdi kişilik değerlendirmesi bölümüne geçiyoruz."
        action = "START_QUIZ"
        session["stage"] = "quiz"
        return {"response": response_text, "action": action, "conversation_history": session["full_conversation"]}
    elif user_message == "QUIZ_COMPLETED":
        session["stage"] = "ending"
        starting_history_str = "\n".join([f"{'Aday' if msg['sender']=='user' else 'Asistan'}: {msg['text']}" for msg in session["starting_conversation"]])
        candidate_id = session["candidate_id"]
        response_text = await ending_agent(client, starting_history_str, "", candidate_id)
        if response_text:
            session["ending_conversation"].append({"sender": "assistant", "text": response_text})
    elif stage == "starting":
        candidate_id = session["candidate_id"]
        agent_result = await starting_agent(client, history_str, user_message, candidate_id)
        response_text = agent_result.get("response", "")
        if agent_result.get("is_complete"):
            action = "START_INTERVIEW"
            session["stage"] = "interview"
    elif stage == "interview":
        candidate_id = session["candidate_id"]
        response_text = await interview_agent(client, history_str, user_message, candidate_id)
        if "INTERVIEW_COMPLETE" in response_text:
            response_text = response_text.replace("INTERVIEW_COMPLETE", "").strip()
            action = "START_QUIZ"
            session["stage"] = "quiz"
    elif stage == "ending":
        combined_history = session["starting_conversation"] + session["ending_conversation"]
        ending_history_str = "\n".join([f"{'Aday' if msg['sender']=='user' else 'Asistan'}: {msg['text']}" for msg in combined_history])
        candidate_id = session["candidate_id"]
        response_text = await ending_agent(client, ending_history_str, user_message, candidate_id)
        if "POST_INTERVIEW_COMPLETE" in response_text:
            response_text = response_text.replace("POST_INTERVIEW_COMPLETE", "").strip()
            action = "FINISH_INTERVIEW"

    if user_message not in ["QUIZ_COMPLETED", "INTERVIEW_STARTED"]:
        if stage == "starting":
            session["starting_conversation"].append({"sender": "user", "text": user_message})
        elif stage == "ending":
            session["ending_conversation"].append({"sender": "user", "text": user_message})
        session["full_conversation"].append({"sender": "user", "text": user_message})

    if response_text and user_message not in ["QUIZ_COMPLETED", "INTERVIEW_STARTED"]:
        if stage == "starting":
            session["starting_conversation"].append({"sender": "assistant", "text": response_text})
        elif stage == "ending":
            session["ending_conversation"].append({"sender": "assistant", "text": response_text})
        session["full_conversation"].append({"sender": "assistant", "text": response_text})

    conversation_to_send = session["starting_conversation"] + session["ending_conversation"] if stage == "ending" or user_message == "QUIZ_COMPLETED" else session["full_conversation"]
    return {"response": response_text, "action": action, "conversation_history": conversation_to_send}

@app.post('/api/save-transcript')
async def save_transcript(request: ChatRequest):
    session = sessions.get(request.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    candidate_id = session.get('candidate_id')
    job_id = session.get('job_id')
    
    transcript_data = {
        "session_id": request.sessionId,
        "timestamp": datetime.now().isoformat(),
        "starting_conversation": session.get("starting_conversation", []),
        "ending_conversation": session.get("ending_conversation", []),
        "full_conversation": session.get("full_conversation", [])
    }
    
    file_manager.writer.save_candidate_data(job_id, candidate_id, "interview_transcript", transcript_data)
    
    del sessions[request.sessionId]
    return {"status": "success"}

@app.post('/api/agents/quiz')
async def handle_quiz_agent_route(request: ChatRequest):
    session = get_session(request.sessionId)
    job_id = session.get('job_id')
    
    print(f"🔍 Quiz istendi - SessionId: {request.sessionId}, JobId: {job_id}")
    
    # Her seferinde yeni quiz oluştur (cache'i kaldır)
    qna_data = file_manager.reader.get_qna_data(job_id)
    job_data = file_manager.reader.get_job_ad_data(job_id)
    
    print(f"💼 İş ilanı: {job_data.get('position', 'Bilinmiyor')}")
    print(f"📝 Q&A veri sayısı: {len(qna_data) if isinstance(qna_data, list) else 'Dict'}")
    
    quiz_data = await quiz_agent(client, qna_data, job_data)
    
    print(f"✅ Quiz oluşturuldu - İlk soru: {quiz_data[0].get('question', 'Soru yok') if quiz_data else 'Quiz boş'}")
    
    return quiz_data

class QuizResultsRequest(BaseModel):
    sessionId: str
    score: int
    totalQuestions: int
    results: list

@app.post('/api/save-quiz-results')
async def save_quiz_results(request: QuizResultsRequest):
    try:
        session = sessions.get(request.sessionId)
        if session:
            candidate_id = session.get('candidate_id')
            job_id = session.get('job_id')
            
            quiz_data = {
                "session_id": request.sessionId,
                "timestamp": datetime.now().isoformat(),
                "score": request.score,
                "total_questions": request.totalQuestions,
                "percentage": round((request.score / request.totalQuestions) * 100, 2),
                "results": request.results
            }
            
            file_manager.writer.save_candidate_data(job_id, candidate_id, "quiz_results", quiz_data)
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)