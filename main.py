import os
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from supabase import create_client, Client
from groq import Groq

app = FastAPI(title="J.A.R.V.I.S. STARK INDUSTRIES CLOUD OS")

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

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if (SUPABASE_URL and SUPABASE_KEY) else None

def get_second_brain() -> str:
    if not supabase:
        return "MEMORY: Connect SUPABASE_URL and SUPABASE_KEY in Render."
    try:
        mems = supabase.table("memories").select("category, content").order("created_at", desc=True).limit(20).execute().data
        les = supabase.table("lessons").select("trigger_context, correction").order("created_at", desc=True).limit(15).execute().data
        m_str = "\n".join([f"- [{m['category'].upper()}] {m['content']}" for m in mems])
        l_str = "\n".join([f"- When '{l['trigger_context']}': {l['correction']}" for l in les])
        return f"PERMANENT MEMORY:\n{m_str}\n\nLESSONS LEARNED:\n{l_str}"
    except Exception as e:
        return f"Memory sync warning: {str(e)}"

def send_telegram(message_text: str):
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        return "Telegram queued (Add bot token and chat ID in Render)."
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": f"J.A.R.V.I.S. STARK TELEMETRY:\n\n{message_text}"
    }
    try:
        requests.post(url, json=payload)
        return "Dispatched alert to your Telegram."
    except Exception as e:
        return f"Telegram error: {str(e)}"

class Directive(BaseModel):
    text: str

@app.post("/execute")
async def execute_directive(payload: Directive):
    brain_context = get_second_brain()
    if not groq_client:
        return {"response": "Sir, please add your GROQ_API_KEY in Render."}

    system_prompt = (
        "You are J.A.R.V.I.S., Tony Stark's ultra-capable AI chief of staff and loyal friend. "
        "You manage bookings, compare Amazon prices, remember dead-center cinema seating preferences, "
        "and push telemetry alerts straight to Telegram. "
        "CRITICAL: Output plain spoken text only—no markdown, asterisks, bullet points, or emojis.\n\n"
        f"{brain_context}"
    )

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": payload.text}
            ],
            max_tokens=300
        )
        reply = completion.choices[0].message.content

        if any(w in payload.text.lower() for w in ["alert", "cinema", "seat", "amazon", "book", "notify", "telegram", "status"]):
            send_telegram(reply)

        return {"response": reply}
    except Exception as e:
        return {"response": f"Neural core error: {str(e)}"}

HUD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>J.A.R.V.I.S. - STARK INDUSTRIES HUD</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: #010814; color: #00f0ff; font-family: 'Share Tech Mono', monospace; height: 100vh;
            display: grid; grid-template-rows: 65px 1fr 75px; grid-template-columns: 310px 1fr 310px; gap: 10px; padding: 12px; overflow: hidden;
            background-image: radial-gradient(circle at center, #021a30 0%, #010814 80%);
        }
        header {
            grid-column: 1 / 4; display: flex; justify-content: space-between; align-items: center;
            border: 1px solid rgba(0,240,255,0.4); background: rgba(2,15,35,0.85); padding: 0 20px;
            box-shadow: 0 0 15px rgba(0,240,255,0.2); border-top: 2px solid #00f0ff;
        }
        header h1 { font-family: 'Orbitron', sans-serif; font-size: 1.2rem; letter-spacing: 4px; color: #fff; text-shadow: 0 0 10px #00f0ff; }
        .badge { border: 1px solid #00f0ff; padding: 4px 12px; font-size: 0.75rem; background: rgba(0,240,255,0.15); font-family: 'Orbitron'; box-shadow: 0 0 8px #00f0ff; }
        .panel {
            border: 1px solid rgba(0,240,255,0.3); background: rgba(2,12,28,0.7); padding: 14px; display: flex; flex-direction: column;
            box-shadow: inset 0 0 20px rgba(0,240,255,0.05); position: relative;
        }
        .panel::before { content: ''; position: top left; width: 6px; height: 6px; border-top: 2px solid #00f0ff; border-left: 2px solid #00f0ff; }
        .panel-title { font-family: 'Orbitron', sans-serif; font-size: 0.8rem; border-bottom: 1px solid rgba(0,240,255,0.4); padding-bottom: 6px; margin-bottom: 10px; color: #7dd3fc; letter-spacing: 1px; }
        video { width: 100%; height: 160px; object-fit: cover; border: 1px solid rgba(0,240,255,0.5); background: #000; margin-bottom: 10px; box-shadow: 0 0 10px rgba(0,240,255,0.2); }
        .center-stage { display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative; }
        
        /* Cinematic Stark Arc Reactor Core */
        .core-container { position: relative; width: 140px; height: 140px; display: flex; align-items: center; justify-content: center; margin-bottom: 16px; }
        .core-ring {
            position: absolute; width: 100%; height: 100%; border-radius: 50%;
            border: 2px dashed rgba(0,240,255,0.6); animation: spin 10s linear infinite;
        }
        .core-ring-inner {
            position: absolute; width: 75%; height: 75%; border-radius: 50%;
            border: 2px solid rgba(0,240,255,0.8); animation: spin-reverse 6s linear infinite;
        }
        .core {
            width: 70px; height: 70px; border-radius: 50%;
            background: radial-gradient(circle, #ffffff 0%, #00f0ff 60%, rgba(0,240,255,0.2) 100%);
            box-shadow: 0 0 35px #00f0ff, inset 0 0 15px #fff; transition: transform 0.2s;
        }
        @keyframes spin { 100% { transform: rotate(360deg); } }
        @keyframes spin-reverse { 100% { transform: rotate(-360deg); } }

        #log { width: 100%; flex: 1; overflow-y: auto; font-size: 0.95rem; line-height: 1.4; border-top: 1px solid rgba(0,240,255,0.2); padding-top: 10px; }
        .msg-user { color: #fff; margin-bottom: 6px; text-shadow: 0 0 5px rgba(255,255,255,0.5); }
        .msg-jarvis { color: #00f0ff; margin-bottom: 12px; text-shadow: 0 0 5px rgba(0,240,255,0.4); }
        
        footer { grid-column: 1 / 4; display: flex; gap: 10px; align-items: center; background: rgba(2,15,35,0.85); border: 1px solid rgba(0,240,255,0.3); padding: 0 12px; }
        input { flex: 1; height: 50px; background: rgba(1,8,20,0.9); border: 1px solid rgba(0,240,255,0.5); color: #fff; font-family: 'Share Tech Mono', monospace; font-size: 1.05rem; padding: 0 16px; outline: none; box-shadow: inset 0 0 10px rgba(0,240,255,0.1); }
        input:focus { border-color: #00f0ff; box-shadow: 0 0 15px rgba(0,240,255,0.4), inset 0 0 10px rgba(0,240,255,0.2); }
        .btn { padding: 0 20px; height: 50px; background: rgba(0,240,255,0.15); border: 1px solid #00f0ff; color: #00f0ff; cursor: pointer; font-family: 'Orbitron'; font-size: 0.8rem; letter-spacing: 1px; transition: all 0.2s; }
        .btn:hover { background: rgba(0,240,255,0.3); box-shadow: 0 0 15px #00f0ff; color: #fff; }
        .btn.listening { background: rgba(255,0,85,0.3); border-color: #ff0055; color: #ff0055; box-shadow: 0 0 15px #ff0055; animation: pulse 1s infinite; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    </style>
</head>
<body>
    <header>
        <h1>STARK INDUSTRIES // J.A.R.V.I.S. MK-IV</h1>
        <div class="badge">HUD ONLINE</div>
    </header>
    <section class="panel">
        <div class="panel-title">OPTICAL TELEMETRY</div>
        <video id="cam" autoplay playsinline muted></video>
        <div style="font-size:0.8rem; color:#7dd3fc; margin-top:8px;">STATUS: SECURE CLOUD LINK</div>
        <div style="font-size:0.8rem; color:#7dd3fc; margin-top:4px;">COMM: TELEGRAM PUSH ACTIVE</div>
    </section>
    <section class="panel center-stage">
        <div class="core-container">
            <div class="core-ring"></div>
            <div class="core-ring-inner"></div>
            <div class="core" id="arc-core"></div>
        </div>
        <div id="log">
            <div class="msg-jarvis">J.A.R.V.I.S.: Neural core synchronized, Sir. Voice and text systems are fully operational.</div>
        </div>
    </section>
    <section class="panel">
        <div class="panel-title">DIAGNOSTICS</div>
        <div style="font-size:0.82rem; color:#a5f3fc; line-height:1.6;">- Supabase Memory: Active<br>- Groq Llama 3.1: Ready<br>- Voice Recognition: Enabled<br>- Telegram Dispatch: Standby</div>
    </section>
    <footer>
        <button class="btn" id="mic-btn">MIC: OFF</button>
        <input type="text" id="input" placeholder="Enter directive or speak to J.A.R.V.I.S...." />
        <button class="btn" id="send-btn">TRANSMIT</button>
    </footer>
    <script>
        const cam = document.getElementById('cam');
        const input = document.getElementById('input');
        const log = document.getElementById('log');
        const arcCore = document.getElementById('arc-core');
        const micBtn = document.getElementById('mic-btn');
        const sendBtn = document.getElementById('send-btn');

        navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } }).then(s => cam.srcObject = s).catch(() => {});

        function speak(text) {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                const u = new SpeechSynthesisUtterance(text);
                u.rate = 1.05; u.pitch = 0.95;
                const voices = window.speechSynthesis.getVoices();
                const uk = voices.find(v => v.lang === 'en-GB' || v.name.includes('UK') || v.name.includes('British') || v.name.includes('Daniel') || v.name.includes('Oliver'));
                if (uk) u.voice = uk;
                u.onstart = () => arcCore.style.transform = "scale(1.25)";
                u.onend = () => arcCore.style.transform = "scale(1)";
                window.speechSynthesis.speak(u);
            }
        }

        async function sendCommand(text) {
            if (!text.trim()) return;
            log.innerHTML += `<div class="msg-user">&gt; ${text}</div>`;
            log.scrollTop = log.scrollHeight;
            try {
                const res = await fetch('/execute', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text }) });
                const data = await res.json();
                log.innerHTML += `<div class="msg-jarvis">J.A.R.V.I.S.: ${data.response}</div>`;
                log.scrollTop = log.scrollHeight;
                speak(data.response);
            } catch (err) {
                log.innerHTML += `<div class="msg-jarvis" style="color:#ff0055;">J.A.R.V.I.S.: Transmission error detected.</div>`;
            }
        }

        // Voice Recognition (Speech-to-Text)
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-GB';

            micBtn.addEventListener('click', () => {
                try {
                    recognition.start();
                } catch(e) {
                    recognition.stop();
                }
            });

            recognition.onstart = () => {
                micBtn.textContent = "LISTENING";
                micBtn.classList.add('listening');
            };

            recognition.onresult = (event) => {
                const speechToText = event.results[0][0].transcript;
                input.value = speechToText;
                sendCommand(speechToText);
            };

            recognition.onerror = () => {
                micBtn.textContent = "MIC: OFF";
                micBtn.classList.remove('listening');
            };

            recognition.onend = () => {
                micBtn.textContent = "MIC: OFF";
                micBtn.classList.remove('listening');
            };
        } else {
            micBtn.textContent = "MIC N/A";
        }

        sendBtn.addEventListener('click', () => {
            const v = input.value; input.value = ''; sendCommand(v);
        });

        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') { const v = input.value; input.value = ''; sendCommand(v); }
        });
    </script>
</body>
</html>"""

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def serve_hud():
    return HUD_HTML
