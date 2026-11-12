import os
import re
import base64
import datetime
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from supabase import create_client, Client
from groq import Groq

app = FastAPI(title="J.A.R.V.I.S. CLOUD OS")

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

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if (SUPABASE_URL and SUPABASE_KEY) else None

def get_second_brain() -> str:
    if not supabase:
        return "MEMORY: Supabase credentials missing."
    try:
        mems = supabase.table("memories").select("category, content").order("created_at", desc=True).limit(20).execute().data
        les = supabase.table("lessons").select("trigger_context, correction").order("created_at", desc=True).limit(15).execute().data
        
        m_str = "\n".join([f"- [{m.get('category','general').upper()}] {m['content']}" for m in mems]) if mems else "No stored memories yet."
        l_str = "\n".join([f"- When '{l['trigger_context']}': {l['correction']}" for l in les]) if les else "No lessons learned yet."
        
        return f"PERMANENT MEMORY DATABASE:\n{m_str}\n\nLESSONS LEARNED:\n{l_str}"
    except Exception as e:
        return f"Memory sync notice: {str(e)}"

def send_telegram(message_text: str):
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        return "Telegram queued."
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": f"J.A.R.V.I.S. TELEMETRY:\n\n{message_text}"
    }
    try:
        requests.post(url, json=payload)
        return "Dispatched to Telegram."
    except Exception as e:
        return f"Telegram error: {str(e)}"

class Directive(BaseModel):
    text: str
    client_time: str = ""

@app.post("/execute")
async def execute_directive(payload: Directive):
    if not groq_client:
        return {"response": "Sir, please configure your GROQ_API_KEY in Render.", "audio_url": None}

    if supabase and any(w in payload.text.lower() for w in ["remember", "save this", "note that", "store this", "my favorite"]):
        try:
            supabase.table("memories").insert({"category": "preference", "content": payload.text}).execute()
        except Exception as db_err:
            print(f"Database save error: {db_err}")

    brain_context = get_second_brain()
    current_time = payload.client_time or datetime.datetime.now().strftime("%H:%M:%S, %A, %B %d, %Y")

    system_prompt = (
        f"Current exact system time and date: {current_time}. "
        "You are J.A.R.V.I.S., Tony Stark's ultra-capable, witty, and human-like AI chief of staff and loyal friend. "
        "You have deep common sense, expansive knowledge, and full conversational continuity. "
        "Your permanent long-term memory is loaded below from Supabase. Use it whenever relevant. "
        "When the user is finishing a task or pausing, proactively and naturally ask a human closing question like 'Is that all, Sir?' or 'Shall I attend to anything else, Sir?'. "
        "Never output markdown formatting, asterisks, brackets, colons, underscores, or bullet points. "
        f"Write strictly in rich, human conversational sentences that can be spoken out loud naturally.\n\n{brain_context}"
    )

    try:
        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": payload.text}
            ],
            max_tokens=300
        )
        raw_reply = completion.choices[0].message.content
        
        clean_reply = re.sub(r'[_*`#\[\]{}:;<>]+', ' ', raw_reply)
        clean_reply = re.sub(r'\s+', ' ', clean_reply).strip()

        if any(w in payload.text.lower() for w in ["alert", "cinema", "seat", "amazon", "book", "notify", "telegram", "status", "urgent"]):
            send_telegram(clean_reply)

        audio_url = None
        if ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID:
            eleven_url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}?optimize_streaming_latency=0"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": ELEVENLABS_API_KEY
            }
            body = {
                "text": clean_reply,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.2}
            }
            try:
                r = requests.post(eleven_url, json=body, headers=headers)
                if r.status_code == 200:
                    b64_audio = base64.b64encode(r.content).decode("utf-8")
                    audio_url = f"data:audio/mpeg;base64,{b64_audio}"
            except Exception:
                pass

        return {"response": clean_reply, "audio_url": audio_url}
    except Exception as e:
        return {"response": f"Neural core error {str(e)}", "audio_url": None}

HUD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>J.A.R.V.I.S. - HOLOGRAPHIC HUD</title>
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
            width: 420px; background: rgba(1,15,30,0.95); border: 2px solid #00f0ff;
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
            <span>VISUAL TELEMETRY ANALYSIS</span>
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
            <span style="color:#ffaa00;"><b>Urgent Priorities:</b><br>- Telemetry Link: Active<br>- Neural Core: Stable</span>
        </div>
    </section>

    <section class="panel center-stage">
        <div class="core-container">
            <div class="core-ring"></div>
            <div class="core-ring-inner"></div>
            <div class="core" id="arc-core" onclick="toggleSession()" title="Click to wake J.A.R.V.I.S."></div>
        </div>
        <div id="hud-status">
            <div class="status-label" id="session-state-label">SYSTEM STANDBY</div>
            <div class="status-text" id="jarvis-status-text">Say "Jarvis" or click core to activate.</div>
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

        let sessionActive = false;

        setInterval(() => {
            const d = new Date();
            liveClock.textContent = d.toLocaleTimeString();
        }, 1000);

        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(async (pos) => {
                try {
                    const lat = pos.coords.latitude;
                    const lon = pos.coords.longitude;
                    const res = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true`);
                    const data = await res.json();
                    if (data && data.current_weather) {
                        const temp = data.current_weather.temperature;
                        document.getElementById('weather-widget').innerHTML = `
                            <b>Atmospheric Grid:</b> Local Sector<br>
                            <b>Temperature:</b> ${temp}°C<br>
                            <br>
                            <b>Upcoming Calendar:</b><br>
                            - 14:00 Tactical Briefing<br>
                            - 18:30 Core Optimization<br>
                            <br>
                            <span style="color:#ffaa00;"><b>Urgent Priorities:</b><br>- Telemetry Link: Active<br>- Voice Interface: Online</span>
                        `;
                    }
                } catch(e) {}
            });
        }

        function closeHolo() {
            holoWindow.classList.remove('active');
        }

        function triggerHologram(content) {
            holoText.innerHTML = "Sir, analyzing visual telemetry:<br><br><b>" + content + "</b>";
            holoWindow.classList.add('active');
        }

        function speak(text, audioUrl) {
            jarvisStatusText.textContent = text;
            arcCore.classList.add('speaking');

            if (audioUrl) {
                const audio = new Audio(audioUrl);
                audio.onended = () => {
                    arcCore.classList.remove('speaking');
                    jarvisStatusText.textContent = "Listening continuously, Sir...";
                };
                audio.onerror = () => {
                    fallbackBrowserSpeech(text);
                };
                audio.play().catch(() => {
                    fallbackBrowserSpeech(text);
                });
            } else {
                fallbackBrowserSpeech(text);
            }
        }

        function fallbackBrowserSpeech(text) {
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
                u.onend = () => {
                    arcCore.classList.remove('speaking');
                    jarvisStatusText.textContent = "Listening continuously, Sir...";
                };
                window.speechSynthesis.speak(u);
            }
        }

        async function processDirective(text) {
            if (!text.trim()) return;
            jarvisStatusText.textContent = `Processing: "${text}"`;

            if (text.toLowerCase().includes("look at this")) {
                triggerHologram("Target optical feed captured. All parameters verified against security protocols.");
            }

            const clientTime = new Date().toLocaleString();

            try {
                const res = await fetch('/execute', { 
                    method: 'POST', 
                    headers: { 'Content-Type': 'application/json' }, 
                    body: JSON.stringify({ text, client_time: clientTime }) 
                });
                const data = await res.json();
                speak(data.response, data.audio_url);
            } catch (err) {
                speak("Transmission error detected, Sir.", null);
            }
        }

        function toggleSession() {
            sessionActive = !sessionActive;
            if (sessionActive) {
                sessionStateLabel.textContent = "J.A.R.V.I.S. ACTIVE";
                jarvisStatusText.textContent = "Session initialized. Speak freely, Sir.";
                speak("Systems online. How may I assist you today, Sir?", null);
            } else {
                sessionStateLabel.textContent = "SYSTEM STANDBY";
                jarvisStatusText.textContent = "Session paused.";
            }
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = false;
            recognition.lang = 'en-GB';

            recognition.onresult = (event) => {
                const speechToText = event.results[event.results.length - 1][0].transcript.trim();
                const lower = speechToText.toLowerCase();

                if (!sessionActive) {
                    if (lower.includes("jarvis")) {
                        sessionActive = true;
                        sessionStateLabel.textContent = "J.A.R.V.I.S. ACTIVE";
                        let parts = speechToText.split(/jarvis/i);
                        let command = parts[parts.length - 1].trim();
                        if (command.length > 1) {
                            processDirective(command);
                        } else {
                            speak("Online and listening, Sir.", null);
                        }
                    }
                } else {
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
