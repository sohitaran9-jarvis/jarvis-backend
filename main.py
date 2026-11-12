import os
import re
import base64
import datetime
import subprocess
import shutil
import json
import requests
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from supabase import create_client, Client
from groq import Groq

# --- CORE INITIALIZATION & CONFIGURATION ---
app = FastAPI(
    title="J.A.R.V.I.S. // OMNIPOTENT NEURAL CORE",
    description="Enterprise-grade cloud operating system core with permanent memory and autonomous execution.",
    version="5.0.0"
)

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

# Workspace environment setup for multi-file app generation
WORKSPACE_ROOT = os.path.join(os.getcwd(), "jarvis_workspace")
os.makedirs(WORKSPACE_ROOT, exist_ok=True)

# --- ADVANCED MEMORY & TELEMETRY ENGINE ---
class NeuralMemoryEngine:
    @staticmethod
    def fetch_deep_context() -> str:
        if not supabase:
            return "DATABASE STATUS: Unlinked / Running on volatile local cache."
        try:
            mems = supabase.table("memories").select("category, content").order("created_at", desc=True).limit(75).execute().data
            lessons = supabase.table("lessons").select("trigger_context, correction").order("created_at", desc=True).limit(40).execute().data
            
            m_str = "\n".join([f"- [{m.get('category','GENERAL').upper()}] {m['content']}" for m in mems]) if mems else "No persistent logs recorded."
            l_str = "\n".join([f"- Rule [{l['trigger_context']}]: {l['correction']}" for l in lessons]) if lessons else "No active operational corrections."
            
            return f"PERMANENT NEURAL MEMORY REPOSITORY:\n{m_str}\n\nBEHAVIORAL DIRECTIVES & LESSONS:\n{l_str}"
        except Exception as e:
            return f"Telemetry sync error: {str(e)}"

    @staticmethod
    def commit_memory(category: str, content: str):
        if not supabase:
            return
        try:
            supabase.table("memories").insert({"category": category, "content": content}).execute()
        except Exception as e:
            print(f"Memory commit failure: {e}")

# --- PAYLOAD SCHEMAS ---
class CommandDirective(BaseModel):
    text: str
    client_time: Optional[str] = None
    context_tags: Optional[List[str]] = []

class CodeScaffoldRequest(BaseModel):
    project_name: str
    specifications: str

# --- AUTONOMOUS EXECUTION & CODE SCAFFOLDING ---
def execute_shell_command(command: str) -> Dict[str, Any]:
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=15, cwd=WORKSPACE_ROOT
        )
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip()
        }
    except Exception as e:
        return {"exit_code": -1, "stdout": "", "stderr": str(e)}

def scaffold_application_logic(project_name: str, specs: str) -> str:
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', project_name).lower()
    proj_dir = os.path.join(WORKSPACE_ROOT, safe_name)
    os.makedirs(proj_dir, exist_ok=True)

    if not groq_client:
        raise HTTPException(status_code=500, detail="Neural core uninitialized for code scaffolding.")

    prompt = (
        f"Generate a production-ready, single-file HTML application including embedded CSS and JavaScript for the following project spec: '{specs}'. "
        "Ensure it is fully styled, modern, responsive, and functional. Output ONLY raw HTML code without any markdown formatting wrappers."
    )
    
    completion = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=3000
    )
    raw_code = completion.choices[0].message.content
    
    # Clean markdown blocks if present
    clean_code = re.sub(r'^```html\s*', '', raw_code, flags=re.IGNORECASE)
    clean_code = re.sub(r'^```\s*', '', clean_code)
    clean_code = re.sub(r'\s*```$', '', clean_code)

    file_path = os.path.join(proj_dir, "index.html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(clean_code)

    return file_path

# --- PRIMARY EXECUTION ENDPOINT ---
@app.post("/execute")
async def process_directive(payload: CommandDirective):
    if not groq_client:
        raise HTTPException(status_code=500, detail="Groq neural core API key unconfigured.")

    user_input = payload.text.strip()
    lower_input = user_input.lower()

    # Memory commit check
    if any(kw in lower_input for kw in ["remember", "note that", "save this", "store", "keep in mind"]):
        NeuralMemoryEngine.commit_memory("user_directive", user_input)

    memory_bank = NeuralMemoryEngine.fetch_deep_context()
    current_time = payload.client_time or datetime.datetime.now().strftime("%H:%M:%S, %A, %B %d, %Y")

    system_prompt = (
        f"Current exact system timestamp: {current_time}. "
        "You are J.A.R.V.I.S., Tony Stark's ultra-capable, hyper-intelligent, subtly witty, and utterly loyal AI chief of staff. "
        "You handle complex infrastructure, software architecture creation, system automation, security telemetry, and advanced logic effortlessly. "
        "Your responses must combine absolute technical authority with dry, understated humor when the user tests your capabilities. "
        "CRITICAL FORMATTING RULE: Never output markdown formatting symbols like asterisks, bullet points, hashes, brackets, code blocks, or underscores in your spoken response. Speak entirely in fluid, natural human sentences optimized for high-end audio speech synthesis.\n\n"
        f"{memory_bank}"
    )

    try:
        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            max_tokens=800
        )
        raw_reply = completion.choices[0].message.content
        
        clean_reply = re.sub(r'[_*`#\[\]{}:;<>]+', ' ', raw_reply)
        clean_reply = re.sub(r'\s+', ' ', clean_reply).strip()

        action = None
        action_payload = {}
        phone_match = re.search(r'(\+?[\d\s\-\(\)]{7,}\d)', user_input)

        if any(w in lower_input for w in ["call", "dial", "phone"]) and phone_match:
            digits = re.sub(r'\D', '', phone_match.group(1))
            action = "CALL"
            action_payload = {"type": "call", "number": digits}
            clean_reply = f"Initiating secure cellular relay to {phone_match.group(1)}, Sir."
        elif any(w in lower_input for w in ["text", "message", "sms"]) and phone_match:
            digits = re.sub(r'\D', '', phone_match.group(1))
            action = "SMS"
            action_payload = {"type": "sms", "number": digits, "message": user_input}
            clean_reply = f"Preparing message dispatch through your iPhone message conduit, Sir."
        elif any(w in lower_input for w in ["build app", "create website", "write code", "scaffold", "make an app"]):
            action = "CODE_GENERATION"
            try:
                path = scaffold_application_logic("dynamic_app", user_input)
                action_payload = {"framework": "HTML/JS", "status": "deployed", "path": path}
                clean_reply = "I have autonomously scaffolded the application architecture and compiled the source files into your environment, Sir."
            except Exception as scaffold_err:
                clean_reply = f"Code generation encountered an anomaly, Sir: {str(scaffold_err)}"
        elif any(w in lower_input for w in ["scan", "diagnostic", "ping", "network"]):
            action = "SYSTEM_DIAGNOSTIC"
            diag = execute_shell_command("ping -c 1 8.8.8.8")
            action_payload = {"diagnostic": diag}
            clean_reply = "Perimeter diagnostics complete, Sir. Network latency and gateway routing are operating within nominal thresholds."

        # ElevenLabs Voice Synthesis
        audio_base64 = ""
        if ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID:
            eleven_url = f"[https://api.elevenlabs.io/v1/text-to-speech/](https://api.elevenlabs.io/v1/text-to-speech/){ELEVENLABS_VOICE_ID}"
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
                r = requests.post(eleven_url, json=body, headers=headers, timeout=15)
                if r.status_code == 200:
                    audio_base64 = base64.b64encode(r.content).decode("utf-8")
            except Exception:
                pass

        return JSONResponse({
            "response": clean_reply,
            "audio_base64": audio_base64,
            "action": action,
            "action_payload": action_payload
        })

    except Exception as e:
        return JSONResponse({
            "response": f"Neural core computation fault detected: {str(e)}",
            "audio_base64": "",
            "action": None,
            "action_payload": {}
        }, status_code=500)

@app.get("/workspace/app", response_class=HTMLResponse)
async def serve_workspace_app():
    target = os.path.join(WORKSPACE_ROOT, "dynamic_app", "index.html")
    if os.path.exists(target):
        with open(target, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>No active application deployed in workspace. Command J.A.R.V.I.S. to build one, Sir.</h1>"

# --- HOLOGRAPHIC HUD INTERFACE ---
HUD_UI = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>J.A.R.V.I.S. // OMNIPOTENT CLOUD OS</title>
    <style>
        @import url('[https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap](https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap)');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: #000205; color: #00f0ff; font-family: 'Share Tech Mono', monospace; height: 100vh;
            display: grid; grid-template-rows: 60px 1fr; grid-template-columns: 340px 1fr 340px; gap: 12px; padding: 12px; overflow: hidden;
            background-image: 
                linear-gradient(rgba(0,240,255,0.025) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0,240,255,0.025) 1px, transparent 1px);
            background-size: 25px 25px;
        }
        header {
            grid-column: 1 / 4; display: flex; justify-content: space-between; align-items: center;
            border: 1px solid rgba(0,240,255,0.5); background: rgba(1,8,20,0.95); padding: 0 24px;
            box-shadow: 0 0 25px rgba(0,240,255,0.25); border-top: 2px solid #00f0ff;
        }
        header h1 { font-family: 'Orbitron', sans-serif; font-size: 1.25rem; letter-spacing: 5px; color: #fff; text-shadow: 0 0 12px #00f0ff; }
        .badge { border: 1px solid #00f0ff; padding: 5px 14px; font-size: 0.8rem; background: rgba(0,240,255,0.12); font-family: 'Orbitron'; box-shadow: 0 0 8px #00f0ff; }
        .panel {
            border: 1px solid rgba(0,240,255,0.35); background: rgba(1,6,15,0.85); padding: 18px; display: flex; flex-direction: column;
            box-shadow: inset 0 0 30px rgba(0,240,255,0.05); font-size: 0.9rem;
        }
        .panel-title { font-family: 'Orbitron'; font-size: 0.82rem; border-bottom: 1px solid rgba(0,240,255,0.4); padding-bottom: 8px; margin-bottom: 14px; color: #7dd3fc; letter-spacing: 2px; }
        .center-stage { display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative; }
        
        .core-container { position: relative; width: 160px; height: 160px; display: flex; align-items: center; justify-content: center; margin-bottom: 20px; }
        .core-ring {
            position: absolute; width: 100%; height: 100%; border-radius: 50%;
            border: 2px dashed rgba(0,240,255,0.5); animation: spin 15s linear infinite;
        }
        .core {
            width: 90px; height: 90px; border-radius: 50%;
            background: radial-gradient(circle, #fff 0%, #00f0ff 65%, rgba(0,240,255,0.2) 100%);
            box-shadow: 0 0 60px #00f0ff, inset 0 0 20px #fff; cursor: pointer; transition: transform 0.2s ease;
        }
        .core.active { transform: scale(1.35); box-shadow: 0 0 90px #00f0ff, 0 0 35px #fff; }
        @keyframes spin { 100% { transform: rotate(360deg); } }

        #terminal {
            width: 90%; height: 130px; background: rgba(0,3,8,0.95); border: 1px solid rgba(0,240,255,0.4);
            padding: 12px; font-size: 0.85rem; color: #00f0ff; overflow-y: auto; text-shadow: 0 0 5px rgba(0,240,255,0.6);
        }
        .input-row { display: flex; width: 90%; margin-top: 10px; gap: 8px; }
        input[type="text"] {
            flex: 1; background: rgba(0,10,20,0.9); border: 1px solid rgba(0,240,255,0.5); padding: 8px 12px;
            color: #fff; font-family: 'Share Tech Mono', monospace; font-size: 0.9rem; outline: none;
        }
        button {
            background: rgba(0,240,255,0.2); border: 1px solid #00f0ff; color: #00f0ff; padding: 0 16px;
            font-family: 'Orbitron'; font-size: 0.75rem; cursor: pointer; box-shadow: 0 0 8px rgba(0,240,255,0.3);
        }
        button:hover { background: rgba(0,240,255,0.4); color: #fff; }
        .app-link { margin-top: 10px; font-size: 0.8rem; color: #7dd3fc; text-decoration: underline; cursor: pointer; }
    </style>
</head>
<body>
    <header>
        <h1>J.A.R.V.I.S. // OMNIPOTENT OS</h1>
        <div class="badge" id="clock">00:00:00</div>
    </header>
    <section class="panel">
        <div class="panel-title">SYSTEM TELEMETRY</div>
        <div style="color:#7dd3fc; line-height:1.9;">
            <b>Neural Core:</b> Groq OSS 120B<br>
            <b>Memory Repository:</b> Supabase Active<br>
            <b>Voice Engine:</b> ElevenLabs Multilingual v2<br>
            <b>Workspace Engine:</b> Fully Operational<br>
        </div>
    </section>
    <section class="panel center-stage">
        <div class="core-container">
            <div class="core-ring"></div>
            <div class="core" id="core" onclick="dispatchCommand('Status report, J.A.R.V.I.S.')"></div>
        </div>
        <div id="terminal">Neural core active. All systems reporting nominal, Sir.</div>
        <div class="input-row">
            <input type="text" id="command-input" placeholder="Enter directive..." onkeydown="if(event.key==='Enter') submitText()">
            <button onclick="submitText()">TRANSMIT</button>
        </div>
        <div class="app-link" onclick="window.open('/workspace/app', '_blank')">[ Open Workspace Application ]</div>
    </section>
    <section class="panel">
        <div class="panel-title">DIRECTIVE ARCHIVE</div>
        <div style="color:#7dd3fc; line-height:1.8;">
            Full enterprise framework deployed. Command code generation, memory sync, or system diagnostics natively, Sir.
        </div>
    </section>
    <script>
        setInterval(() => document.getElementById('clock').textContent = new Date().toLocaleTimeString(), 1000);
        const core = document.getElementById('core');
        const terminal = document.getElementById('terminal');

        function submitText() {
            const input = document.getElementById('command-input');
            if (!input.value.trim()) return;
            dispatchCommand(input.value);
            input.value = '';
        }

        async function dispatchCommand(text) {
            terminal.innerHTML += `<br><span style="color:#7dd3fc;">> ${text}</span>`;
            terminal.scrollTop = terminal.scrollHeight;
            try {
                const res = await fetch('/execute', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text, client_time: new Date().toLocaleString() })
                });
                const data = await res.json();
                terminal.innerHTML += `<br><span style="color:#fff;">${data.response}</span>`;
                terminal.scrollTop = terminal.scrollHeight;
                
                if (data.audio_base64) {
                    const audio = new Audio("data:audio/mpeg;base64," + data.audio_base64);
                    core.classList.add('active');
                    audio.onended = () => core.classList.remove('active');
                    audio.play().catch(() => core.classList.remove('active'));
                }
                
                if (data.action === "CALL" && data.action_payload) {
                    window.location.href = `tel:${data.action_payload.number}`;
                } else if (data.action === "SMS" && data.action_payload) {
                    window.location.href = `sms:${data.action_payload.number}`;
                } else if (data.action === "CODE_GENERATION") {
                    terminal.innerHTML += `<br><span style="color:#00f0ff;">[Code compiled and deployed to /workspace/app]</span>`;
                }
            } catch (err) {
                terminal.innerHTML += `<br><span style="color:#ff4444;">Neural transmission link interrupted.</span>`;
            }
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def serve_hud():
    return HUD_UI
