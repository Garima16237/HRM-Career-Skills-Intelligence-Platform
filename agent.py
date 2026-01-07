import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """
You are a Career & Skills AI Agent.
Your responsibilities:
1. Analyze employee skills
2. Suggest certifications
3. Track career progression
4. Recommend next career steps
Be concise, structured, and professional.
"""

def career_agent(user_input):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",  # Free Groq-supported model
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content
