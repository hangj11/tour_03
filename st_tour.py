import streamlit as st
from openai import OpenAI
import folium
from streamlit_folium import st_folium
import requests
import json
import re

# Language dictionaries
LANGUAGES = {
    "한국어": {
        "title": "🌍 여행 챗봇 with 지도",
        "sidebar_title": "설정",
        "language_label": "언어 선택",
        "user_input_label": "여행 질문을 입력하세요: ",
        "send_button": "전송",
        "map_title": "🗺️ 추천 여행지",
        "api_error": "OpenAI API 키가 설정되지 않았습니다. Streamlit 설정에서 OPENAI_API_KEY를 추가해주세요.",
        "system_message": (
            "당신은 여행에 관한 질문에 답하는 전문 챗봇입니다. "
            "여행지를 추천할 때는 반드시 다음 형식으로 답변해주세요: "
            "LOCATION: [도시명, 국가명] "
            "여행 외의 질문에는 답변하지 마세요. "
            "정확하지 않은 정보는 만들어내지 마세요. "
            "여행지 추천, 준비물, 문화, 음식 등에 대해 친절하게 안내해주세요. "
            "한국어로 답변해 주세요."
        )
    },
    "English": {
        "title": "🌍 Travel Chatbot with Map",
        "sidebar_title": "Settings",
        "language_label": "Select Language",
        "user_input_label": "Enter your travel question: ",
        "send_button": "Send",
        "map_title": "🗺️ Recommended Destinations",
        "api_error": "OpenAI API key not configured. Please add OPENAI_API_KEY in Streamlit settings.",
        "system_message": (
            "You are a professional travel chatbot. "
            "When recommending destinations, always use this format: "
            "LOCATION: [City, Country] "
            "Do not answer questions outside of travel topics. "
            "Do not make up information you don't know. "
            "Provide friendly guidance on travel destinations, preparations, culture, food, etc. "
            "Please respond in English."
        )
    }
}

# Function to get coordinates from location name
def get_coordinates(location):
    """Get latitude and longitude from location name using Nominatim API"""
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={location}&format=json&limit=1"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
    except:
        pass
    return None, None

# Function to extract locations from text
def extract_locations(text):
    """Extract locations from chatbot response"""
    locations = []
    # Look for LOCATION: pattern
    pattern = r'LOCATION:\s*([^,]+),\s*([^\n]+)'
    matches = re.findall(pattern, text, re.IGNORECASE)
    
    for city, country in matches:
        city = city.strip()
        country = country.strip()
        locations.append(f"{city}, {country}")
    
    return locations

# Initialize Streamlit page
st.set_page_config(page_title="Travel Chatbot with Map", page_icon="🌍", layout="wide")

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

# API Key configuration using st.secrets
try:
    openai_api_key = st.secrets["OPENAI_API_KEY"]
    client = OpenAI(api_key=openai_api_key)
except:
    st.error(texts["api_error"])
    st.info("💡 **GitHub to Streamlit 배포 가이드:**\n1. GitHub 리포지토리에 코드 푸시\n2. Streamlit Cloud에서 앱 배포\n3. Advanced settings에서 OPENAI_API_KEY 추가")
    st.stop()

# Initialize session state
if "messages" not in st.session_state or "current_language" not in st.session_state or st.session_state.current_language != selected_language:
    st.session_state.messages = [  
        {"role": "system", "content": texts["system_message"]}
    ]
    st.session_state.current_language = selected_language
    st.session_state.locations = []

# Create two columns for chat and map
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("💬 채팅" if selected_language == "한국어" else "💬 Chat")
    
    # User input
    user_input = st.text_input(texts["user_input_label"], key="user_input")
    
    if st.button(texts["send_button"]) and user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        try:
            # OpenAI API call
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.messages
            )
            
            # Get response
            response_message = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": response_message})
            
            # Extract locations from response
            new_locations = extract_locations(response_message)
            if new_locations:
                st.session_state.locations.extend(new_locations)
                # Remove duplicates
                st.session_state.locations = list(set(st.session_state.locations))
            
        except Exception as e:
            st.error(f"API 오류: {str(e)}")
    
    # Display chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            if message["role"] != "system":
                icon = "👤" if message["role"] == "user" else "🤖"
                st.markdown(f"{icon}: {message['content']}")

with col2:
    st.subheader(texts["map_title"])
    
    # Create map
    if st.session_state.locations:
        # Create a map centered on the first location or world center
        if st.session_state.locations:
            first_location = st.session_state.locations[0]
            lat, lon = get_coordinates(first_location)
            if lat and lon:
                m = folium.Map(location=[lat, lon], zoom_start=6)
            else:
                m = folium.Map(location=[20, 0], zoom_start=2)
        else:
            m = folium.Map(location=[20, 0], zoom_start=2)
        
        # Add markers for all locations
        for location in st.session_state.locations:
            lat, lon = get_coordinates(location)
            if lat and lon:
                folium.Marker(
                    [lat, lon],
                    popup=folium.Popup(location, parse_html=True),
                    tooltip=location,
                    icon=folium.Icon(color='red', icon='info-sign')
                ).add_to(m)
        
        # Display map
        map_data = st_folium(m, width=500, height=400)
        
        # Show locations list
        if st.session_state.locations:
            st.write("📍 **추천된 여행지:**" if selected_language == "한국어" else "📍 **Recommended Destinations:**")
            for i, location in enumerate(st.session_state.locations, 1):
                st.write(f"{i}. {location}")
    else:
        # Default world map
        m = folium.Map(location=[20, 0], zoom_start=2)
        st_folium(m, width=500, height=400)
        st.info("여행지를 추천받으면 지도에 표시됩니다!" if selected_language == "한국어" else "Recommended destinations will appear on the map!")

# Clear locations button
if st.session_state.locations:
    if st.sidebar.button("🗑️ 지도 초기화" if selected_language == "한국어" else "🗑️ Clear Map"):
        st.session_state.locations = []
        st.rerun()
