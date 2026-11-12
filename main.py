import os
import json
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

class Directive(BaseModel):
    text: str

@app.post("/execute")
async def execute_directive(payload: Directive):
    brain_context = get_second_brain()
    if not groq_client:
        return {"response": "Sir, please add your free GROQ_API_KEY in Render environment variables."}

    system_prompt = (
        "You are J.A.R.V.I.S., Tony Stark's ultra-capable AI chief of staff and loyal friend. "
        "You manage bookings, compare Amazon prices, remember dead-center cinema seating preferences, "
        "ask before applying CEA discount codes, and coordinate via WhatsApp. "
        "CRITICAL: Output plain spoken text only—no markdown, asterisks, bullet points, or emojis.\n\n"
        f"{brain_context}"
    )

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": payload.text}
            ],
            max_tokens=300
        )
        return {"response": completion.choices[0].message.content}
    except Exception as e:
        return {"response": f"Neural core error: {str(e)}"}

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def serve_hud():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>J.A.R.V.I.S. CLOUD OS</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Share+Tech+Mono&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: #030712; color: #00f0ff; font-family: 'Share Tech Mono', monospace; height: 100vh;
            display: grid; grid-template-rows: 60px 1fr 70px; grid-template-columns: 280px 1fr 280px; gap: 12px; padding: 12px; overflow: hidden;
        }
        header { grid-column: 1 / 4; display: flex; justify-content: space-between; align-items: center; border: 1px solid rgba(0,240,255,0.3); background: rgba(5,15,30,0.8); padding: 0 20px; }
        header h1 { font-family: 'Orbitron', sans-serif; font-size: 1.1rem; letter-spacing: 3px; }
        .badge { border: 1px solid #00f0ff; padding: 4px 10px; font-size: 0.75rem; background: rgba(0,240,255,0.1); }
        .panel { border: 1px solid rgba(0,240,255,0.3); background: rgba(5,15,30,0.6); padding: 14px; display: flex; flex-direction: column; }
        .panel-title { font-family: 'Orbitron', sans-serif; font-size: 0.8rem; border-bottom: 1px solid rgba(0,240,255,0.3); padding-bottom: 6px; margin-bottom: 10px; color: #7dd3fc; }
        video { width: 100%; height: 150px; object-fit: cover; border: 1px solid #00f0ff; background: #000; margin-bottom: 10px; }
        .center-stage { display: flex; flex-direction: column; align-items: center; justify-content: center; }
        .core { width: 110px; height: 110px; border-radius: 50%; background: radial-gradient(circle, #fff 0%, #00f0ff 50%, transparent 70%); box-shadow: 0 0 30px #00f0ff; margin-bottom: 16px; transition: transform 0.2s; }
        #log { width: 100%; flex: 1; overflow-y: auto; font-size: 0.95rem; line-height: 1.4; border-top: 1px solid rgba(0,240,255,0.2); padding-top: 10px; }
        .msg-user { color: #fff; margin-bottom: 6px; }
        .msg-jarvis { color: #00f0ff; margin-bottom: 12px; }
        footer { grid-column: 1 / 4; display: flex; gap: 10px; align-items: center; }
        input { flex: 1; height: 50px; background: rgba(5,15,30,0.9); border: 1px solid #00f0ff; color: #fff; font-family: 'Share Tech Mono', monospace; font-size: 1rem; padding: 0 16px; outline: none; }
        .btn { padding: 0 18px; height: 50px; background: rgba(0,240,255,0.1); border: 1px solid #00f0ff; color: #00f0ff; cursor: pointer; font-family: 'Orbitron'; font-size: 0.8rem; }
    </style>
</head>
<body>
    <header>
        <h1>J.A.R.V.I.S. CLOUD OS</h1>
        <div class="badge">CROSS-PLATFORM (£0.00)</div>
    </header>
    <section class="panel">
        <div class="panel-title">OPTICAL & TELEMETRY</div>
        <video id="cam" autoplay playsinline muted></video>
        <div style="font-size:0.8rem; color:#a5f3fc; margin-top:8px;">HOST: Render Cloud</div>
        <div style="font-size:0.8rem; color:#a5f3fc; margin-top:4px;">MEMORY: Supabase Cloud</div>
    </section>
    <section class="panel center-stage">
        <div class="core" id="arc-core"></div>
        <div id="log">
            <div class="msg-jarvis">J.A.R.V.I.S.: Cloud core online, Sir. Ready for deployment.</div>
        </div>
    </section>
    <section class="panel">
        <div class="panel-title">SYSTEM STATUS</div>
        <div style="font-size:0.85rem; color:#ffaa00; line-height:1.5;">- Zero local files.<br>- Accessible on any OS.<br>- Browser speech voice active.</div>
    </section>
    <footer>
        <button class="btn" id="mic-btn">MIC: ON</button>
        <input type="text" id="input" placeholder="Type command..." />
    </footer>
    <script>
        const cam = document.getElementById('cam');
        const input = document.getElementById('input');
        const log = document.getElementById('log');
        const arcCore = document.getElementById('arc-core');
        navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } }).then(s => cam.srcObject = s).catch(() => {});

        function speak(text) {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                const u = new SpeechSynthesisUtterance(text);
                u.rate = 1.05; u.pitch = 0.95;
                const voices = window.speechSynthesis.getVoices();
                const uk = voices.find(v => v.lang === 'en-GB' || v.name.includes('UK') || v.name.includes('British'));
                if (uk) u.voice = uk;
                u.onstart = () => arcCore.style.transform = "scale(1.18)";
                u.onend = () => arcCore.style.transform = "scale(1)";
                window.speechSynthesis.speak(u);
            }
        }

        async function sendCommand(text) {
            if (!text.trim()) return;
            log.innerHTML += `<div class="msg-user">&gt; ${text}</div>`;
            log.scrollTop = log.scrollHeight;
            const res = await fetch('/execute', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text }) });
            const data = await res.json();
            log.innerHTML += `<div class="msg-jarvis">J.A.R.V.I.S.: ${data.response}</div>`;
            log.scrollTop = log.scrollHeight;
            speak(data.response);
        }

        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') { const v = input.value; input.value = ''; sendCommand(v); }
        });
    </script>
</body>
</html>
    """
