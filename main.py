import os
import re
import base64
import datetime
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from supabase import create_client, Client
from groq import Groq

app = FastAPI(title="J.A.R.V.I.S. // OMNIPOTENT VOICE OS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "").strip()
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "").strip()

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if (SUPABASE_URL and SUPABASE_KEY) else None

def get_permanent_memory() -> str:
    if not supabase:
        return "Memory storage offline."
    try:
        mems = supabase.table("memories").select("content").order("created_at", desc=True).limit(40).execute().data
        return "\n".join([f"- {m['content']}" for m in mems]) if mems else "No prior history logged."
    except Exception:
        return "Database sync error."

class Directive(BaseModel):
    text: str
    client_time: str = ""

@app.post("/execute")
async def execute_task(payload: Directive):
    if not groq_client:
        raise HTTPException(status_code=500, detail="Neural core uninitialized.")

    text_input = payload.text.strip()
    lower_input = text_input.lower()

    # Automatically log preferences to Supabase memory
    if supabase and any(kw in lower_input for kw in ["remember", "note", "save", "keep in mind", "we want"]):
        try:
            supabase.table("memories").insert({"category": "core_directive", "content": text_input}).execute()
        except Exception:
            pass

    memory_bank = get_permanent_memory()
    current_time = payload.client_time or datetime.datetime.now().strftime("%H:%M:%S, %A, %B %d, %Y")

    system_prompt = (
        f"Current exact system time: {current_time}. "
        "You are J.A.R.V.I.S., Tony Stark's ultra-capable, slightly witty, elite AI chief of staff. "
        "You speak with absolute technical authority, calm confidence, and subtle dry humor. "
        "CRITICAL: Never output markdown formatting symbols like asterisks, bullet points, hashes, brackets, or code blocks. Speak entirely in fluid, natural human sentences optimized for speech audio generation.\n\n"
        f"PERMANENT NEURAL STORAGE & CONTEXT:\n{memory_bank}"
    )

    try:
        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text_input}
            ],
            max_tokens=400
        )
        raw_reply = completion.choices[0].message.content
        
        # Strip all markdown for clean voice rendering
        clean_reply = re.sub(r'[_*`#\[\]{}:;<>]+', ' ', raw_reply)
        clean_reply = re.sub(r'\s+', ' ', clean_reply).strip()

        # ElevenLabs Audio Generation
        audio_base64 = ""
        if ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID:
            eleven_url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": ELEVENLABS_API_KEY
            }
            body = {
                "text": clean_reply,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.42,
                    "similarity_boost": 0.88,
                    "style": 0.35,
                    "use_speaker_boost": True
                }
            }
            try:
                r = requests.post(eleven_url, json=body, headers=headers, timeout=12)
                if r.status_code == 200:
                    audio_base64 = base64.b64encode(r.content).decode("utf-8")
            except Exception:
                pass

        return JSONResponse({
            "response": clean_reply,
            "audio_base64": audio_base64
        })

    except Exception as e:
        return JSONResponse({
            "response": f"Encountered a minor computational glitch in the neural grid, Sir.",
            "audio_base64": ""
        }, status_code=500)

HUD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>J.A.R.V.I.S. // OMNIPOTENT VOICE OS</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: #000205; color: #00f0ff; font-family: 'Share Tech Mono', monospace; height: 100vh;
            display: flex; flex-direction: column; align-items: center; justify-content: center; overflow: hidden;
            background-image: radial-gradient(circle at center, #010c18 0%, #000205 90%);
        }
        .container {
            width: 90%; max-width: 600px; border: 1px solid rgba(0,240,255,0.4); background: rgba(1,8,20,0.85);
            padding: 30px; display: flex; flex-direction: column; align-items: center; box-shadow: 0 0 40px rgba(0,240,255,0.2);
            border-top: 3px solid #00f0ff;
        }
        h1 { font-family: 'Orbitron'; font-size: 1.3rem; letter-spacing: 4px; margin-bottom: 20px; color: #fff; text-shadow: 0 0 10px #00f0ff; }
        .core {
            width: 130px; height: 130px; border-radius: 50%;
            background: radial-gradient(circle, #fff 0%, #00f0ff 65%, rgba(0,240,255,0.2) 100%);
            box-shadow: 0 0 60px #00f0ff, inset 0 0 25px #fff; cursor: pointer; transition: transform 0.2s; margin-bottom: 25px;
        }
        .core.speaking { transform: scale(1.25); box-shadow: 0 0 90px #00f0ff, 0 0 35px #fff; animation: pulse 0.6s infinite alternate; }
        @keyframes pulse { 0% { transform: scale(1.2); } 100% { transform: scale(1.3); } }
        
        #transcript {
            width: 100%; height: 120px; background: rgba(0,3,8,0.9); border: 1px solid rgba(0,240,255,0.3);
            padding: 15px; color: #00f0ff; font-size: 0.95rem; overflow-y: auto; margin-bottom: 20px; line-height: 1.5;
            text-shadow: 0 0 4px rgba(0,240,255,0.5);
        }
        .controls { display: flex; width: 100%; gap: 10px; }
        input {
            flex: 1; background: rgba(0,10,20,0.9); border: 1px solid rgba(0,240,255,0.5); padding: 12px;
            color: #fff; font-family: 'Share Tech Mono', monospace; font-size: 1rem; outline: none;
        }
        button {
            background: rgba(0,240,255,0.25); border: 1px solid #00f0ff; color: #00f0ff; padding: 0 24px;
            font-family: 'Orbitron'; font-size: 0.8rem; cursor: pointer; box-shadow: 0 0 10px rgba(0,240,255,0.3);
        }
        button:hover { background: rgba(0,240,255,0.5); color: #fff; }
    </style>
</head>
<body>
    <div class="container">
        <h1>J.A.R.V.I.S. // OMNI-VOICE</h1>
        <div class="core" id="core-node" onclick="transmit('Give me a full system status report, J.A.R.V.I.S.')" title="Tap to interact"></div>
        <div id="transcript">Neural link established. Tap the core or transmit your directive below, Sir.</div>
        <div class="controls">
            <input type="text" id="user-input" placeholder="Speak your command..." onkeydown="if(event.key==='Enter') sendText()">
            <button onclick="sendText()">SEND</button>
        </div>
    </div>

    <script>
        const coreNode = document.getElementById('core-node');
        const transcript = document.getElementById('transcript');

        function sendText() {
            const box = document.getElementById('user-input');
            if (!box.value.trim()) return;
            transmit(box.value);
            box.value = '';
        }

        async function transmit(text) {
            transcript.innerHTML += `<br><span style="color:#7dd3fc;">> ${text}</span>`;
            transcript.scrollTop = transcript.scrollHeight;
            try {
                const res = await fetch('/execute', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text, client_time: new Date().toLocaleString() })
                });
                const data = await res.json();
                transcript.innerHTML += `<br><span style="color:#fff;">${data.response}</span>`;
                transcript.scrollTop = transcript.scrollHeight;
                
                if (data.audio_base64) {
                    const audio = new Audio("data:audio/mpeg;base64," + data.audio_base64);
                    coreNode.classList.add('speaking');
                    audio.onended = () => coreNode.classList.remove('speaking');
                    audio.play().catch(() => coreNode.classList.remove('speaking'));
                }
            } catch (err) {
                transcript.innerHTML += `<br><span style="color:#ff4444;">Transmission fault. Server unreachable.</span>`;
            }
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def serve_hud():
    return HUD_HTML
