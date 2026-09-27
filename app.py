import streamlit as st
import fitz
import io
import urllib.parse
import random
import time
from PIL import Image
from docx import Document
from pdf2docx import Converter

st.set_page_config(page_title="Marco AI", layout="wide", page_icon="🧠")

# --- CSS BONITO TIPO GEMINI CON CEREBRO ---
st.markdown("""
<style>
.stApp { background: #0f0f13; }
.header { text-align:center; padding: 20px 0 10px 0; }
.header h1 { font-size: 3rem; margin:0; }
.header h1 span { background: linear-gradient(90deg,#FF9A8B,#FF6A88,#D66DFF,#6A5AF9); -webkit-background-clip:text; -webkit-text-fill-color:transparent; font-weight:900; }
.brain { font-size: 4rem; animation: float 3s ease-in-out infinite; }
@keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-8px)} }
.card { background: #1b1b24; border:1px solid #2c2c3d; border-radius:18px; padding:16px; text-align:center; }
.card:hover{ border-color:#D66DFF; box-shadow:0 0 20px #d66dff33; }
div[data-testid="stChatMessage"]{ background:#181822; border:1px solid #2a2a3e; border-radius:16px; }
</style>
<div class="header">
<div class="brain">🧠🦙</div>
<h1><span>Marco - Tu Cerebro IA</span></h1>
<p style="color:#888;">Pregúntame lo que sea, te respondo Y te creo la imagen al mismo tiempo</p>
</div>
""", unsafe_allow_html=True)

api_key = st.secrets.get("GROQ_API_KEY", "")

if 'chat' not in st.session_state:
    st.session_state.chat = []

# --- INPUT ARRIBA CON ENTER ---
with st.form("form_marco", clear_on_submit=True):
    c1, c2 = st.columns([5,1])
    with c1:
        prompt = st.text_input("prompt_input", placeholder="💬 Escribe y presiona ENTER: ej. que es una llama y crea una imagen de una llama", label_visibility="collapsed")
    with c2:
        enviar = st.form_submit_button("Enviar 🚀", type="primary", use_container_width=True)

def generar_imagen_url(texto):
    texto_en = texto
    if "llama" in texto.lower(): texto_en = "cute fluffy llama alpaca smiling in Andes mountains, photorealistic, ultra detailed, 8k"
    if "oveja" in texto.lower(): texto_en = "cute fluffy white sheep lamb in green field with flowers, photorealistic"
    encoded = urllib.parse.quote(texto_en)
    seed = random.randint(1, 99999999)
    # Usamos turbo que es más estable que flux y no da rayas
    return f"https://image.pollinations.ai/prompt/{encoded}?model=turbo&seed={seed}&width=1024&height=1024&nologo=true&enhance=false&nofeed=true"

def responder_texto(p):
    if not api_key:
        return "Soy Marco 🧠🦙. Para explicarte necesito tu GROQ_API_KEY en Secrets. Pero igual te genero la imagen."
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        # UN SOLO CEREBRO ES SUFICIENTE: llama-3.1-8b-instant es el más estable
        r = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role":"system","content":"Te llamas Marco, tienes un cerebro 🧠 en el hombro, eres boliviano, amigable, explicas breve y divertido. Si te piden imagen, di que la estás generando."},
                {"role":"user","content":p}
            ],
            temperature=0.7
        )
        return r.choices[0].message.content
    except Exception as e:
        return f"Soy Marco, tuve un error de texto: {e}. Pero igual te genero la imagen."

if enviar and prompt:
    st.session_state.chat.append({"role":"user","content":prompt})

    quiere_texto = any(w in prompt.lower() for w in ["que es","que","quien","como","cuando","donde","explica","info"])
    quiere_imagen = any(w in prompt.lower() for w in ["imagen","foto","crea","dibuja","genera","llama","oveja","pug","gato"])

    # SI PIDE LAS DOS COSAS -> HACE LAS DOS
    if quiere_texto and quiere_imagen:
        txt = responder_texto(prompt)
        st.session_state.chat.append({"role":"assistant","content":txt})
        url = generar_imagen_url(prompt)
        st.session_state.chat.append({"role":"assistant","content":f"IMG::{url}::{prompt}"})
    elif quiere_imagen:
        url = generar_imagen_url(prompt)
        st.session_state.chat.append({"role":"assistant","content":f"IMG::{url}::{prompt}"})
    else:
        txt = responder_texto(prompt)
        st.session_state.chat.append({"role":"assistant","content":txt})

    st.rerun()

# --- CHAT ---
for m in st.session_state.chat:
    with st.chat_message(m["role"], avatar="🧠" if m["role"]=="assistant" else "👤"):
        if m["content"].startswith("IMG::"):
            _, url, cap = m["content"].split("::",2)
            st.write(f"**Marco te generó:** {cap}")
            # Truco para evitar rayas: si falla, reintenta
            try:
                st.image(url, use_container_width=True)
            except:
                st.warning("Pollinations está saturado, reintentando...")
                time.sleep(1)
                st.image(url + f"&r={random.randint(0,9999)}", use_container_width=True)
        else:
            st.write(m["content"])

st.divider()
st.markdown("#### 🛠️ Caja de herramientas bonita")

if 'files' not in st.session_state: st.session_state.files=[]
up = st.file_uploader("Arrastra PDFs / Word / JPG", type=["pdf","docx","jpg","jpeg","png"], accept_multiple_files=True)
if up: st.session_state.files = up

tools = [("🔗","Unir PDF","unir"),("✂️","Dividir","dividir"),("🗜️","Comprimir","comprimir"),("📄","PDF a Word","pdf2word"),
         ("📝","Word a PDF","word2pdf"),("🖼️","JPG a PDF","jpg2pdf"),("🎨","PDF a JPG","pdf2jpg"),("📖","Extraer Texto","texto")]

cols = st.columns(4)
sel=None
for i,(ic,nm,key) in enumerate(tools):
    with cols[i%4]:
        if st.button(f"{ic}\n{nm}", key=key, use_container_width=True):
            sel=key

if sel and st.session_state.files:
    try:
        if sel=="unir":
            out=fitz.open()
            for f in st.session_state.files:
                if f.name.lower().endswith(".pdf"): out.insert_pdf(fitz.open(stream=f.getvalue(), filetype="pdf"))
            buf=io.BytesIO(); out.save(buf)
            st.download_button("⬇️ Descargar Unido", buf.getvalue(), "unido.pdf", type="primary", use_container_width=True)
        if sel=="comprimir":
            for f in st.session_state.files:
                if f.name.lower().endswith(".pdf"):
                    doc=fitz.open(stream=f.getvalue(), filetype="pdf")
                    b=io.BytesIO(); doc.save(b, garbage=4, deflate=True)
                    st.download_button(f"⬇️ {f.name}", b.getvalue(), f"comp_{f.name}", type="primary", use_container_width=True)
        if sel=="jpg2pdf":
            imgs=[Image.open(io.BytesIO(f.getvalue())).convert("RGB") for f in st.session_state.files if "image" in f.type or f.name.endswith(("jpg","jpeg","png"))]
            if imgs:
                buf=io.BytesIO(); imgs[0].save(buf,"PDF",save_all=True,append_images=imgs[1:])
                st.download_button("⬇️ PDF de Imágenes", buf.getvalue(), "imagenes.pdf", type="primary", use_container_width=True)
        if sel=="pdf2jpg":
            for f in st.session_state.files:
                if f.name.lower().endswith(".pdf"):
                    doc=fitz.open(stream=f.getvalue(), filetype="pdf")
                    for i,pg in enumerate(doc):
                        pix=pg.get_pixmap(dpi=150)
                        st.image(pix.tobytes("png"), caption=f"Pág {i+1}", use_container_width=True)
        if sel=="texto":
            full=""
            for f in st.session_state.files:
                if f.name.lower().endswith(".pdf"):
                    doc=fitz.open(stream=f.getvalue(), filetype="pdf")
                    for p in doc: full+=p.get_text()+"\n"
            st.text_area("Texto", full, height=250)
            st.download_button("⬇️ Descargar txt", full, "texto.txt", use_container_width=True)
        if sel=="dividir":
            for f in st.session_state.files:
                if f.name.lower().endswith(".pdf"):
                    doc=fitz.open(stream=f.getvalue(), filetype="pdf")
                    for i in range(len(doc)):
                        s=fitz.open(); s.insert_pdf(doc,from_page=i,to_page=i); b=io.BytesIO(); s.save(b)
                        st.download_button(f"⬇️ Pág {i+1}", b.getvalue(), f"{f.name}_{i+1}.pdf", use_container_width=True)
        if sel=="word2pdf":
            for f in st.session_state.files:
                if f.name.lower().endswith(".docx"):
                    docx=Document(io.BytesIO(f.getvalue())); pdf=fitz.open(); page=pdf.new_page(); y=50
                    for p in docx.paragraphs:
                        if p.text.strip():
                            page.insert_text((50,y), p.text[:1000]); y+=20
                            if y>750: page=pdf.new_page(); y=50
                    buf=io.BytesIO(); pdf.save(buf)
                    st.download_button(f"⬇️ {f.name}.pdf", buf.getvalue(), f"{f.name}.pdf", type="primary", use_container_width=True)
        if sel=="pdf2word":
            for f in st.session_state.files:
                if f.name.lower().endswith(".pdf"):
                    open("temp.pdf","wb").write(f.getvalue())
                    cv=Converter("temp.pdf"); cv.convert("temp.docx"); cv.close()
                    with open("temp.docx","rb") as d:
                        st.download_button(f"⬇️ {f.name}.docx", d.read(), f"{f.name}.docx", type="primary", use_container_width=True)
        st.success("Listo 🧠✨")
    except Exception as e:
        st.error(f"Error: {e}")

st.caption("🧠 Marco usa 1 solo cerebro: llama-3.1-8b-instant (el más estable). No necesitas crear más prompts.")
