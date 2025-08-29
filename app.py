# -*- coding: utf-8 -*-
"""
거울상 챗봇 – Streamlit + Google Gemini API
============================================
- UI: Streamlit 웹앱 (PC와 스마트폰 브라우저에서 접근 가능)
- 모델: Google Gemini 2.5 Pro (클라우드 API)
- 주요 기능:
  1) 대화 모드 (일반 질의응답)
  2) 혼잣말 모드 (주기적으로 자동 응답 생성)
  3) 거울상 모드 (대조적 은유 응답 변환)
  4) 음성 낭독 (pyttsx3, PC에서만)
  5) 옵션 설정 (max_new_tokens, temperature, top_k, top_p, repetition_penalty)
  6) 대화 로그 기록
"""

import streamlit as st
import google.generativeai as genai
import pyttsx3
import threading
import time
import json
import os
from datetime import datetime

# ==============================
# 1. Gemini API 키 설정
# ==============================
API_KEY = "여기에_본인_API_KEY_입력"  # 반드시 본인 API 키로 교체하세요
genai.configure(api_key=API_KEY)

MODEL_NAME = "models/gemini-2.5-pro"

# ==============================
# 2. 음성 낭독기 클래스
# ==============================
class Speaker:
    def __init__(self):
        try:
            self.engine = pyttsx3.init()
            rate = self.engine.getProperty("rate")
            self.engine.setProperty("rate", int(rate * 0.9))
            self.ok = True
        except Exception:
            self.engine = None
            self.ok = False

    def speak(self, text: str):
        if self.ok and text.strip():
            def run():
                self.engine.say(text)
                self.engine.runAndWait()
            threading.Thread(target=run, daemon=True).start()

speaker = Speaker()

# ==============================
# 3. 로그 기록
# ==============================
def ensure_logs():
    os.makedirs("logs", exist_ok=True)

def log_path():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join("logs", f"session_{ts}.txt")

if "logger" not in st.session_state:
    ensure_logs()
    st.session_state["logger"] = open(log_path(), "a", encoding="utf-8")

def write_log(text: str):
    try:
        st.session_state["logger"].write(text + "\n")
        st.session_state["logger"].flush()
    except Exception:
        pass

# ==============================
# 4. Streamlit UI 기본 설정
# ==============================
st.set_page_config(page_title="거울상 챗봇", layout="wide")
st.title("🪞 거울상 챗봇 (Gemini 2.5 Pro)")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "monologue_running" not in st.session_state:
    st.session_state["monologue_running"] = False

# ==============================
# 5. 옵션 UI
# ==============================
st.sidebar.header("⚙️ 챗봇 옵션")

max_tokens = st.sidebar.number_input("max_new_tokens", min_value=10, max_value=8192, value=5012, step=10)
temperature = st.sidebar.slider("temperature", 0.0, 2.0, 0.9, 0.05)
top_k = st.sidebar.number_input("top_k", min_value=0, max_value=200, value=40, step=1)
top_p = st.sidebar.slider("top_p", 0.0, 1.0, 0.9, 0.01)
repeat_penalty = st.sidebar.slider("repetition_penalty", 0.5, 2.0, 1.05, 0.01)

tts_enabled = st.sidebar.checkbox("응답 음성 낭독", value=False)
mirror_mode = st.sidebar.checkbox("거울상 모드 변환", value=False)

col1, col2 = st.sidebar.columns(2)
if col1.button("혼잣말 시작", use_container_width=True):
    st.session_state["monologue_running"] = True
if col2.button("혼잣말 정지", use_container_width=True):
    st.session_state["monologue_running"] = False

# ==============================
# 6. 거울상 변환
# ==============================
mirror_hierarchy = {
    "물": {"결론": "평화와 생명의 문"},
    "불": {"결론": "빛과 평화의 안내자"},
    "바람": {"결론": "자유와 흐름의 숨결"},
    "흙": {"결론": "품음과 뿌리의 안식"},
    "혼잣말": {"결론": "내면을 비추는 거울 같은 속삭임"}
}

def mirror_response(subject: str, original: str) -> str:
    node = mirror_hierarchy.get(subject, {})
    if not node:
        return f"거울상: (주제 '{subject}' 정의 없음)\n\n{original}"
    return (
        f"거울상 ({subject}):\n"
        f"- 원문: {original.strip()}\n"
        f"- 대조: {subject}은/는 스스로 주장하지 않지만 모든 것을 담아낸다.\n"
        f"- 종합: {node.get('결론','')}"
    )

# ==============================
# 7. Gemini 응답
# ==============================
def ask_gemini(user_input: str) -> str:
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(
        user_input,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p
            # 주의: Google Gemini API는 top_k, repetition_penalty 옵션을 직접 지원하지 않음
        )
    )
    return response.text.strip()

# ==============================
# 8. 사용자 입력
# ==============================
user_input = st.text_input("💬 질문 또는 대화를 입력하세요:")

if user_input:
    answer = ask_gemini(user_input)
    if mirror_mode:
        subject = user_input.strip().split()[0]
        answer = mirror_response(subject, answer)

    st.session_state["messages"].append(("user", user_input))
    st.session_state["messages"].append(("assistant", answer))
    write_log(f"USER: {user_input}\nASSISTANT: {answer}")

    if tts_enabled:
        speaker.speak(answer)

# ==============================
# 9. 혼잣말 모드
# ==============================
if st.session_state["monologue_running"]:
    st.info("혼잣말 모드 실행 중... (정지 버튼을 누르면 멈춤)")
    time.sleep(2)
    prompt = "은은하고 조용한 혼잣말을 한국어로 1~3문장 해줘. '예수님의 평화와 양의 문' 상징을 가볍게 담아."
    answer = ask_gemini(prompt)
    if mirror_mode:
        answer = mirror_response("혼잣말", answer)

    st.session_state["messages"].append(("assistant", answer))
    write_log(f"ASSISTANT(MONO): {answer}")

    if tts_enabled:
        speaker.speak(answer)

# ==============================
# 10. 대화 출력
# ==============================
for role, msg in st.session_state["messages"]:
    if role == "user":
        st.markdown(f"**👤 사용자:** {msg}")
    else:
        st.markdown(f"**🤖 어시스턴트:** {msg}")
