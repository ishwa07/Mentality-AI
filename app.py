import requests
import speech_recognition as sr
import pyttsx3
from PIL import Image
import gradio as gr
import threading
import queue

# ================= CONFIG =================
LANGFLOW_API_KEY = "sk-NhQUJO4U67Q3ELoNudtOFB7zMEh4aKV1ED17B4K0x7s"
LANGFLOW_URL = "http://localhost:7860/api/v1/run/256c8204-b360-449c-a3f9-fd1437594502"

# ================= TTS =================
tts_queue = queue.Queue()

def tts_worker():
    engine = pyttsx3.init()
    while True:
        text = tts_queue.get()
        if text is None:
            break
        engine.say(text)
        engine.runAndWait()
        tts_queue.task_done()

threading.Thread(target=tts_worker, daemon=True).start()

def speak(text):
    if text:
        tts_queue.put(text)

# ================= VOICE INPUT =================
def listen():
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, timeout=4, phrase_time_limit=8)
        return r.recognize_google(audio)
    except:
        return ""

# ================= LANGFLOW =================
def call_langflow(message):
    payload = {
        "input_value": message,
        "input_type": "chat",
        "output_type": "chat"
    }
    headers = {
        "Content-Type": "application/json",
        "x-api-key": LANGFLOW_API_KEY
    }
    try:
        res = requests.post(LANGFLOW_URL, json=payload, headers=headers, timeout=20)
        data = res.json()
        return data["outputs"][0]["outputs"][0]["results"]["message"]["text"]
    except:
        return "I'm having trouble connecting right now."

# ================= IMAGE =================
def generate_image(prompt):
    return Image.new("RGB", (512, 512), "#E0F7FA")

# ================= CHAT =================
def chat_fn(message, history, mode):
    if mode == "voice":
        message = listen()
        if not message:
            return history, None, ""

    reply = call_langflow(message)
    speak(reply)

    history = history + [(message, reply)]
    return history, None, ""

# ================= VISUAL =================
def visualize(prompt):
    return generate_image(prompt)

# ================= UI =================
custom_css = """
body { background-color: #f8fafc; }
"""

with gr.Blocks(title="Mentality AI", css=custom_css) as demo:

    gr.HTML("""
    <div style="text-align:center">
        <h1 style="color:#14b8a6">🧠 Mentality Ai</h1>
        <p>Your peaceful mental health companion</p>
    </div>
    """)

    with gr.Tabs():

        # ================= HOME =================
        with gr.Tab("🏠 Home"):
            gr.HTML("""
            <div style="background:#e6fffa;padding:40px;border-radius:20px;text-align:center">
                <h2>Welcome to Mentality Ai</h2>
                <p>We listen, understand and help you find calm through AI and serene visualizations.</p>
            </div>

            <div style="display:flex;gap:20px;justify-content:center;margin-top:30px">
                <div style="background:white;padding:20px;border-radius:15px;width:250px;text-align:center">
                    <h3>🧠 Empathic Chat</h3>
                    <p>Talk freely. AI listens with empathy.</p>
                </div>
                <div style="background:white;padding:20px;border-radius:15px;width:250px;text-align:center">
                    <h3>🎨 Visual Serenity</h3>
                    <p>Generate calming visuals.</p>
                </div>
                <div style="background:white;padding:20px;border-radius:15px;width:250px;text-align:center">
                    <h3>🎤 Voice Interaction</h3>
                    <p>Speak naturally with AI.</p>
                </div>
            </div>

            <div style="margin-top:40px;text-align:center">
                <h3>Meet the Creators</h3>
                <p>Varun Bhagwat · Arjun · Ishwar</p>
                <p>📧 varunbhagwat948@gmail.com</p>
            </div>
            """)

        # ================= CHAT =================
        with gr.Tab("💬 Chat"):
            chatbot = gr.Chatbot(height=450, label="Conversation")
            msg = gr.Textbox(placeholder="Type your thoughts here...")
            image_out = gr.Image(visible=False)

            with gr.Row():
                send = gr.Button("Send", variant="primary")
                voice = gr.Button("🎤 Speak")

            send.click(
                chat_fn,
                inputs=[msg, chatbot, gr.State("text")],
                outputs=[chatbot, image_out, msg]
            )

            msg.submit(
                chat_fn,
                inputs=[msg, chatbot, gr.State("text")],
                outputs=[chatbot, image_out, msg]
            )

            voice.click(
                chat_fn,
                inputs=[gr.State(""), chatbot, gr.State("voice")],
                outputs=[chatbot, image_out, msg]
            )

        # ================= VISUAL =================
        with gr.Tab("🎨 Visualization"):
            gr.Markdown("### Visual Serenity")
            prompt = gr.Textbox(placeholder="A calm ocean at sunset...")
            gen = gr.Button("Generate")
            img = gr.Image()

            gen.click(visualize, inputs=prompt, outputs=img)

# ================= RUN =================
demo.launch(server_port=7880)
