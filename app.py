
import streamlit as st
import google.generativeai as genai
import os
import json
from datetime import datetime

# Configure Gemini API key from secrets
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel(model_name="gemini-1.0")

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

st.title("TalentScout - Gemini (Base Model) Assistant")

with st.sidebar:
    st.subheader("Controls")
    if st.button("🔁 Reset Conversation"):
        st.session_state.chat_history = []
        st.rerun()

# Display chat history
for msg in st.session_state.chat_history:
    role = "You" if msg["is_user"] else "Assistant"
    st.markdown(f"**{role}:** {msg['text']}")

# Input box
user_input = st.text_input("Your message:")
if user_input:
    st.session_state.chat_history.append({"text": user_input, "is_user": True})
    try:
        response = model.generate_content(user_input)
        st.session_state.chat_history.append({"text": response.text, "is_user": False})
    except Exception as e:
        st.session_state.chat_history.append({"text": f"❌ Error: {str(e)}", "is_user": False})
    st.rerun()
