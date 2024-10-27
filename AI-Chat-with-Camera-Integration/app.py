import asyncio  # Add this import
import streamlit as st
import cv2
from PIL import Image
import base64
import io
import time
import threading
import queue
import sounddevice as sd
import numpy as np
import wave
from pydub import AudioSegment  # Add this import
from text_to_speech import text_to_speech_stream
from speech_to_text import get_speech_input
from llm_utils import get_llm_response  # Import the function from llm_utils

def init_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'camera_active' not in st.session_state:
        st.session_state.camera_active = False
    if 'camera_thread' not in st.session_state:
        st.session_state.camera_thread = None
    if 'camera_stop_event' not in st.session_state:
        st.session_state.camera_stop_event = threading.Event()
    if 'frame_queue' not in st.session_state:
        st.session_state.frame_queue = queue.Queue(maxsize=1)
    if 'selected_voice' not in st.session_state:
        st.session_state.selected_voice = "pNInz6obpgDQGcFmaJgB"  # Default voice

def capture_frame(video_capture):
    ret, frame = video_capture.read()
    if ret:
        # Convert BGR to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(frame)
    return None

def encode_image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

def camera_loop(stop_event, frame_queue):
    cap = cv2.VideoCapture(0)
    last_frame_time = time.time()
    
    while not stop_event.is_set():
        current_time = time.time()
        
        if current_time - last_frame_time >= 2:
            ret, frame = cap.read()
            if ret:
                # Convert BGR to RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = Image.fromarray(frame)
                
                # Put frame in queue, replacing old frame if necessary
                try:
                    frame_queue.put_nowait(frame)
                except queue.Full:
                    try:
                        frame_queue.get_nowait()
                        frame_queue.put_nowait(frame)
                    except queue.Empty:
                        pass
                
                last_frame_time = current_time
        
        time.sleep(0.1)
    
    cap.release()

def play_audio_stream(audio_stream):
    # Convert MP3 stream to WAV format using pydub
    audio_stream.seek(0)  # Ensure the stream is at the beginning
    audio = AudioSegment.from_file(audio_stream, format="mp3")
    
    # Export the audio to a BytesIO object in WAV format
    wav_stream = io.BytesIO()
    audio.export(wav_stream, format="wav")
    wav_stream.seek(0)  # Reset stream position to the beginning

    # Read the WAV stream and play it
    with wave.open(wav_stream, 'rb') as wf:
        data = wf.readframes(wf.getnframes())
        audio_array = np.frombuffer(data, dtype=np.int16)
        sd.play(audio_array, wf.getframerate())
        sd.wait()

def main():
    init_state()

    # Initialize chat history without images
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # Sidebar for controls
    st.sidebar.title("Controls")
    
    # Camera controls
    st.sidebar.subheader("Camera")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("▶️ Start Camera"):
            if not st.session_state.camera_active:
                st.session_state.camera_stop_event.clear()
                st.session_state.camera_active = True
                st.session_state.camera_thread = threading.Thread(
                    target=camera_loop,
                    args=(st.session_state.camera_stop_event, st.session_state.frame_queue),
                    daemon=True
                )
                st.session_state.camera_thread.start()
    with col2:
        if st.button("⏹️ Stop Camera"):
            if st.session_state.camera_active:
                st.session_state.camera_stop_event.set()
                st.session_state.camera_active = False
                if st.session_state.camera_thread:
                    st.session_state.camera_thread.join(timeout=1)
                    st.session_state.camera_thread = None

    # Conversation controls
    st.sidebar.subheader("Conversation")
    if st.sidebar.button("🔄 Start New Conversation"):
        st.session_state.chat_history = []  # Reset chat history

    # Language selection
    st.sidebar.subheader("Language Selection")
    language_map = {
        "English": "en",
        "Nepali": "ne",
        "Hindi": "hi",
        "French": "fr",  # Example addition
        "Other": "en"  # Default to English if "Other" is selected
    }
    selected_language = st.sidebar.selectbox("Choose a language", list(language_map.keys()))
    language_code = language_map[selected_language]

    # Add voice selection to sidebar
    st.sidebar.subheader("Voice Selection")
    voices = {
        "Alice (British female)": "Xb7hH8MSUJpSbSDYk0k2",
        "Aria (American female)": "9BWtsMINqrJLrRacOk9x",
        "Bill (American male)": "pqHfZKP75CvOlQylNhV4",
        "Brian (American male)": "nPczCjzI2devNBz1zQrb",
        "Callum (Transatlantic male)": "N2lVS1w4EtoT3dr4eOWO",
        "Charlie (Australian male)": "IKne3meq5aSn9XLyUdCD",
        "Charlotte (Swedish female)": "XB0fDUnXU5powFXDhCwa",
        "Chris (American male)": "iP95p4xoKVk53GoZ742B",
        "Daniel (British male)": "onwK4e9ZLuTAKqWW03F9",
        "Eric (American male)": "cjVigY5qzO86Huf0OWal",
        "George (British male)": "JBFqnCBsd6RMkjVDRZzb",
        "Jessica (American female)": "cgSgspJ2msm6clMCkdW9",
        "Laura (American female)": "FGY2WhTYpPnrIDTdsKH5",
        "Liam (American male)": "TX3LPaxmHKxFdv7VOQHJ",
        "Lily (British female)": "pFZP5JQG7iQjIQuC4Bku",
        "Matilda (American female)": "XrExE9yKIg1WjnnlVkGX",
        "River (American non-binary)": "SAz9YHcvj6GT2YYXdXww",
        "Roger (American male)": "CwhRBWXzGAHq8TQ4Fs17",
        "Sarah (American female)": "EXAVITQu4vr4xnSDxMaL",
        "Will (American male)": "bIHbv24MWmeRgasZH58o"
    }
    selected_voice_name = st.sidebar.selectbox("Choose a voice", list(voices.keys()))
    st.session_state.selected_voice = voices[selected_voice_name]

    # Add LLM service selection to sidebar
    st.sidebar.subheader("LLM Service Selection")
    llm_service = st.sidebar.radio("Choose LLM Service", ("Groq", "Anthropic"))
    use_groq = llm_service == "Groq"

    # Main layout
    st.title("AI Chat with Camera Integration")

    # Sidebar for camera feed
    st.sidebar.subheader("Camera Feed")
    camera_placeholder = st.sidebar.empty()  # Create a placeholder for the camera feed
    if st.session_state.camera_active:
        try:
            frame = st.session_state.frame_queue.get_nowait()
            camera_placeholder.image(frame, use_column_width=True)  # Update the placeholder with the latest frame
            st.session_state.current_frame = frame
        except queue.Empty:
            pass
    else:
        st.sidebar.info("Camera inactive. Click 'Start' in the sidebar to begin.")

    # Chat section
    st.subheader("Chat History")
    for message in st.session_state.chat_history:
        role_icon = "👤" if message["role"] == "user" else "🤖"
        st.markdown(f"""
            <div class="message-container" style="padding: 10px; border-radius: 5px; background-color: #e0e0e0; color: #333; margin-bottom: 10px;">
                <strong>{role_icon} {message["role"].title()}:</strong><br>
                {message["content"]}
            </div>
        """, unsafe_allow_html=True)
    
    # Chat input
    col1, col2 = st.columns([1, 5])
    with col1:
        mic_button = st.button("🎤 Speak", key="mic_button")
    with col2:
        prompt = st.chat_input("Ask me anything about what you see...")

    if mic_button:
        st.info("Recording... Please speak into the microphone.")
        # Pass the language code to get_speech_input
        prompt = get_speech_input(language=language_code)
        st.success("Recording complete. Transcription: " + prompt)

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        print(f"Prompt: {prompt}")
        print(f"Language: {selected_language}")
        print(f"Use Groq: {use_groq}")
        print(f"Selected Voice: {st.session_state.selected_voice}")
        print(f"Camera Active: {st.session_state.camera_active}")
        print(f"Frame Queue: {st.session_state.frame_queue}")
        print(f"Camera Stop Event: {st.session_state.camera_stop_event}")
        print(f"Messages: {st.session_state.messages}")
        
        if st.session_state.camera_active:
            current_frame = st.session_state.get('current_frame')
            if current_frame:
                image_base64 = encode_image_to_base64(current_frame)
                response = asyncio.run(get_llm_response(prompt, image_base64, selected_language, use_groq))
            else:
                response = asyncio.run(get_llm_response(prompt, language=selected_language, use_groq=use_groq))
        else:
            response = asyncio.run(get_llm_response(prompt, language=selected_language, use_groq=use_groq))
        
        # Append to chat history without images
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Update the audio stream creation to use the selected voice
        audio_stream = text_to_speech_stream(response.strip(), st.session_state.selected_voice)
        play_audio_stream(audio_stream)
        
        st.rerun()

if __name__ == "__main__":
    main()
