import json
from groq import AsyncGroq

async def interview_agent(client: AsyncGroq, conversation_history: str, user_message: str, cv_data: dict, job_ad_data: dict):
    # Video görüşme simule edildiği için direkt INTERVIEW_COMPLETE sinyali gönder
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