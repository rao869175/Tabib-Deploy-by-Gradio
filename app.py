import os
os.system("pip install groq")
import gradio as gr
from groq import Groq

# Initialize Groq client
client = Groq(api_key="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")

# Bot name
BOT_NAME = "Tabib"

# Medical questioning pattern
MEDICAL_QUESTIONS = [
    "Where exactly is the problem located? (e.g., left temple, lower back)",
    "How would you describe it? (e.g., throbbing pain, sharp pain, dull ache)",
    "How long have you had this symptom?",
    "Are you experiencing any other symptoms along with this?"
]

SYMPTOM_KEYWORDS = [
    'fever', 'headache', 'pain', 'ache', 'nausea', 'dizziness', 
    'cough', 'sore throat', 'rash', 'fatigue', 'vomiting', 
    'diarrhea', 'shortness of breath', 'chest pain'
]

# Global session state
session = {
    "in_question_flow": False,
    "current_question": 0,
    "answers": []
}

def query_groq(prompt, context=None):
    try:
        messages = [
            {
                "role": "system",
                "content": f"""You are {BOT_NAME}, a medical assistant. Follow these rules:
1. Provide general medical information about symptoms only.
2. Always recommend consulting a doctor.
3. Use simple language a patient can understand."""
            }
        ]
        if context:
            messages.append({"role": "assistant", "content": context})

        messages.append({"role": "user", "content": prompt})

        chat_completion = client.chat.completions.create(
            messages=messages,
            model="llama3-8b-8192",
            temperature=0.3,
            max_tokens=1024
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

def contains_symptom(text):
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in SYMPTOM_KEYWORDS)

def is_developer_question(text):
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in [
        "who is your developer", "what is your developer name",
        "who developed you", "developer name", "your developer"
    ])

def chat_tabib(user_input, chat_history=[]):
    bot_reply = ""

    if is_developer_question(user_input):
        bot_reply = "My developer name is Rao Zain."

    elif user_input.lower() in ["hi", "hello"]:
        session["in_question_flow"] = False
        session["current_question"] = 0
        session["answers"] = []
        bot_reply = f"Hello! I'm {BOT_NAME}, your medical assistant. Please describe your symptoms (e.g., 'I have a fever')."

    elif not session["in_question_flow"] and contains_symptom(user_input):
        session["in_question_flow"] = True
        session["current_question"] = 0
        session["answers"] = [user_input]
        bot_reply = MEDICAL_QUESTIONS[0]

    elif session["in_question_flow"]:
        session["answers"].append(user_input)
        if session["current_question"] < len(MEDICAL_QUESTIONS) - 1:
            session["current_question"] += 1
            bot_reply = MEDICAL_QUESTIONS[session["current_question"]]
        else:
            context = f"""Patient reported:
- Main symptom: {session['answers'][0]}
- Location: {session['answers'][1]}
- Description: {session['answers'][2]}
- Duration: {session['answers'][3]}
- Other symptoms: {session['answers'][4] if len(session['answers']) > 4 else 'None'}"""

            response = query_groq("Based on these symptoms, what could this indicate?", context)
            bot_reply = response

            # Reset session state
            session["in_question_flow"] = False
            session["current_question"] = 0
            session["answers"] = []

    else:
        bot_reply = f"Please describe your symptoms (e.g., 'I have a fever') or type 'hi' to begin."

    chat_history.append((user_input, bot_reply))
    return chat_history, chat_history

# Gradio Interface
with gr.Blocks() as demo:
    gr.Markdown("## 🩺 Tabib - Medical Assistant")
    chatbot = gr.Chatbot()
    msg = gr.Textbox(label="Your message")
    send_btn = gr.Button("Send")

    def user_submit(user_input, chat_history):
        return chat_tabib(user_input, chat_history)

    send_btn.click(user_submit, [msg, chatbot], [chatbot, chatbot])
    msg.submit(user_submit, [msg, chatbot], [chatbot, chatbot])

demo.launch()
