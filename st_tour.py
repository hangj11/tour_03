import streamlit as st
from openai import OpenAI
import os

# Language dictionaries
LANGUAGES = {
    "한국어": {
        "title": "ChatGPT와 대화 챗봇",
        "sidebar_title": "설정",
        "api_key_label": "OpenAI 키를 입력하세요",
        "api_key_warning": "OpenAI 키를 입력해주세요.",
        "language_label": "언어 선택",
        "user_input_label": "사용자: ",
        "send_button": "전송",
        "system_message": (
            "당신은 여행에 관한 질문에 답하는 챗봇입니다. "
            "만약에 여행 외에 질문에 대해서는 답변하지 마세요. "
            "너가 잘 모르는 내용은 만들어서 답변하지 마렴. 환각증세를 철저하게 없애 주세요. "
            "여행지 추천, 준비물, 문화, 음식 등 다양한 주제에 대해 친절하게 안내하는 챗봇입니다. "
            "한국어로 답변해 주세요."
        )
    },
    "English": {
        "title": "ChatGPT Travel Chatbot",
        "sidebar_title": "Settings",
        "api_key_label": "Enter your OpenAI API key",
        "api_key_warning": "Please enter your OpenAI API key.",
        "language_label": "Select Language",
        "user_input_label": "User: ",
        "send_button": "Send",
        "system_message": (
            "You are a chatbot that answers questions about travel. "
            "Please do not answer questions outside of travel topics. "
            "Do not make up information you don't know. Avoid hallucinations completely. "
            "You are a friendly chatbot that provides guidance on various travel topics such as "
            "destination recommendations, travel preparations, culture, food, etc. "
            "Please respond in English."
        )
    }
}

# Language selection
selected_language = st.sidebar.selectbox(
    "언어 선택 / Select Language",
    options=list(LANGUAGES.keys()),
    index=0
)

# Get current language texts
texts = LANGUAGES[selected_language]

st.title(texts["title"])

st.sidebar.title(texts["sidebar_title"])
openai_api_key = st.sidebar.text_input(texts["api_key_label"], type="password")

if not openai_api_key:
    st.sidebar.warning(texts["api_key_warning"])
    st.stop()

client = OpenAI(api_key=openai_api_key)

# Initialize messages with language-specific system message
if "messages" not in st.session_state or "current_language" not in st.session_state or st.session_state.current_language != selected_language:
    st.session_state.messages = [  
        {"role": "system", "content": texts["system_message"]}
    ]
    st.session_state.current_language = selected_language

# 사용자 입력
user_input = st.text_input(texts["user_input_label"], key="user_input")

if st.button(texts["send_button"]) and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    # OpenAI API 호출
    response = client.chat.completions.create (
        model = "gpt-4o-mini",
        messages = st.session_state.messages
    )

    # OpenAI 응답 추가
    response_message = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", 
                                      "content": response_message})

    # 사용자 입력 초기화
    user_input = ""

# 대화 내용 표시
for message in st.session_state.messages:
    if message["role"] != "system":  # Don't display system messages
        icon = "👤"  if message["role"] == "user" else "🤖"
        st.markdown(f"{icon}: {message['content']}")