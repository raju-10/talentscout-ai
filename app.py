import streamlit as st
import openai
import os
import json
from datetime import datetime
import re

# Set OpenRouter credentials for DeepSeek
openai.api_key = st.secrets["OPENROUTER_API_KEY"]
openai.api_base = "https://openrouter.ai/api/v1"

# Save chat
def save_chat(chat_history, candidate_info):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chat_history_{timestamp}.json"
    data = {"candidate_info": candidate_info, "chat_history": chat_history}
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    return filename

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'candidate_info' not in st.session_state:
    st.session_state.candidate_info = {
        "name": "",
        "email": "",
        "phone": "",
        "experience": "",
        "position": "",
        "location": "",
        "tech_stack": []
    }
if 'current_stage' not in st.session_state:
    st.session_state.current_stage = "greeting"
if 'is_complete' not in st.session_state:
    st.session_state.is_complete = False

# AI response
def get_ai_response(user_input, chat_history, candidate_info, current_stage):
    system_prompt = get_system_prompt(candidate_info, current_stage)
    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        role = "user" if msg["is_user"] else "assistant"
        messages.append({"role": role, "content": msg["text"]})
    messages.append({"role": "user", "content": user_input})

    try:
        response = openai.ChatCompletion.create(
            model="deepseek/deepseek-chat",
            messages=messages,
            temperature=0.7,
        )
        reply = response.choices[0].message["content"]
        update_candidate_info(user_input, current_stage, candidate_info)
        next_stage = determine_next_stage(current_stage, candidate_info)
        return reply, next_stage
    except Exception as e:
        return f"❌ Error: {str(e)}", current_stage

# Info extraction
def update_candidate_info(user_input, current_stage, candidate_info):
    user_input = user_input.strip()
    lower_input = user_input.lower()

    if current_stage == "collecting_info":
        if not candidate_info["name"] and not any(char.isdigit() for char in user_input):
            candidate_info["name"] = user_input.title()
        elif not candidate_info["email"] and "@" in user_input and "." in user_input:
            candidate_info["email"] = user_input
        elif not candidate_info["phone"] and re.match(r"^\\+?\\d[\\d\\s\\-]{7,15}$", user_input):
            candidate_info["phone"] = user_input
        elif not candidate_info["experience"] and "year" in lower_input:
            candidate_info["experience"] = user_input
        elif not candidate_info["position"] and any(w in lower_input for w in ["developer", "designer", "engineer", "role", "manager"]):
            candidate_info["position"] = user_input
        elif not candidate_info["location"] and any(w in lower_input for w in ["city", "remote", "india", "usa", "bangalore", "delhi"]):
            candidate_info["location"] = user_input

    elif current_stage == "tech_stack":
        technologies = [tech.strip() for tech in user_input.replace(",", " ").split() if len(tech.strip()) > 1]
        candidate_info["tech_stack"].extend(technologies)

# Stage progression
def determine_next_stage(current_stage, candidate_info):
    if current_stage == "greeting":
        return "collecting_info"
    if current_stage == "collecting_info":
        required = ["name", "email", "phone", "experience", "position", "location"]
        if all(candidate_info[k] for k in required):
            return "tech_stack"
        return "collecting_info"
    if current_stage == "tech_stack" and len(candidate_info["tech_stack"]) >= 3:
        return "tech_questions"
    if current_stage == "tech_questions":
        return "completion"
    return current_stage

# Prompt template
def get_system_prompt(candidate_info, current_stage):
    base_prompt = """
    You are TalentScout's AI Hiring Assistant. Have a friendly and professional conversation to collect candidate info and assess technical skills.
    1. Ask one question at a time.
    2. Do not mention you're an AI.
    3. Don't fabricate info about the hiring process.
    4. End the conversation if the user types exit/quit.
    """
    if current_stage == "greeting":
        return base_prompt + "Start by asking their full name."
    elif current_stage == "collecting_info":
        missing = [k for k, v in candidate_info.items() if not v and k != "tech_stack"]
        return base_prompt + f"You're collecting: {', '.join(missing)}. Ask one at a time."
    elif current_stage == "tech_stack":
        if len(candidate_info["tech_stack"]) >= 3:
            return base_prompt + "Begin technical questions based on their stack."
        return base_prompt + "Ask about technical tools, languages, and frameworks."
    elif current_stage == "tech_questions":
        return base_prompt + "Continue technical questions. After 3-5, end politely."
    elif current_stage == "completion":
        return base_prompt + "Thank the candidate and close the conversation."

# UI layout
st.title("TalentScout Hiring Assistant (DeepSeek via OpenRouter)")

with st.sidebar:
    st.subheader("Candidate Info")
    for key, val in st.session_state.candidate_info.items():
        if isinstance(val, list):
            st.write(f"{key.title()}: {', '.join(val)}")
        else:
            st.write(f"{key.title()}: {val}")
    if st.button("🔁 Reset"):
        st.session_state.chat_history = []
        st.session_state.candidate_info = {k: "" if k != "tech_stack" else [] for k in st.session_state.candidate_info}
        st.session_state.current_stage = "greeting"
        st.session_state.is_complete = False
        st.rerun()

# Start chat
if not st.session_state.chat_history:
    welcome = "Hello! I'm the TalentScout Hiring Assistant. What's your full name?"
    st.session_state.chat_history.append({"text": welcome, "is_user": False})

for message in st.session_state.chat_history:
    role = "You" if message["is_user"] else "Assistant"
    st.markdown(f"**{role}:** {message['text']}")

if not st.session_state.is_complete:
    user_input = st.text_input("Your response:")
    if user_input:
        if user_input.lower() in ["exit", "quit"]:
            st.session_state.chat_history.append({"text": user_input, "is_user": True})
            st.session_state.chat_history.append({
                "text": "Thanks! We'll review your info and get back to you. Goodbye!",
                "is_user": False
            })
            st.session_state.is_complete = True
            st.rerun()
        else:
            st.session_state.chat_history.append({"text": user_input, "is_user": True})
            ai_response, next_stage = get_ai_response(
                user_input,
                st.session_state.chat_history,
                st.session_state.candidate_info,
                st.session_state.current_stage
            )
            st.session_state.current_stage = next_stage
            st.session_state.chat_history.append({"text": ai_response, "is_user": False})
            if next_stage == "completion":
                save_chat(st.session_state.chat_history, st.session_state.candidate_info)
            st.rerun()
else:
    if st.button("Start New Chat"):
        st.session_state.chat_history = []
        st.session_state.candidate_info = {
            "name": "",
            "email": "",
            "phone": "",
            "experience": "",
            "position": "",
            "location": "",
            "tech_stack": []
        }
        st.session_state.current_stage = "greeting"
        st.session_state.is_complete = False
        st.rerun()
