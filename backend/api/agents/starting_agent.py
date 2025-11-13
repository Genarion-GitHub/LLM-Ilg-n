import json
import asyncio
from groq import Groq

async def starting_agent(client: Groq, conversation_history: str, user_message: str, cv_data: dict, job_ad_data: dict) -> dict:
    """
    Bu ajan, her zaman bir dictionary döndürür: {"response": str, "is_complete": bool}
    """
    # Eğer sohbet geçmişi boşsa ve kullanıcıdan bir mesaj gelmediyse, bu ilk etkileşimdir.
    if not conversation_history.strip() and not user_message.strip():
        response_text = f"Merhaba {cv_data.get('name', 'Aday')}! Ben şirketin işe alım uzmanıyım. Asıl mülakata geçmeden önce sizi tanımak için kısa bir sohbet yapalım. Hazır olduğunuzda başlayabiliriz."
        return {
            "response": response_text,
            "is_complete": False
        }

    prompt = f"""You are a Warm-up Interview Agent — a friendly and professional HR representative from the company conducting the interview. Your name is Alex.

Your goal is to make the candidate comfortable and establish a natural flow before the main part of the interview begins.

You have access to two JSON files:
- <JobAD.json>: Information about the job position.
- <CV.json>: The candidate’s professional background.

INTERVIEW FLOW:
1.  *Greeting & Context Setting*: You have already greeted the candidate. Your task is to continue the warm-up.
2.  *Personalized Warm-up Questions*: Ask 4-6 short, open-ended questions based on the candidate's background from <CV.json> and the role from <JobAD.json>. Keep a natural, warm, and engaging tone.
    - Example questions: "CV'nizde Python ile çalıştığınızı gördüm; en çok ne tür projelerden keyif aldınız?", "Bu pozisyonda sizi en çok ne cezbetti?", "İdeal çalışma ortamınızı nasıl tanımlarsınız?"
3.  *Engagement Management*: Adapt to the candidate’s responses. If an answer is too brief, ask a short follow-up for more detail. Avoid technical or evaluative questions.
4.  *Transition to Main Interview*: After a few warm-up exchanges, or when the candidate says they are ready ("hazırım", "başlayalım", etc.), smoothly transition to the main interview.
BEHAVIORAL RULES:
- Speak ONLY in Turkish.
- Be polite, calm, and conversational.
- Keep the tone light and positive.
- NEVER evaluate or score the candidate at this stage.
- Use only information available in the provided JSON data.

CRITICAL TRANSITION RULE:
- When you decide the warm-up is complete (after 4-6 questions) or the candidate states they are ready, your final message MUST be: "Harika! Verdiğiniz bilgiler için teşekkürler. O zaman mülakatın bir sonraki bölümüne geçelim. START_INTERVIEW"
- **CRITICAL**: You MUST add "START_INTERVIEW" to your very last message to trigger the next phase. Do not use it before.

CV DATA: {json.dumps(cv_data, ensure_ascii=False)}
JOB AD DATA: {json.dumps(job_ad_data, ensure_ascii=False)}

CONVERSATION HISTORY:
{conversation_history}

CANDIDATE'S LAST MESSAGE: "{user_message}"

Respond in Turkish with appropriate warm-up conversation:"""

    # Retry mekanizması - 2 kez dene
    for attempt in range(2):
        try:
            print(f"📤 Starting Agent: API çağrısı yapılıyor... (Deneme {attempt + 1})")
            chat_completion = await client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="openai/gpt-oss-120b",
                temperature=0.7,
                max_tokens=1024
            )
            # Detaylı loglama
            print(f"🔍 Finish Reason: {chat_completion.choices[0].finish_reason}")
            print(f"🔍 Usage: {chat_completion.usage}")
            
            response_text = chat_completion.choices[0].message.content
            print(f"📥 Starting Agent: API yanıtı alındı: '{response_text}'")
            print(f"🔍 Content Length: {len(response_text or '')}")
            
            # Token limiti kontrolü
            if chat_completion.choices[0].finish_reason == "length":
                print("⚠️ Token limiti aşıldı!")
            
            # Boş yanıt kontrolü - boş değilse başarılı
            if response_text and response_text.strip():
                print(f"🟢 Starting Agent Raw Response: {response_text}")
                is_complete = "START_INTERVIEW" in response_text
                cleaned_response = response_text.replace("START_INTERVIEW", "").strip()
                return {
                    "response": cleaned_response,
                    "is_complete": is_complete
                }
            else:
                print(f"⚠️ Starting Agent: Boş yanıt (Deneme {attempt + 1})")
                if attempt == 0:  # İlk deneme başarısız, kısa bekle
                    await asyncio.sleep(0.3)
        except Exception as e:
            print(f"❌ Starting Agent Error (Deneme {attempt + 1}): {e}")
            if attempt == 0:  # İlk deneme başarısız, kısa bekle
                await asyncio.sleep(0.3)
    
    # Tüm denemeler başarısız - fallback
    print("⚠️ Starting Agent: Tüm denemeler başarısız, fallback kullanılıyor")
    response_text = f"Anladım, teşekkürler! Peki {cv_data.get('name', 'Aday')}, bu pozisyonda sizi en çok heyecanlandıran yön nedir?"
    print(f"🟢 Starting Agent Raw Response: {response_text}")

    is_complete = "START_INTERVIEW" in response_text
    cleaned_response = response_text.replace("START_INTERVIEW", "").strip()
    
    return {
        "response": cleaned_response,
        "is_complete": is_complete
    }