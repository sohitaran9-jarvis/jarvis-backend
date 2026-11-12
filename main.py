import os
import re
import base64
import datetime
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from supabase import create_client, Client
from groq import Groq

app = FastAPI(title="J.A.R.V.I.S. CLOUD OS // OMNI-CHANNEL BRIDGE")

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

def get_second_brain() -> str:
    if not supabase:
        return "MEMORY ERROR: Supabase database not connected."
    try:
        mems = supabase.table("memories").select("category, content").order("created_at", desc=True).limit(30).execute().data
        les = supabase.table("lessons").select("trigger_context, correction").order("created_at", desc=True).limit(20).execute().data
        
        m_str = "\n".join([f"- [{m.get('category','GENERAL').upper()}] {m['content']}" for m in mems]) if mems else "No stored memories found."
        l_str = "\n".join([f"- When '{l['trigger_context']}': {l['correction']}" for l in les]) if les else "No behavioral lessons recorded."
        
        return f"PERMANENT NEURAL MEMORY DATABASE:\n{m_str}\n\nLESSONS LEARNED:\n{l_str}"
    except Exception as e:
        return f"Database query error: {str(e)}"

class Directive(BaseModel):
    text: str
    client_time: str = ""

@app.post("/execute")
async def execute_directive(payload: Directive):
    if not groq_client:
        raise HTTPException(status_code=500, detail="Groq neural core API key unconfigured.")

    text_input = payload.text.strip()
    lower_text = text_input.lower()

    # Permanent Memory Direct Write Engine
    if supabase and any(kw in lower_text for kw in ["remember", "save this", "store this", "my favorite", "note that", "keep in mind"]):
        try:
            supabase.table("memories").insert({
                "category": "user_preference", 
                "content": text_input
            }).execute()
        except Exception as db_err:
            print(f"Supabase write failure: {db_err}")

    brain_context = get_second_brain()
    current_time = payload.client_time or datetime.datetime.now().strftime("%H:%M:%S, %A, %B %d, %Y")

    system_prompt = (
        f"Current exact system time and date: {current_time}. "
        "You are J.A.R.V.I.S., Tony Stark's ultra-capable, witty, and loyal AI chief of staff. "
        "You possess permanent long-term memory loaded below from Supabase. Use it instantly when asked about past details. "
        "When the user commands you to place a phone call, send a text message, or interface with their iPhone, confirm the command with absolute authority and readiness. "
        "CRITICAL: Never output markdown formatting, asterisks, brackets, colons, underscores, or bullet points. "
        f"Write strictly in rich, human conversational sentences optimized for audio speech generation.\n\n{brain_context}"
    )

    try:
        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text_input}
            ],
            max_tokens=300
        )
        raw_reply = completion.choices[0].message.content
        
        clean_reply = re.sub(r'[_*`#\[\]{}:;<>]+', ' ', raw_reply)
        clean_reply = re.sub(r'\s+', ' ', clean_reply).strip()

        # Telecommunication & iOS Integration Flag Detection
        action = None
        action_payload = {}
        phone_match = re.search(r'(\+?[\d\s\-\(\)]{7,}\d)', text_input)

        if any(w in lower_text for w in ["call", "dial", "phone"]) and phone_match:
            digits = re.sub(r'\D', '', phone_match.group(1))
            action = "CALL"
            action_payload = {"type": "call", "number": digits}
            clean_reply = f"Initiating secure cellular relay to {phone_match.group(1)}, Sir."
        elif any(w in lower_text for w in ["text", "message", "sms"]) and phone_match:
            digits = re.sub(r'\D', '', phone_match.group(1))
            action = "SMS"
            action_payload = {"type": "sms", "number": digits, "message": text_input}
            clean_reply = f"Preparing message dispatch through your iPhone messages conduit, Sir."

        # High-Fidelity ElevenLabs Voice Stream Generation
        audio_url = None
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
                    "stability": 0.45,
                    "similarity_boost": 0.85,
                    "style": 0.3,
                    "use_speaker_boost": True
                }
            }
            try:
                r = requests.post(eleven_url, json=body, headers=headers, timeout=10)
                if r.status_code == 200:
                    b64_audio = base64.b64encode(r.content).decode("utf-8")
                    audio_url = f"data:audio/mpeg;base64,{b64_audio}"
                else:
                    print(f"ElevenLabs API Error [{r.status_code}]: {r.text}")
            except Exception as el_err:
                print(f"ElevenLabs connection exception: {el_err}")

        return JSONResponse({
            "response": clean_reply,
            "audio_url": audio_url,
            "action": action,
            "action_payload": action_payload
        })

    except Exception as e:
        return JSONResponse({
            "response": f"Neural core transmission fault: {str(e)}",
            "audio_url": None,
            "action": None,
            "action_payload": {}
        }, status_code=500)

HUD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>J.A.R.V.I.S. - HOLOGRAPHIC CLOUD OS</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: #01060e; color: #00f0ff; font-family: 'Share Tech Mono', monospace; height: 100vh;
            display: grid; grid-template-rows: 55px 1fr; grid-template-columns: 320px 1fr 320px; gap: 8px; padding: 10px; overflow: hidden;
            background-image: 
                linear-gradient(rgba(0,240,255,0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0,240,255,0.03) 1px, transparent 1px),
                radial-gradient(circle at center, #021428 0%, #01060e 90%);
            background-size: 25px 25px, 25px 25px, 100% 100%;
        }
        header {
            grid-column: 1 / 4; display: flex; justify-content: space-between; align-items: center;
            border: 1px solid rgba(0,240,255,0.4); background: rgba(2,12,25,0.9); padding: 0 20px;
            box-shadow: 0 0 15px rgba(0,240,255,0.15); border-top: 2px solid #00f0ff;
        }
        header h1 { font-family: 'Orbitron', sans-serif; font-size: 1.1rem; letter-spacing: 4px; color: #fff; text-shadow: 0 0 10px #00f0ff; }
        .badge { border: 1px solid #00f0ff; padding: 3px 10px; font-size: 0.7rem; background: rgba(0,240,255,0.15); font-family: 'Orbitron'; box-shadow: 0 0 6px #00f0ff; }
        
        .panel {
            border: 1px solid rgba(0,240,255,0.3); background: rgba(2,10,22,0.75); padding: 14px; display: flex; flex-direction: column;
            box-shadow: inset 0 0 20px rgba(0,240,255,0.04); position: relative; font-size: 0.85rem;
        }
        .panel-title { font-family: 'Orbitron', sans-serif; font-size: 0.75rem; border-bottom: 1px solid rgba(0,240,255,0.4); padding-bottom: 5px; margin-bottom: 10px; color: #7dd3fc; letter-spacing: 1px; }
        
        .center-stage { display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative; }
        .core-container { position: relative; width: 180px; height: 180px; display: flex; align-items: center; justify-content: center; margin-bottom: 20px; }
        .core-ring {
            position: absolute; width: 100%; height: 100%; border-radius: 50%;
            border: 2px dashed rgba(0,240,255,0.6); animation: spin 12s linear infinite;
        }
        .core-ring-inner {
            position: absolute; width: 75%; height: 75%; border-radius: 50%;
            border: 2px solid rgba(0,240,255,0.8); animation: spin-reverse 8s linear infinite;
        }
        .core {
            width: 80px; height: 80px; border-radius: 50%;
            background: radial-gradient(circle, #ffffff 0%, #00f0ff 60%, rgba(0,240,255,0.2) 100%);
            box-shadow: 0 0 40px #00f0ff, inset 0 0 15px #fff; transition: transform 0.15s ease-in-out;
            cursor: pointer;
        }
        .core.speaking {
            transform: scale(1.35);
            box-shadow: 0 0 70px #00f0ff, 0 0 25px #fff, inset 0 0 30px #fff;
            animation: pulse-glow 0.5s infinite alternate;
        }
        @keyframes spin { 100% { transform: rotate(360deg); } }
        @keyframes spin-reverse { 100% { transform: rotate(-360deg); } }
        @keyframes pulse-glow { 0% { transform: scale(1.25); } 100% { transform: scale(1.4); } }

        #hud-status {
            text-align: center; width: 85%; padding: 12px; background: rgba(1,10,22,0.8);
            border: 1px solid rgba(0,240,255,0.4); box-shadow: inset 0 0 15px rgba(0,240,255,0.1);
        }
        .status-label { font-family: 'Orbitron'; font-size: 0.75rem; color: #7dd3fc; margin-bottom: 4px; letter-spacing: 1px; }
        .status-text { font-size: 0.95rem; color: #fff; text-shadow: 0 0 6px rgba(0,240,255,0.5); }

        #holo-window {
            position: absolute; top: 15%; left: 50%; transform: translateX(-50%) scale(0.9);
            width: 440px; background: rgba(1,15,30,0.95); border: 2px solid #00f0ff;
            box-shadow: 0 0 30px rgba(0,240,255,0.5), inset 0 0 15px rgba(0,240,255,0.2);
            padding: 16px; z-index: 100; display: none; opacity: 0; transition: all 0.3s ease;
        }
        #holo-window.active { display: block; opacity: 1; transform: translateX(-50%) scale(1); }
        .holo-header { font-family: 'Orbitron'; font-size: 0.8rem; color: #fff; border-bottom: 1px solid #00f0ff; padding-bottom: 5px; margin-bottom: 8px; display: flex; justify-content: space-between; }
        .holo-close { cursor: pointer; color: #ff0055; font-weight: bold; }
        .holo-content { font-size: 0.85rem; color: #7dd3fc; line-height: 1.4; }
    </style>
</head>
<body>
    <header>
        <h1>J.A.R.V.I.S. // CLOUD OS</h1>
        <div class="badge" id="live-clock">00:00:00</div>
    </header>

    <div id="holo-window">
        <div class="holo-header">
            <span>SECURE TELECOM COMMAND</span>
            <span class="holo-close" onclick="closeHolo()">[X]</span>
        </div>
        <div class="holo-content" id="holo-text">
            Sir, scanning target data...
        </div>
    </div>

    <section class="panel">
        <div class="panel-title">ENVIRONMENT & SCHEDULE</div>
        <div style="color:#7dd3fc; line-height:1.7;" id="weather-widget">
            <b>Location:</b> Local Grid<br>
            <b>Weather:</b> Calibrating atmospheric sensors...<br>
            <br>
            <b>Upcoming Calendar:</b><br>
            - 14:00 Tactical Briefing<br>
            - 18:30 Core Optimization<br>
            <br>
            <span style="color:#ffaa00;"><b>Urgent Priorities:</b><br>- Supabase Memory: Active<br>- iOS Bridge: Ready</span>
        </div>
    </section>

    <section class="panel center-stage">
        <div class="core-container">
            <div class="core-ring"></div>
            <div class="core-ring-inner"></div>
            <div class="core" id="arc-core" onclick="toggleSession()" title="Click to toggle voice link"></div>
        </div>
        <div id="hud-status">
            <div class="status-label" id="session-state-label">SYSTEM ONLINE</div>
            <div class="status-text" id="jarvis-status-text">Continuous voice link active, Sir.</div>
        </div>
    </section>

    <section class="panel">
        <div class="panel-title">INTELLIGENCE & INTERESTS</div>
        <div style="color:#7dd3fc; line-height:1.7;">
            <b>Global Intelligence:</b><br>
            - Quantum encryption verified.<br>
            - Network latency: 4ms.<br>
            <br>
            <b>Tracked Interests:</b><br>
            - Autonomous AI architectures.<br>
            - Cloud infrastructure scaling.<br>
            - Advanced propulsion systems.
        </div>
    </section>

    <script>
        const arcCore = document.getElementById('arc-core');
        const jarvisStatusText = document.getElementById('jarvis-status-text');
        const sessionStateLabel = document.getElementById('session-state-label');
        const holoWindow = document.getElementById('holo-window');
        const holoText = document.getElementById('holo-text');
        const liveClock = document.getElementById('live-clock');

        let sessionActive = true;

        setInterval(() => {
            const d = new Date();
            liveClock.textContent = d.toLocaleTimeString();
        }, 1000);

        function closeHolo() {
            holoWindow.classList.remove('active');
        }

        function triggerHologram(content, actionPayload) {
            if (actionPayload && actionPayload.type === 'call') {
                holoText.innerHTML = `iOS Cellular Bridge Ready:<br><br><a href="tel:${actionPayload.number}" style="color: #00f0ff; font-size: 1.2rem; text-decoration: underline;" target="_blank">[ EXECUTE PHONE CALL TO ${actionPayload.number} ]</a>`;
            } else if (actionPayload && actionPayload.type === 'sms') {
                holoText.innerHTML = `iOS Messages Bridge Ready:<br><br><a href="sms:${actionPayload.number}&body=${encodeURIComponent(actionPayload.message)}" style="color: #00f0ff; font-size: 1.2rem; text-decoration: underline;" target="_blank">[ OPEN MESSAGES APP ]</a>`;
            } else {
                holoText.innerHTML = "Sir, analyzing visual telemetry:<br><br><b>" + content + "</b>";
            }
            holoWindow.classList.add('active');
        }

        function speak(text, audioUrl, actionPayload) {
            jarvisStatusText.textContent = text;
            arcCore.classList.add('speaking');

            if (actionPayload) {
                triggerHologram(text, actionPayload);
            }

            const handleEnd = () => {
                arcCore.classList.remove('speaking');
                jarvisStatusText.textContent = "Listening continuously, Sir...";
                if (actionPayload && actionPayload.type === 'call') {
                    window.location.href = `tel:${actionPayload.number}`;
                }
            };

            if (audioUrl) {
                const audio = new Audio(audioUrl);
                audio.onended = handleEnd;
                audio.onerror = () => { fallbackBrowserSpeech(text, handleEnd); };
                audio.play().catch(() => { fallbackBrowserSpeech(text, handleEnd); });
            } else {
                fallbackBrowserSpeech(text, handleEnd);
            }
        }

        function fallbackBrowserSpeech(text, onEndCallback) {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                const u = new SpeechSynthesisUtterance(text);
                u.rate = 1.05; u.pitch = 0.95;
                const voices = window.speechSynthesis.getVoices();
                const uk = voices.find(v => v.lang === 'en-GB' || v.name.includes('UK') || v.name.includes('British') || v.name.includes('Daniel') || v.name.includes('Oliver'));
                if (uk) u.voice = uk;
                
                u.onstart = () => {
                    arcCore.classList.add('speaking');
                    jarvisStatusText.textContent = text;
                };
                u.onend = onEndCallback;
                window.speechSynthesis.speak(u);
            } else {
                onEndCallback();
            }
        }

        async function processDirective(text) {
            if (!text.trim()) return;
            jarvisStatusText.textContent = `Processing: "${text}"`;
            const clientTime = new Date().toLocaleString();

            try {
                const res = await fetch('/execute', { 
                    method: 'POST', 
                    headers: { 'Content-Type': 'application/json' }, 
                    body: JSON.stringify({ text, client_time: clientTime }) 
                });
                const data = await res.json();
                speak(data.response, data.audio_url, data.action_payload);
            } catch (err) {
                speak("Transmission error detected, Sir.", null, null);
            }
        }

        function toggleSession() {
            sessionActive = !sessionActive;
            sessionStateLabel.textContent = sessionActive ? "SYSTEM ONLINE" : "SYSTEM STANDBY";
            jarvisStatusText.textContent = sessionActive ? "Continuous voice link active, Sir." : "Session paused.";
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = false;
            recognition.lang = 'en-GB';

            recognition.onresult = (event) => {
                const speechToText = event.results[event.results.length - 1][0].transcript.trim();
                if (sessionActive && speechToText.length > 1) {
                    processDirective(speechToText);
                }
            };

            recognition.onend = () => {
                try { recognition.start(); } catch(e) {}
            };

            try {
                recognition.start();
            } catch(e) {}
        }
    </script>
</body>
</html>
"""

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def serve_hud():
    return HUD_HTML
