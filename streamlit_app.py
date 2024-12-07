import streamlit as st
import pandas as pd
import random
import pydeck as pdk
import google.generativeai as genai
import os

# ----------------------------------------------------------------------------------
# 본 코드는 중구 지역경제 활성화 웹 서비스의 프로토타입 예시입니다.
# 실제 서비스 적용 시, 보안, 접근성, UI/UX 개선, 정확한 데이터 확보 등을
# 보다 공고히 할 필요가 있습니다.
#
# 아래 코드는 Google Generative AI를 활용하여 사용자의 요청에 대해 장소를 추천하는
# 간단한 예제입니다. 실제 서비스 적용 전, 다음 사항을 고려하십시오:
# 1. Google API Key를 안전하게 관리하고, 외부에 유출되지 않도록 주의하십시오.
# 2. 실제 데이터는 공공데이터 포털 또는 지자체 데이터베이스에서 가져와 신뢰성을 확보하십시오.
# 3. 장소 추천 알고리즘은 단순 랜덤 생성이 아닌, 실제 평가나 거리/시간 계산 로직,
#    지역 특색을 반영한 맞춤형 필터링 로직으로 개선하십시오.
# 4. UI/UX 개선: 반응형 웹 디자인, 시각 장애인을 위한 접근성 고려,
#    모바일 화면에 적합한 Layout 등.
# 5. 보안/프라이버시: 사용자 입력 정보 관리 및 위치 정보에 대한 보호.
#
# 본 예제 코드는 일종의 프로토타입으로써 모든 로직은 테스트/데모용이며,
# 실제 서비스 구축 시 대폭 개선 및 검증이 필요합니다.
# ----------------------------------------------------------------------------------

# Streamlit 페이지 기본 설정
st.set_page_config(
    layout="wide",
    page_title="중구 지역경제 활성화 서비스",
    page_icon="🌟"
)

# Google Generative AI API 키 설정 (환경변수 사용 권장)
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "AIzaSyD0OmoRH3ot6mapbEpYW_DvMQJ-oVE9Kaw")
genai.configure(api_key=GOOGLE_API_KEY)

# 모델 초기화
model = genai.GenerativeModel('gemini-1.5-flash')

# 데이터 생성 함수 (랜덤 추천 데이터)
def generate_data():
    categories = ["음식", "관광지", "카페", "쇼핑", "기타"]
    times = ["5분", "10분", "30분", "1시간 이상"]
    random_data = []
    for i in range(50):
        random_data.append({
            "장소 이름": f"추천 장소 {i + 1}",
            "카테고리": random.choice(categories),
            "시간": random.choice(times),
            "위도": 36.35 + random.uniform(-0.01, 0.01),
            "경도": 127.39 + random.uniform(-0.01, 0.01),
            "추천 이유": random.choice(["음식이 훌륭해요!", "친절한 서비스", "지역 특산물"]),
        })
    return pd.DataFrame(random_data)

@st.cache_data
def load_data():
    return generate_data()

data = load_data()

# CSS 스타일
st.markdown(
    """
    <style>
        .title {
            font-size: 2.5em;
            font-weight: bold;
            text-align: center;
            margin-bottom: 5px;
        }
        .subtitle {
            font-size: 1.2em;
            text-align: center;
            color: gray;
            margin-bottom: 20px;
        }
        .chat-container {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-top: 20px;
        }
        .user-message, .bot-message {
            display: flex;
            align-items: center;
        }
        .user-message {
            justify-content: flex-end;
        }
        .bot-message {
            justify-content: flex-start;
        }
        .message-bubble {
            padding: 10px 15px;
            border-radius: 20px;
            font-size: 1em;
            max-width: 70%;
            line-height: 1.4;
        }
        .user-bubble {
            background-color: #DCF8C6;
            color: black;
        }
        .bot-bubble {
            background-color: #ECECEC;
            color: black;
        }
        .sidebar .block-container {
            padding-top: 20px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# 상단 제목 섹션
st.markdown('<div class="title">🌟 중구로 놀러 오세요! 🌟</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">중구 지역경제를 활성화하고 더 많은 즐거움을 누려보세요!</div>', unsafe_allow_html=True)

# 사이드바에서 카테고리 및 시간 선택
st.sidebar.header("🔎 필터 옵션")

if "selected_category" not in st.session_state:
    st.session_state.selected_category = None

if "selected_time" not in st.session_state:
    st.session_state.selected_time = None

selected_category = st.sidebar.radio(
    "카테고리를 선택하세요:",
    ["전체", "음식", "관광지", "카페", "쇼핑", "기타"],
    index=0,
    key="category_radio"
)

if selected_category == st.session_state.selected_category:
    st.session_state.selected_category = None
else:
    st.session_state.selected_category = selected_category

selected_time = st.sidebar.radio(
    "시간을 선택하세요:",
    ["전체", "5분", "10분", "30분", "1시간 이상"],
    index=0,
    key="time_radio"
)

if selected_time == st.session_state.selected_time:
    st.session_state.selected_time = None
else:
    st.session_state.selected_time = selected_time

if "filtered_data" not in st.session_state:
    st.session_state.filtered_data = pd.DataFrame(columns=["장소 이름", "카테고리", "시간", "위도", "경도", "추천 이유"])

filtered_data = data.copy()

if st.session_state.selected_category and st.session_state.selected_category != "전체":
    filtered_data = filtered_data[filtered_data["카테고리"] == st.session_state.selected_category]

if st.session_state.selected_time and st.session_state.selected_time != "전체":
    filtered_data = filtered_data[filtered_data["시간"] == st.session_state.selected_time]

# 성심당 본점 정보 (좌표: 36.3277° N, 127.4273° E)
sungsimdang_main = pd.DataFrame([{
    "장소 이름": "성심당 본점",
    "카테고리": "음식",
    "시간": "5분",
    "위도": 36.3277,
    "경도": 127.4273,
    "추천 이유": "대전에서 가장 유명한 빵집이에요!"
}])

st.session_state.filtered_data = pd.concat([sungsimdang_main, filtered_data], ignore_index=True)

# IconLayer를 사용하기 위해 아이콘 매핑 정의
icon_url = "https://raw.githubusercontent.com/visgl/deck.gl-data/master/website/icon-atlas.png"
icon_mapping = {
    "음식": {"x": 0,   "y": 0,   "width": 128, "height":128, "anchorY":128},
    "관광지": {"x": 128, "y": 0,   "width": 128, "height":128, "anchorY":128},
    "카페": {"x": 0,   "y": 128, "width": 128, "height":128, "anchorY":128},
    "쇼핑": {"x": 128, "y":128,  "width": 128, "height":128, "anchorY":128},
    "기타": {"x": 256, "y": 0,   "width": 128, "height":128, "anchorY":128},
    "성심당": {"x": 0, "y": 0,   "width": 128, "height":128, "anchorY":128}
}

st.session_state.filtered_data["icon"] = st.session_state.filtered_data["카테고리"]
st.session_state.filtered_data.loc[st.session_state.filtered_data["장소 이름"] == "성심당 본점", "icon"] = "성심당"

# 성심당 본점 데이터 분리
sungsimdang_data = st.session_state.filtered_data[st.session_state.filtered_data["장소 이름"] == "성심당 본점"]
places_data = st.session_state.filtered_data[st.session_state.filtered_data["장소 이름"] != "성심당 본점"]

# 다른 장소 아이콘 사이즈를 더 키우기 (기존 8 -> 10)
icon_layer_places = pdk.Layer(
    "IconLayer",
    data=places_data,
    get_icon="icon",
    get_position=["경도", "위도"],
    get_size=10,  # 크기 확장
    icon_atlas=icon_url,
    icon_mapping=icon_mapping,
    pickable=False
)

# 성심당 아이콘 레이어 (파란색으로 표시)
icon_layer_sungsimdang = pdk.Layer(
    "IconLayer",
    data=sungsimdang_data,
    get_icon="icon",
    get_position=["경도", "위도"],
    get_size=15, # 기존보다 크게
    icon_atlas=icon_url,
    icon_mapping=icon_mapping,
    get_color=[0,0,255], # 파란색으로
    pickable=False
)

# "현위치" 텍스트 레이어 (성심당 위에)
current_location_layer = pdk.Layer(
    "TextLayer",
    data=sungsimdang_data,
    get_position=["경도", "위도"],
    get_text="현위치",
    get_color=[0, 0, 0, 255],
    get_size=16,
    get_alignment_baseline="top",
    get_offset=[0,40],
    pickable=False
)

# 초기 뷰 설정
view_state = pdk.ViewState(
    latitude=36.3277,
    longitude=127.4273,
    zoom=17,
    pitch=0,
)

# 지도 스타일 변경 (밝은 톤의 mapbox 스타일)
deck = pdk.Deck(
    layers=[icon_layer_places, icon_layer_sungsimdang, current_location_layer],
    initial_view_state=view_state,
    tooltip=None,
    map_style='mapbox://styles/mapbox/light-v9'  # 밝은 톤 지도 스타일
)

st.markdown("### 📍 성심당 본점 중심 중구 추천 장소 지도")
st.pydeck_chart(deck)

# 챗봇 섹션
st.markdown("### 🤖 AI 어시스턴트와 대화하기")

st.markdown('<div class="chat-container">', unsafe_allow_html=True)
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

for speaker, message in st.session_state.chat_history:
    if speaker == "User":
        st.markdown(
            f"""
            <div class='user-message'>
                <div class='message-bubble user-bubble'>{message}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class='bot-message'>
                <div class='message-bubble bot-bubble'>{message}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown("#### 💬 메시지 입력")

def handle_user_message():
    user_message = st.session_state["user_message"]
    if user_message:
        try:
            conversation_history = "\n".join([f"{speaker}: {message}" for speaker, message in st.session_state.chat_history])
            ai_prompt = f"{conversation_history}\nUser: {user_message}\nAssistant:"
            ai_response = model.generate_content(
                ai_prompt,
                generation_config=genai.types.GenerationConfig(
                    candidate_count=1,
                    stop_sequences=["\n"],
                    temperature=0.7,
                ),
            ).text

            st.session_state.chat_history.append(("User", user_message))
            st.session_state.chat_history.append(("Bot", ai_response))

            if "추천" in user_message or "검색" in user_message:
                place_type = "카페"
                if "카페" in user_message:
                    place_type = "카페"
                elif "공원" in user_message:
                    place_type = "관광지"
                elif "음식" in user_message or "맛집" in user_message:
                    place_type = "음식"

                new_places = pd.DataFrame([{
                    "장소 이름": f"새로운 {place_type} 추천 {i + 1}",
                    "카테고리": place_type,
                    "시간": "10분",
                    "위도": 36.3277 + random.uniform(-0.01, 0.01),
                    "경도": 127.4273 + random.uniform(-0.01, 0.01),
                    "추천 이유": f"멋진 {place_type} 공간이에요!",
                    "icon": place_type
                } for i in range(5)])

                st.session_state.filtered_data = pd.concat([st.session_state.filtered_data, new_places], ignore_index=True)

        except Exception as e:
            st.session_state.chat_history.append(("Bot", f"죄송해요, 오류가 발생했습니다. {str(e)}"))
        finally:
            st.session_state["user_message"] = ""

st.text_input(
    "궁금한 것을 물어보세요:",
    key="user_message",
    placeholder="예: 카페 추천해주세요!",
    on_change=handle_user_message,
)
