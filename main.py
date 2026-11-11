from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import anthropic
import base64
import json
import os

app = FastAPI()

# Initialize Anthropic client using environment variables
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 1. Enable CORS so your mobile HUD can communicate with Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ImagePayload(BaseModel):
    image: str # Base64 encoded image string from frontend

@app.post("/analyze")
async def analyze_surroundings(payload: ImagePayload):
    try:
        # Strip data URL prefix if present (e.g., "data:image/jpeg;base64,")
        image_data = payload.image
        if "," in image_data:
            image_data = image_data.split(",")[1]

        # Call Claude 3.5 Sonnet with Vision
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
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
        
        response_text = message.content[0].text
        return {"response": response_text}
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
def home():
    return {"status": "J.A.R.V.I.S. Cloud Backend is Live"}

MOBILE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>J.A.R.V.I.S. Cloud HUD</title>
    <style>
        body { background: #0b0f19; color: #00ffcc; font-family: monospace; text-align: center; margin: 0; padding: 20px; }
        video { width: 100%; max-width: 400px; border: 2px solid #00ffcc; border-radius: 10px; }
        button { background: #00ffcc; color: #0b0f19; border: none; padding: 15px 30px; font-size: 18px; font-weight: bold; border-radius: 8px; margin-top: 20px; cursor: pointer; }
        #response { margin-top: 20px; font-size: 16px; padding: 15px; background: #111827; border: 1px solid #1f2937; border-radius: 5px; text-align: left; max-width: 400px; margin-left: auto; margin-right: auto; }
    </style>
</head>
<body>
    <h2>J.A.R.V.I.S. CLOUD HUD</h2>
    <video id="video" autoplay playsinline></video><br>
    <button onclick="sendFrame()">Analyze Surroundings</button>
    <div id="response">Status: Online globally. Tap button to scan.</div>
    <canvas id="canvas" style="display:none;"></canvas>

    <script>
        const video = document.getElementById('video');
        const wsProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        const ws = new WebSocket(wsProtocol + window.location.host + '/ws');

        navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
            .then(stream => { video.srcObject = stream; })
            .catch(err => { document.getElementById('response').innerText = "Camera Error: " + err; });

        ws.onmessage = function(event) {
            document.getElementById('response').innerText = "J.A.R.V.I.S.: " + event.data;
            let utterance = new SpeechSynthesisUtterance(event.data);
            window.speechSynthesis.speak(utterance);
        };

        function sendFrame() {
            if (video.videoWidth === 0) return;
            const canvas = document.getElementById('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            const base64Data = canvas.toDataURL('image/jpeg', 0.7).split(',')[1];
            
            document.getElementById('response').innerText = "Analyzing live feed with Claude...";
            ws.send(JSON.stringify({
                image: base64Data,
                prompt: "Identify what is in front of my camera right now concisely and address me as Sir."
            }));
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def get_mobile_hud():
    return MOBILE_HTML

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            parsed = json.loads(data)
            
            image_bytes = base64.b64decode(parsed["image"])
            prompt = parsed["prompt"]
            
            # Send frame to Claude's Vision API
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
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
                                    "data": base64.b64encode(image_bytes).decode("utf-8"),
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ],
                    }
                ],
            )
            
            reply = response.content[0].text
            await websocket.send_text(reply)
    except WebSocketDisconnect:
        pass
