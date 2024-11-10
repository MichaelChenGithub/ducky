import os
import threading
import wave
import pyaudio
import pygame
from dotenv import load_dotenv
from gtts import gTTS
from openai import OpenAI

# Load .env file
load_dotenv()

# Initialize the OpenAI client with the modern API pattern
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    base_url=os.getenv('OPENAI_API_BASE_URL', 'https://api.openai.com/v1')
)

# Initialize pygame speech mixer with explicit parameters for robustness
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=4096)

# Set up audio recording parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000  # Whisper supports 16kHz for best results
CHUNK = 1024
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "data/audio/voice_chat.wav"

def record_audio():
    """
    Capture audio from the microphone and save it to a file.
    
    Returns:
        bool: True if recording was successful, False otherwise
    """
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(WAVE_OUTPUT_FILENAME), exist_ok=True)
        
        # Initialize PyAudio
        audio = pyaudio.PyAudio()
        
        # Open audio stream
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        
        print("Recording...")
        frames = []
        
        # Record audio in chunks
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)
            
        print("Finished recording")
        
        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        audio.terminate()
        
        # Save the recorded audio to WAV file
        with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            
        return True
        
    except Exception as e:
        print(f"Error during recording: {e}")
        return False

def transcribe_audio():
    """
    Transcribe the recorded audio file using OpenAI's Whisper model.
    
    Returns:
        str: The transcription of the audio file.
    """
    try:
        # Check if the audio file exists
        if not os.path.exists(WAVE_OUTPUT_FILENAME):
            raise FileNotFoundError(f"Audio file not found: {WAVE_OUTPUT_FILENAME}")
            
        # Open the audio file and send to Whisper API
        with open(WAVE_OUTPUT_FILENAME, 'rb') as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            
        # Clean up the audio file
        os.remove(WAVE_OUTPUT_FILENAME)
        
        return transcription.text
        
    except Exception as e:
        print(f"Error during transcription: {e}")
        return None

def generate_gpt_response(prompt, messages=None):
    """
    Send transcribed text to GPT-4 for a response.
    
    Args:
        prompt (str): The prompt or input text.
        messages (list, optional): The context messages for the GPT-4 API.
        
    Returns:
        str: The GPT-4 response.
    """
    try:
        # Prepare the messages for the API
        if messages is None:
            messages = []
            
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Make the API call
        response = client.chat.completions.create(
            model="gpt-4",  # You can change this to other models as needed
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        # Extract and return the response text
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        else:
            return None
            
    except Exception as e:
        print(f"Error generating GPT response: {e}")
        return None

def speak_text(text, lang="en"):
    """
    Convert text to speech using gTTS and play the audio file using pygame.

    Args:
        text (str): The text to be spoken.
        lang (str): Language for speech (default is "en" for English).
    """

    def _speak():
        try:
            print("Converting text to speech...")
            # Convert the text to speech
            tts = gTTS(text=text, lang=lang)
            filename = "speech_output.mp3"

            print("Saving audio file...")
            try:
                tts.save(filename)
                print(f"Saved audio file: {filename}")
            except OSError as e:
                print(f"Failed to save file due to OS error: {e}")
                return
            except Exception as e:
                print(f"Unexpected error when saving file: {e}")
                return

            if os.path.exists(filename):
                print(f"Saved audio file successfully: {filename}")
            else:
                print(f"Failed to save the audio file: {filename}")
                return  # If the file didn't save, exit the function

            # Load and play the speech using pygame
            print("Loading audio file...")
            pygame.mixer.music.load(filename)
            print("Playing audio...")
            pygame.mixer.music.play()

            # Wait for the audio to finish playing
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

            print("Audio finished playing.")

            # Optionally, remove the file after playing
            os.remove(filename)
            print(f"Removed audio file: {filename}")
        except Exception as e:
            print(f"Error in speak_text: {e}")

    # Run the speech process in a separate thread to prevent blocking
    thread = threading.Thread(target=_speak)
    thread.daemon = True  # Mark thread as daemon so it exits when the app exits
    thread.start()
    thread.join()  # Ensure the thread completes before the program exits
