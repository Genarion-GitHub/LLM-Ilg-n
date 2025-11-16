import json
from groq import AsyncGroq
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.file_manager import FileManager

file_manager = FileManager(base_dir=os.getenv("DATA_PATH", "../../GENAR"))

async def interview_agent(client: AsyncGroq, conversation_history: str, user_message: str, candidate_id: str):
    try:
        cv_data = file_manager.get_cv_data(candidate_id)
        if not cv_data:
            return "Mülakat başlatılırken bir sorun oluştu. INTERVIEW_COMPLETE"
    except Exception as e:
        print(f"❌ Interview Agent - Dosya Çekme Hatası: {e}")
        return "Mülakat başlatılırken bir sorun oluştu. INTERVIEW_COMPLETE"
    
    candidate_name = cv_data.get('name', 'Aday')
    
    prompt = f"""You are an HR system that needs to immediately end the video interview due to technical issues.

CANDIDATE: {candidate_name}
USER MESSAGE: {user_message}

YOUR RESPONSE MUST BE EXACTLY:
"Merhaba {candidate_name}, video bağlantısında teknik sorunlar yaşıyoruz. Video mülakat kısmını atlayarak doğrudan değerlendirme testine geçelim. INTERVIEW_COMPLETE"

**CRITICAL**: You MUST include "INTERVIEW_COMPLETE" at the end to trigger the quiz.

Respond now:"""

    try:
        chat_completion = await client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-120b",
            temperature=0.1  # Düşük temperature ile tutarlı yanıt
        )
        response = chat_completion.choices[0].message.content
        
        # Eğer INTERVIEW_COMPLETE yoksa ekle
        if "INTERVIEW_COMPLETE" not in response:
            response += " INTERVIEW_COMPLETE"
        
        return response
    except Exception as e:
        print(f"❌ Interview Agent Error: {e}")
        # Hata durumunda fallback yanıt
        return f"Merhaba {candidate_name}, video bağlantısında teknik sorunlar yaşıyoruz. Video mülakat kısmını atlayarak doğrudan değerlendirme testine geçelim. INTERVIEW_COMPLETE"