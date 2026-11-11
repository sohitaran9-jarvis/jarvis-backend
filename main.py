from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import anthropic
import os
import requests
import base64

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "").strip()

# --- DIAGNOSTIC: FETCH VALID MODELS FOR THIS KEY ---
print("--- CHECKING AVAILABLE ANTHROPIC MODELS ---")
try:
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01"
    }
    model_res = requests.get("https://api.anthropic.com/v1/models", headers=headers)
    if model_res.status_code == 200:
        models_data = model_res.json().get("data", [])
        model_ids = [m.get("id") for m in models_data]
        print(f"SUCCESS! Valid model IDs for your key: {model_ids}")
    else:
        print(f"Failed to list models: {model_res.status_code} - {model_res.text}")
except Exception as e:
    print(f"Error checking models: {e}")
print("------------------------------------------")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

class ImagePayload(BaseModel):
    image: str

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def serve_hud():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>J.A.R.V.I.S. CLOUD HUD</title>
        <style>
            body { background-color: #0b111e; color: #00ffcc; font-family: monospace; display: flex; flex-direction: column; align-items: center; padding: 20px; margin: 0; }
            h1 { font-size: 1.2rem; letter-spacing: 2px; margin-bottom: 15px; }
            video { width: 100%; max-width: 500px; border: 2px solid #00ffcc; border-radius: 10px; margin-bottom: 20px; background: #000; }
            button { background-color: #00ffcc; color: #0b111e; border: none; padding: 15px 30px; font-weight: bold; border-radius: 5px; font-size: 1rem; cursor: pointer; box-shadow: 0 0 15px rgba(0, 255, 204, 0.4); }
            button:active { background-color: #00cc99; }
            #status { margin-top: 20px; color: #aaa; text-align: center; max-width: 500px; line-height: 1.4; padding: 0 10px; }
        </style>
    </head>
    <body>
        <h1>J.A.R.V.I.S. CLOUD HUD</h1>
        <video id="webcam" autoplay playsinline muted></video>
        <button id="analyze-btn">Analyze Surroundings</button>
        <div id="status">System Ready</div>

        <script>
            const video = document.getElementById('webcam');
            const btn = document.getElementById('analyze-btn');
            const status = document.getElementById('status');

            navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
                .then(stream => { video.srcObject = stream; })
                .catch(err => { status.innerText = "Camera access error: " + err.message; });

            btn.addEventListener('click', async () => {
                status.innerText = "Analyzing surroundings via J.A.R.V.I.S...";

                const canvas = document.createElement('canvas');
                canvas.width = video.videoWidth || 640;
                canvas.height = video.videoHeight || 480;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                const base64Image = canvas.toDataURL('image/jpeg');

                try {
                    const response = await fetch('/analyze', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ image: base64Image })
                    });
                    
                    const data = await response.json();
                    
                    if (data.description && data.audio_base64) {
                        status.innerText = data.description;
                        
                        const audio = new Audio("data:audio/mpeg;base64," + data.audio_base64);
                        audio.play().catch(e => {
                            status.innerText += " (Audio playback blocked by browser - tap screen again)";
                        });
                    } else if (data.error) {
                        status.innerText = "Error: " + data.error;
                    }
                } catch (err) {
                    status.innerText = "Failed to communicate with backend.";
                }
            });
        </script>
    </body>
    </html>
    """

@app.post("/analyze")
async def analyze_surroundings(payload: ImagePayload):
    try:
        if not ANTHROPIC_API_KEY:
            return {"error": "ANTHROPIC_API_KEY environment variable is missing on Render."}

        image_data = payload.image
        if "," in image_data:
            image_data = image_data.split(",")[1]

        # Change this string to match whatever model ID prints out in your Render logs
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=150,
            system=(
                "You are J.A.R.V.I.S., an advanced AI chief of staff. "
                "CRITICAL FORMATTING RULE: Never output markdown formatting, bullet points, asterisks, hashtags, or special characters. "
                "Write purely in short, conversational sentences that sound completely natural when spoken out loud by a voice synthesizer."
            ),
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": "Describe what you see in front of you concisely as J.A.R.V.I.S. reporting to your user."
                        }
                    ],
                }
            ],
        )
        
        description = next(
            (block.text for block in message.content if getattr(block, "type", None) == "text"),
            "System error: could not parse visual response."
        )

        voice_id = "kZcoyALmepyQ92ntFnwY"
        elevenlabs_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        data = {
            "text": description,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }

        tts_response = requests.post(elevenlabs_url, json=data, headers=headers)
        
        if tts_response.status_code != 200:
            return {"error": f"ElevenLabs Error: {tts_response.text}"}

        audio_base64 = base64.b64encode(tts_response.content).decode("utf-8")

        return {
            "description": description,
            "audio_base64": audio_base64
        }
        
    except Exception as e:
        return {"error": str(e)}
