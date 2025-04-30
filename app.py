
import streamlit as st
import openai

# Configure OpenRouter for DeepSeek
openai.api_key = st.secrets["OPENROUTER_API_KEY"]
openai.api_base = "https://openrouter.ai/api/v1"

# Initialize chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

st.title("TalentScout - DeepSeek AI Assistant")

with st.sidebar:
    st.subheader("Session Control")
    if st.button("🔁 Reset Conversation"):
        st.session_state.chat_history = []
        st.rerun()

# Display chat
for msg in st.session_state.chat_history:
    sender = "You" if msg["is_user"] else "Assistant"
    st.markdown(f"**{sender}:** {msg['text']}")

# Input field
user_input = st.text_input("Your message:")
if user_input:
    st.session_state.chat_history.append({"text": user_input, "is_user": True})
    try:
        response = openai.ChatCompletion.create(
            model="deepseek-ai/deepseek-coder",
            messages=[
                {"role": "system", "content": "You are a helpful AI hiring assistant."},
                *[
                    {"role": "user" if msg["is_user"] else "assistant", "content": msg["text"]}
                    for msg in st.session_state.chat_history
                ]
            ],
            temperature=0.7
        )
        ai_reply = response.choices[0].message["content"]
    except Exception as e:
        ai_reply = f"❌ Error: {str(e)}"

    st.session_state.chat_history.append({"text": ai_reply, "is_user": False})
    st.rerun()
