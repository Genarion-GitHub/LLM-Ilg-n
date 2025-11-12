import json
from groq import AsyncGroq

async def quiz_agent(client: AsyncGroq, qna_data: dict, job_ad_data: dict):
    prompt = f"""You are a world-class HR hiring expert specialized in interview questions.

Your task is to create a personality quiz for a job candidate.
Read the provided <q&a.json> to identify 5 key skills required for the role. For each skill, prepare two multiple-choice questions based on the "Big Five Personality Traits" that are also RELEVANT to the <JobAD.json>. This will result in a total of 10 questions.

RULES:
1.  Generate exactly 10 questions (2 per identified skill).
2.  Each question must have 4 options (A, B, C, D). The answer choices should be close to each other, making it challenging to pick the correct one.
3.  The output must be a valid JSON object with a single key "questions".
4.  Each question object in the list must have: "question", "options" (a list of 4 strings), "correct_answer" (the letter A, B, C, or D), and "time" (always 60 seconds).
5.  IMPORTANT: All content (questions, options) must be in Turkish.

<q&a.json>: {json.dumps(qna_data, ensure_ascii=False)}

<JobAD.json>: {json.dumps(job_ad_data, ensure_ascii=False)}

Generate the quiz:"""

    chat_completion = await client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="openai/gpt-oss-120b",
    )
    response_text = chat_completion.choices[0].message.content
    clean_response = response_text.replace("```json", "").replace("```", "").strip()
    parsed = json.loads(clean_response)

    if 'questions' in parsed:
        # API'den gelen formatı frontend'in beklediği formata çevir
        formatted_questions = []
        for q in parsed['questions']:
            correct_answer = q.get('correct_answer', 'A').upper().strip()
            try:
                correct_index = ['A', 'B', 'C', 'D'].index(correct_answer)
            except ValueError:
                correct_index = 0
            formatted_questions.append({
                "question": q.get('question'),
                "options": q.get('options'),
                "correctAnswerIndex": correct_index,
                "time": q.get('time', 60)
            })
        return formatted_questions
    
    # Fallback in case of parsing error
    return []