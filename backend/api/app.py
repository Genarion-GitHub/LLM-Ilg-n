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

def load_json_data(filename):
    try:
        with open(os.path.join(base_dir, 'data', filename), 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
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
        stage = "ending" if "ending" in session_id or "post-quiz" in session_id else "interview" if "interview" in session_id else "starting"
        sessions[session_id] = {
            "stage": stage,
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
    elif user_message == "QUIZ_COMPLETED":
        session["stage"] = "ending"
        response_text = await ending_agent(client, "", "", qna_data)
        if response_text:
            session["ending_conversation"].append({"sender": "assistant", "text": response_text})
    elif stage == "starting":
        agent_result = await starting_agent(client, history_str, user_message, cv_data, job_ad_data)
        response_text = agent_result.get("response", "")
        if agent_result.get("is_complete"):
            action = "START_INTERVIEW"
            session["stage"] = "interview"
    elif stage == "interview":
        response_text = await interview_agent(client, history_str, user_message, cv_data, job_ad_data)
        if "INTERVIEW_COMPLETE" in response_text:
            response_text = response_text.replace("INTERVIEW_COMPLETE", "").strip()
            action = "START_QUIZ"
            session["stage"] = "quiz"
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
    return await quiz_agent(client, qna_data, job_ad_data)

class QuizResultsRequest(BaseModel):
    sessionId: str
    score: int
    totalQuestions: int
    results: list

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

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)