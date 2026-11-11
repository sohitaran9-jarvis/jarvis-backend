from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import anthropic
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

class ImagePayload(BaseModel):
    image: str

@app.get("/", response_class=HTMLResponse)
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
                status.innerText = "Analyzing live feed with Claude...";
                const primingUtterance = new SpeechSynthesisUtterance("Analyzing surroundings...");
                window.speechSynthesis.speak(primingUtterance);

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
                    
                    if (data.response) {
                        status.innerText = data.response;
                        const reply = new SpeechSynthesisUtterance(data.response);
                        window.speechSynthesis.speak(reply);
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
        image_data = payload.image
        if "," in image_data:
            image_data = image_data.split(",")[1]

        # Updated to active current model ID
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
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
                            "text": "You are J.A.R.V.I.S., an advanced AI HUD assistant. Describe what you see in front of you concisely, accurately, and with a helpful sci-fi assistant tone, as if speaking directly to your user."
                        }
                    ],
                }
            ],
        )
        return {"response": message.content[0].text}
    except Exception as e:
        return {"error": str(e)}
