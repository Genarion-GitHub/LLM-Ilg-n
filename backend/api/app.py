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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY bulunamadı")

client = AsyncGroq(api_key=groq_api_key)
file_manager = FileManager(base_dir="data")

# Sabit değerler
COMPANY_ID = "GENAR"
JOB_ID = "Genar-00001"

def load_json_data(filename, candidate_id=None):
    # Dinamik FileManager kullan
    if filename == 'jobad.json':
        return file_manager.get_job_data(COMPANY_ID, JOB_ID, "JobAd")
    elif filename == 'qna.json':
        return file_manager.get_job_data(COMPANY_ID, JOB_ID, "Q&A")
    elif filename == 'cv.json' and candidate_id:
        # Belirli adayın verilerini al
        return file_manager.get_candidate_data(COMPANY_ID, JOB_ID, candidate_id, "cv_extraction") or {}
    else:
        try:
            with open(os.path.join(base_dir, 'data', filename), 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

# Global veriler - session bazlı yüklenecek
job_ad_data = load_json_data('jobad.json')
qna_data = load_json_data('qna.json')

class ChatRequest(BaseModel):
    sessionId: str
    userMessage: str

sessions: Dict[str, Dict[str, Any]] = {}

def get_session(session_id: str):
    if session_id not in sessions:
        stage = "ending" if "ending" in session_id or "post-quiz" in session_id else "interview" if "interview" in session_id else "starting"
        # Session ID'den candidate ID'yi çıkar (format: sessionId-candidateId)
        candidate_id = f"{JOB_ID}-00001"  # Varsayılan
        if "-" in session_id:
            parts = session_id.split("-")
            if len(parts) >= 3:
                candidate_id = f"{JOB_ID}-{parts[-1].zfill(5)}"
        
        sessions[session_id] = {
            "stage": stage,
            "candidate_id": candidate_id,
            "full_conversation": [],
            "starting_conversation": [],
            "ending_conversation": []
        }
    return sessions[session_id]

@app.get('/api/health')
async def health_check():
    return {"status": "ok"}

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
        # Dinamik CV verisi yükle
        candidate_cv = load_json_data('cv.json', session.get('candidate_id'))
        response_text = await interview_agent(client, "", "Video başladı", candidate_cv, job_ad_data)
        print(f"🔍 Interview Agent Decision: '{response_text}'")
        
        if "INTERVIEW_COMPLETE" in response_text:
            print("✅ Interview Agent decided to start quiz")
            response_text = response_text.replace("INTERVIEW_COMPLETE", "").strip()
            quiz_data = await quiz_agent(client, qna_data, job_ad_data)
            action = "SHOW_QUIZ"
            session["stage"] = "quiz"
            return {
                "response": response_text, 
                "action": action, 
                "quiz_data": quiz_data,
                "conversation_history": session["full_conversation"]
            }
        else:
            print("❌ Interview Agent did not decide to start quiz")
            return {"response": response_text, "action": None, "conversation_history": session["full_conversation"]}
    elif user_message == "QUIZ_COMPLETED":
        session["stage"] = "ending"
        response_text = await ending_agent(client, "", "", qna_data)
        if response_text:
            session["ending_conversation"].append({"sender": "assistant", "text": response_text})
    elif stage == "starting":
        # Dinamik CV verisi yükle
        candidate_cv = load_json_data('cv.json', session.get('candidate_id'))
        agent_result = await starting_agent(client, history_str, user_message, candidate_cv, job_ad_data)
        response_text = agent_result.get("response", "")
        if agent_result.get("is_complete"):
            action = "START_INTERVIEW"
            session["stage"] = "interview"
    elif stage == "interview":
        # Dinamik CV verisi yükle
        candidate_cv = load_json_data('cv.json', session.get('candidate_id'))
        response_text = await interview_agent(client, history_str, user_message, candidate_cv, job_ad_data)
        print(f"🔍 Interview Agent Response: {response_text}")
        if "INTERVIEW_COMPLETE" in response_text:
            print("✅ INTERVIEW_COMPLETE detected, starting quiz")
            response_text = response_text.replace("INTERVIEW_COMPLETE", "").strip()
            action = "START_QUIZ"
            session["stage"] = "quiz"
        else:
            print("❌ INTERVIEW_COMPLETE not found in response")
    elif stage == "ending":
        ending_history_str = "\n".join([f"{'Aday' if msg['sender']=='user' else 'Asistan'}: {msg['text']}" for msg in session["ending_conversation"]])
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
    
    transcript_path = os.path.join(base_dir, 'data', 'transcripts', f'{request.sessionId}.json')
    os.makedirs(os.path.dirname(transcript_path), exist_ok=True)
    
    with open(transcript_path, 'w', encoding='utf-8') as f:
        json.dump({
            "session_id": request.sessionId,
            "timestamp": datetime.now().isoformat(),
            "starting_conversation": session.get("starting_conversation", []),
            "ending_conversation": session.get("ending_conversation", []),
            "full_conversation": session.get("full_conversation", [])
        }, f, ensure_ascii=False, indent=2)
    
    del sessions[request.sessionId]
    return {"status": "success"}

@app.post('/api/agents/quiz')
async def handle_quiz_agent_route():
    # Yeni yapıdan veri al
    qna_data = file_manager.get_job_data(COMPANY_ID, JOB_ID, "Q&A")
    job_data = file_manager.get_job_data(COMPANY_ID, JOB_ID, "JobAd")
    
    quiz_data = await quiz_agent(client, qna_data, job_data)
    print(f"🧠 Quiz data generated: {len(quiz_data.get('questions', []))} questions")
    return quiz_data

class QuizResultsRequest(BaseModel):
    sessionId: str
    score: int
    totalQuestions: int
    results: list

class CandidateApplicationRequest(BaseModel):
    job_id: str
    candidate_data: dict

@app.post('/api/save-quiz-results')
async def save_quiz_results(request: QuizResultsRequest):
    try:
        quiz_results_path = os.path.join(base_dir, 'data', 'quiz_results', f'{request.sessionId}.json')
        os.makedirs(os.path.dirname(quiz_results_path), exist_ok=True)
        
        with open(quiz_results_path, 'w', encoding='utf-8') as f:
            json.dump({
                "session_id": request.sessionId,
                "timestamp": datetime.now().isoformat(),
                "score": request.score,
                "total_questions": request.totalQuestions,
                "percentage": round((request.score / request.totalQuestions) * 100, 2),
                "results": request.results
            }, f, ensure_ascii=False, indent=2)
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/candidate/apply')
async def candidate_apply(request: CandidateApplicationRequest):
    """Aday başvuru endpoint'i - otomatik klasör oluşturur"""
    try:
        candidate_folder = file_manager.create_candidate_folder(
            COMPANY_ID,
            f"Genar-{request.job_id}", 
            request.candidate_data
        )
        
        return {
            "status": "success",
            "message": "Başvuru başarıyla alındı",
            "candidate_folder": candidate_folder
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/candidate/save')
async def save_candidate_data_endpoint(request: dict):
    """Aday verilerini kaydet"""
    try:
        candidate_id = request.get("candidate_id", f"{JOB_ID}-00001")
        data_type = request.get("type")
        data = request.get("data")
        
        file_manager.save_candidate_data(
            COMPANY_ID, 
            JOB_ID, 
            candidate_id, 
            data_type, 
            data
        )
        
        return {"status": "saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/job')
async def get_job():
    """Job ad verilerini getir"""
    return file_manager.get_job_data(COMPANY_ID, JOB_ID, "JobAd")

@app.get('/api/qa')
async def get_qa():
    """Q&A verilerini getir"""
    return file_manager.get_job_data(COMPANY_ID, JOB_ID, "Q&A")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)