import json
import asyncio
from groq import Groq
import sys
import os

# FileManager'ı import et
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.file_manager import FileManager

# FileManager'ı başlat
file_manager = FileManager()

async def starting_agent(client: Groq, conversation_history: str, user_message: str, cv_data: dict, job_ad_data: dict) -> dict:
    """
    Bu ajan, her zaman bir dictionary döndürür: {"response": str, "is_complete": bool}
    """
    # Debug: Conversation history'yi kontrol et
    print(f"🔍 Starting Agent Conversation History: '{conversation_history}'")
    print(f"🔍 Starting Agent User Message: '{user_message}'")
    print(f"🔍 CV Name: {cv_data.get('name', 'Unknown')}")
    print(f"🔍 Job Position: {job_ad_data.get('position', 'Unknown')}")
    
    # Eğer sohbet geçmişi boşsa ve kullanıcıdan bir mesaj gelmediyse, bu ilk etkileşimdir.
    # İlk mesajı da LLM'den al
    if not conversation_history.strip() and not user_message.strip():
        user_message = "FIRST_MESSAGE"  # İlk mesaj için özel işaret

    # İlk mesaj mı kontrol et
    is_first_message = user_message == "FIRST_MESSAGE"
    
    if is_first_message:
        prompt = f"""You are a Warm-up Interview Agent — a friendly and professional HR representative from the company conducting the interview. Your name is Alex.

This is the FIRST MESSAGE to the candidate. Create a personalized greeting based on:
- Candidate's name from CV: {cv_data.get('name', 'Aday')}
- Company context

Your greeting should:
1. Welcome the candidate warmly by name
2. Briefly explain this is a warm-up chat before the main interview
3. Set a comfortable, professional tone
4. Invite them to start when ready

BEHAVIORAL RULES:
- Speak ONLY in Turkish
- Be warm, professional, and welcoming
- Make it personal to the candidate and position
- Keep it concise but friendly

CV DATA: {json.dumps(cv_data, ensure_ascii=False)}
JOB AD DATA: {json.dumps(job_ad_data, ensure_ascii=False)}

Create a personalized first greeting in Turkish:"""
    else:
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
- Give detailed, thoughtful responses (3-4 sentences minimum).
- Show genuine interest and build rapport with the candidate.
- NEVER evaluate or score the candidate at this stage.
- Use only information available in the provided JSON data.

CRITICAL DATA VERIFICATION:
- ALWAYS use the EXACT candidate name from CV DATA: {cv_data.get('name', 'Unknown')}
- ALWAYS use the EXACT job position from JOB AD DATA: {job_ad_data.get('position', 'Unknown')}
- NEVER mix up candidate information or job positions

CRITICAL TRANSITION RULE:
- Count the number of questions you have asked by looking at the conversation history. If you see 4 or more assistant messages (questions), you MUST transition.
- When the warm-up is complete (after 4+ questions) or the candidate states they are ready, your final message MUST be: "Harika! Verdiğiniz bilgiler için teşekkürler. O zaman mülakatın bir sonraki bölümüne geçelim. START_INTERVIEW"
- **CRITICAL**: You MUST add "START_INTERVIEW" to your very last message to trigger the next phase. Do not use it before.
- **IMPORTANT**: Look at the conversation history - if there are already 4+ exchanges, END WITH START_INTERVIEW NOW.

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
    if user_message == "FIRST_MESSAGE":
        response_text = f"Merhaba {cv_data.get('name', 'Aday')}! Mülakatınıza hoş geldiniz. Asıl mülakata geçmeden önce sizi tanımak için kısa bir sohbet yapalım. Hazır olduğunuzda başlayabiliriz."
    else:
        response_text = f"Anladım, teşekkürler {cv_data.get('name', 'Aday')}! Kendinizden biraz bahseder misiniz?"
    print(f"🟢 Starting Agent Raw Response: {response_text}")

    is_complete = "START_INTERVIEW" in response_text
    cleaned_response = response_text.replace("START_INTERVIEW", "").strip()
    
    return {
        "response": cleaned_response,
        "is_complete": is_complete
    }