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

# .env'den veri yollarını al
DATA_PATH = os.getenv("DATA_PATH", "../../GENAR")
COMPANY_ID = os.getenv("COMPANY_ID", "GENAR")
JOB_ID = os.getenv("DEFAULT_JOB_ID", "Genar-00001")

file_manager = FileManager(base_dir=DATA_PATH)

def load_json_data(filename: str, job_id: str, candidate_id: str):
    """
    Dosya okumak için HEM job_id HEM de candidate_id gerekir.
    """
    if filename == 'jobad.json':
        return file_manager.reader.get_job_ad_data(job_id)
    elif filename == 'qna.json':
        return file_manager.reader.get_qna_data(job_id)
    elif filename == 'cv.json':
        return file_manager.reader.get_cv_data(candidate_id)
    return {}

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

@app.get('/api/debug/{session_id}')
async def debug_session(session_id: str):
    """Session bilgilerini debug et"""
    session = get_session(session_id)
    
    # Dosya yollarını debug et
    job_path = f"{DATA_PATH}/{session.get('job_id')}/JobAd.json"
    cv_path = f"{DATA_PATH}/{session.get('job_id')}/{session.get('candidate_id')}/cv_extraction.json"
    
    candidate_cv = load_json_data('cv.json', session.get('job_id'), session.get('candidate_id'))
    job_data = load_json_data('jobad.json', session.get('job_id'), session.get('candidate_id'))
    
    return {
        "session_id": session_id,
        "parsed_job_id": session.get('job_id'),
        "parsed_candidate_id": session.get('candidate_id'),
        "job_path_looking_for": job_path,
        "cv_path_looking_for": cv_path,
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
        qna_data = file_manager.reader.get_qna_data(session.get('job_id'))
        response_text = await ending_agent(client, starting_history_str, "", qna_data)
        if response_text:
            session["ending_conversation"].append({"sender": "assistant", "text": response_text})
    elif stage == "starting":
        job_id = session["job_id"]
        candidate_id = session["candidate_id"]
        candidate_cv = load_json_data('cv.json', job_id, candidate_id)
        job_data = load_json_data('jobad.json', job_id, candidate_id)
        agent_result = await starting_agent(client, history_str, user_message, candidate_cv, job_data)
        response_text = agent_result.get("response", "")
        if agent_result.get("is_complete"):
            action = "START_INTERVIEW"
            session["stage"] = "interview"
    elif stage == "interview":
        job_id = session["job_id"]
        candidate_id = session["candidate_id"]
        candidate_cv = load_json_data('cv.json', job_id, candidate_id)
        job_data = load_json_data('jobad.json', job_id, candidate_id)
        response_text = await interview_agent(client, history_str, user_message, candidate_cv, job_data)
        if "INTERVIEW_COMPLETE" in response_text:
            response_text = response_text.replace("INTERVIEW_COMPLETE", "").strip()
            action = "START_QUIZ"
            session["stage"] = "quiz"
    elif stage == "ending":
        combined_history = session["starting_conversation"] + session["ending_conversation"]
        ending_history_str = "\n".join([f"{'Aday' if msg['sender']=='user' else 'Asistan'}: {msg['text']}" for msg in combined_history])
        qna_data = file_manager.reader.get_qna_data(session.get('job_id'))
        response_text = await ending_agent(client, ending_history_str, user_message, qna_data)
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
    
    file_manager.writer.save_candidate_data("", job_id, candidate_id, "interview_transcript", transcript_data)
    
    del sessions[request.sessionId]
    return {"status": "success"}

@app.post('/api/agents/quiz')
async def handle_quiz_agent_route():
    quiz_data = file_manager.get_job_data("", JOB_ID, "Quiz")
    if not quiz_data:
        qna_data = file_manager.reader.get_qna_data(JOB_ID)
        job_data = file_manager.reader.get_job_ad_data(JOB_ID)
        quiz_data = await quiz_agent(client, qna_data, job_data)
        
        # Oluşturulan quiz'i ilan klasörüne kaydet
        file_manager.writer.save_job_data("", JOB_ID, "Quiz", quiz_data)
        
        return quiz_data
    else:
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
            
            file_manager.writer.save_candidate_data("", job_id, candidate_id, "quiz_results", quiz_data)
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)