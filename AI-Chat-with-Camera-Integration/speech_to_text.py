# speech_to_text.py
import os
from groq import Groq
import sounddevice as sd
import numpy as np
import wave
import io

from dotenv import load_dotenv

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def record_audio(duration=5, samplerate=44100):
    print("Recording...")
    audio_data = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()  # Wait until recording is finished
    print("Recording complete.")
    return audio_data


def save_audio_to_file(audio_data, samplerate, filename="temp_audio.wav"):
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)  # Set to 1 for mono
        wf.setsampwidth(2)  # 16-bit audio
        wf.setframerate(samplerate)
        wf.writeframes(audio_data.tobytes())
    return filename


def transcribe_audio(filename, language="en"):
    with open(filename, "rb") as file:
        transcription = groq_client.audio.transcriptions.create(
            file=(filename, file.read()),
            model="whisper-large-v3-turbo",
            response_format="json",
            language=language,  # Use the language parameter here
            temperature=0.0
        )
    return transcription.text


def get_speech_input(language="en"):
    audio_data = record_audio()
    filename = save_audio_to_file(audio_data, 44100)
    transcription = transcribe_audio(filename, language)
    os.remove(filename)  # Clean up the temporary file
    return transcription