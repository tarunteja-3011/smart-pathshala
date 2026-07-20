import streamlit as st
import google.generativeai as genai
import time
import os
import yt_dlp
from PIL import Image

# ==========================================
# 🛑 CONFIGURATION: PASTE KEY ONCE HERE
# ==========================================
FIXED_API_KEY = "AIzaSyBWQ0pVuHbE_gF8MImeqV-n86tG7GtKJGU" 

# Configure Google AI immediately
try:
    genai.configure(api_key=FIXED_API_KEY)
except Exception as e:
    st.error(f"API Key Error: {e}")

# ==========================================
# 1. PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="Smart-Pathshala | Gemini 3 Pro",
    page_icon="🎓",
    layout="wide"
)

# Cyberpunk / High-Tech Educational CSS
st.markdown("""
<style>
    .stApp { background-color: #0E1117; }
    h1 {
        background: -webkit-linear-gradient(45deg, #FF4B4B, #4285F4, #9B72CB);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
    }
    .stTextInput > div > div > input {
        background-color: #161B22;
        color: white;
        border: 1px solid #30363D;
    }
    .success-box {
        padding: 1rem;
        background-color: #0d3625;
        border-left: 5px solid #00c853;
        border-radius: 5px;
        margin-bottom: 1rem;
        color: white;
    }
    .user-msg { background-color: #2b313e; padding: 10px; border-radius: 10px; margin-bottom: 5px; border-left: 3px solid #4285F4;}
    .ai-msg { background-color: #1c2333; padding: 10px; border-radius: 10px; margin-bottom: 5px; border-left: 3px solid #9B72CB;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ROBUST HELPER FUNCTIONS
# ==========================================

def get_gemini_model():
    """Connects to the best available model (Priority: Gemini 3 -> 2.5 -> 2.0 -> 1.5)"""
    models_to_try = [
        "gemini-3-pro-preview",    
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.0-flash-exp",
        "gemini-1.5-flash"
    ]
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            model.generate_content("test") # Ping test
            return model, model_name
        except:
            continue
    return None, "No Model Found"

def download_youtube_video(url):
    """
    FIXED DOWNLOADER: Forces 'Format 18' (360p Single File).
    This solves the 'Empty File' error on Windows laptops lacking FFmpeg.
    """
    output_base = "temp_lecture"
    
    # Clean up old files
    for file in os.listdir():
        if file.startswith("temp_lecture"):
            try: os.remove(file)
            except: pass

    # We use format '18' to ensure audio and video are ONE file.
    ydl_opts = {
        'format': '18/best', 
        'outtmpl': 'temp_lecture.%(ext)s',
        'quiet': True,
        'no_warnings': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            ext = info['ext']
            final_filename = f"temp_lecture.{ext}"
            return final_filename, info.get('title', 'YouTube Video'), f"video/{ext}"
    except Exception as e:
        return None, str(e), None

def upload_to_gemini(path, mime_type):
    """Uploads file to Google Cloud and waits for processing."""
    file = genai.upload_file(path, mime_type=mime_type)
    while file.state.name == "PROCESSING":
        time.sleep(2)
        file = genai.get_file(file.name)
    return file

# ==========================================
# 3. SIDEBAR & INPUTS
# ==========================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Google_Gemini_logo.svg/2560px-Google_Gemini_logo.svg.png", width=150)
    st.success(f"🔑 Key Loaded: ...{FIXED_API_KEY[-4:]}") 
    
    st.divider()
    st.markdown("### 📥 Knowledge Ingestion")
    
    # 1. PDF Upload
    uploaded_pdf = st.file_uploader("1. Upload Textbook (PDF)", type=['pdf'])
    
    # 2. YouTube URL
    youtube_url = st.text_input("2. Paste Lecture URL (YouTube)", placeholder="https://youtube.com/...")
    
    st.divider()
    init_btn = st.button("🚀 Initialize Agent", type="primary", use_container_width=True)

# ==========================================
# 4. MAIN APP LOGIC
# ==========================================
st.title("🎓 Smart-Pathshala")
st.caption("Powered by Google Gemini 3 Pro Preview | Multimodal Context Window")

if "chat_session" not in st.session_state:
    st.session_state.chat_session = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "status" not in st.session_state:
    st.session_state.status = "System Standby"

# --- INITIALIZATION LOGIC ---
if init_btn:
    if not youtube_url and not uploaded_pdf:
        st.error("⚠️ Please provide a PDF or a YouTube URL")
    else:
        status_placeholder = st.empty()
        try:
            # A. Connect to AI
            status_placeholder.info("🔌 Connecting to Neural Network...")
            model, model_name = get_gemini_model()
            
            if not model:
                st.error("Failed to connect to Gemini. Check API Key quota.")
                st.stop()
                
            files_to_send = []
            
            # B. Process YouTube
            if youtube_url:
                status_placeholder.info("🎥 Downloading & Analyzing YouTube Video... (This may take a moment)")
                video_path, video_title, mime_type = download_youtube_video(youtube_url)
                
                # Check if file exists AND has size > 0 (The robust check)
                if video_path and os.path.exists(video_path) and os.path.getsize(video_path) > 0:
                    gemini_video = upload_to_gemini(video_path, mime_type)
                    files_to_send.append(gemini_video)
                    st.toast(f"Video Ingested: {video_title}", icon="✅")
                else:
                    st.error(f"Failed to download video: {video_title}. Try a different link.") 
                    st.stop()
            
            # C. Process PDF
            if uploaded_pdf:
                status_placeholder.info("📄 Ingesting Textbook Context...")
                with open("temp_text.pdf", "wb") as f:
                    f.write(uploaded_pdf.read())
                gemini_pdf = upload_to_gemini("temp_text.pdf", "application/pdf")
                files_to_send.append(gemini_pdf)
                st.toast("Textbook Ingested", icon="✅")
                
            # D. Start Chat
            status_placeholder.info("🧠 Synchronizing Context Window...")
            
            sys_prompt = """
            You are Smart-Pathshala. 
            1. You have access to a video lecture and a textbook.
            2. When answering, cite the video timestamp (e.g., [05:23]) or the PDF page.
            3. If the user uploads an image, analyze it using the textbook definitions.
            """
            
            st.session_state.chat_session = model.start_chat(
                history=[
                    {"role": "user", "parts": files_to_send + ["Analyze these materials deeply."]},
                    {"role": "model", "parts": ["Materials processed. I am ready to tutor."]}
                ]
            )
            
            st.session_state.status = f"Active | Model: {model_name}"
            status_placeholder.empty()
            st.rerun()
            
        except Exception as e:
            st.error(f"Initialization Error: {e}")

# Display Active Status
if "Active" in st.session_state.status:
    st.markdown(f'<div class="success-box">✅ <b>System Online</b><br>Engine: {st.session_state.status.split(":")[1]}</div>', unsafe_allow_html=True)

# --- CHAT & VISUAL INTERFACE (TABS RESTORED) ---
tab1, tab2 = st.tabs(["💬 Contextual Chat", "📸 Visual Gap Analysis"])

with tab1:
    for msg in st.session_state.messages:
        role_class = "user-msg" if msg["role"] == "user" else "ai-msg"
        with st.chat_message(msg["role"]):
            st.markdown(f'<div class="{role_class}">{msg["content"]}</div>', unsafe_allow_html=True)
            
    if prompt := st.chat_input("Ask about the video or textbook..."):
        if st.session_state.chat_session:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(f'<div class="user-msg">{prompt}</div>', unsafe_allow_html=True)
            
            with st.spinner("Analyzing context..."):
                try:
                    response = st.session_state.chat_session.send_message(prompt)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    with st.chat_message("assistant"):
                        st.markdown(f'<div class="ai-msg">{response.text}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error("Error communicating with AI.")
        else:
            st.warning("⚠️ Please Initialize Agent first.")

with tab2:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.write("### 📤 Upload Diagram")
        st.info("Take a photo of a whiteboard/circuit. The AI will explain it using the Video/PDF context.")
        img_upload = st.file_uploader("Upload Image", type=["jpg", "png"])
    
    with col2:
        if img_upload and st.session_state.chat_session:
            image = Image.open(img_upload)
            st.image(image, caption="Student Query", width=300)
            if st.button("🔍 Analyze Gap"):
                with st.spinner("Linking visual to concepts..."):
                    res = st.session_state.chat_session.send_message(["Explain this image using the uploaded course material.", image])
                    st.markdown("### 💡 Concept Link")
                    st.markdown(res.text)
                    st.session_state.messages.append({"role": "assistant", "content": f"**Visual Analysis:**\n{res.text}"})