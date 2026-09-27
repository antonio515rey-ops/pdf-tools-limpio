import streamlit as st
import fitz
import io
import urllib.parse
import random
from PIL import Image
from docx import Document
from pdf2docx import Converter

st.set_page_config(page_title="Marco AI + PDF", layout="wide", page_icon="🦙")

# --- ESTILO BONITO ---
st.markdown("""
<style>
.big-title { font-size: 2.5rem; font-weight: 900; text-align:center; background: linear-gradient(90deg,#ff6a00,#ee0979,#8a2be2); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.sub { text-align:center; color:#aaa; margin-bottom:15px; }
.stTextInput input { border-radius:12px!important; height:50px; font-size:16px; }
.tool-btn { background: linear-gradient(135deg,#1f1f2e,#2a2a40)!important; border:1px solid #3a3a5c!important; border-radius:15px!important; height:110px; color:white!important; }
.tool-btn:hover { border-color:#8a2be2!important; }
div[data-testid="stChatMessage"]{ border-radius:15px; border:1px solid #2a2a3e; background:#161a27; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="big-title">🦙 Marco - Tu IA + PDF Lover</p>', unsafe_allow_html=True)
st.markdown('<p class="sub">Pregúntame, pídeme imágenes y edita PDFs</p>', unsafe_allow_html=True)

api_key = st.secrets.get("GROQ_API_KEY", "")

if 'chat' not in st.session_state:
    st.session_state.chat = []

# --- INPUT ARRIBA QUE FUNCIONA CON ENTER ---
with st.form("marco_form", clear_on_submit=True):
    col1, col2 = st.columns([6,1])
    with col1:
        prompt = st.text_input(" ", placeholder="💬 Escribe aquí y dale ENTER... Ej: que es una llama y crea una imagen de una llama", label_visibility="collapsed")
    with col2:
        enviar = st.form_submit_button("➤ Enviar", use_container_width=True, type="primary")

if enviar and prompt:
    st.session_state.chat.append({"role": "user", "content": prompt})

    es_imagen = any(w in prompt.lower() for w in ["crea", "imagen", "dibuja", "foto", "genera", "llama", "oveja", "pug", "gato", "perro"])

    if es_imagen:
        # Marco traduce a inglés para que salga perfecto
        prompt_en = prompt
        if "llama" in prompt.lower(): prompt_en = "cute fluffy llama alpaca in andes mountains, photorealistic, adorable, highly detailed"
        if "oveja" in prompt.lower(): prompt_en = "cute fluffy white sheep lamb in green field, photorealistic"

        encoded = urllib.parse.quote(prompt_en)
        seed = random.randint(1, 9999999)
        img_url = f"https://image.pollinations.ai/prompt/{encoded}?model=flux&seed={seed}&width=1024&height=1024&nologo=true&enhance=true"
        st.session_state.chat.append({"role": "assistant", "content": f"IMG::{img_url}::{prompt}::Marco te generó esto 👇"})
    else:
        if not api_key:
            st.session_state.chat.append({"role": "assistant", "content": "Soy Marco 🦙, pero falta tu GROQ_API_KEY en Secrets. Para imágenes no necesito key, solo pide 'crea una imagen de...'"})
        else:
            try:
                from groq import Groq
                client = Groq(api_key=api_key)
                resp = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role":"system","content":"Te llamas Marco, eres una IA amigable boliviana, respondes corto y divertido."},
                              {"role":"user","content":prompt}]
                )
                ans = resp.choices[0].message.content
                st.session_state.chat.append({"role": "assistant", "content": ans})
            except Exception as e:
                st.session_state.chat.append({"role": "assistant", "content": f"Soy Marco, hubo un error: {e}. Intenta 'crea una imagen de una llama'"})

# --- HISTORIAL ---
for m in reversed(st.session_state.chat):
    with st.chat_message(m["role"], avatar="🦙" if m["role"]=="assistant" else "😎"):
        if m["content"].startswith("IMG::"):
            _, url, caption, extra = m["content"].split("::")
            st.write(f"**{extra}** - *{caption}*")
            st.image(url, use_container_width=True)
        else:
            st.write(m["content"])

st.divider()
st.markdown("### 🎨 Herramientas PDF Bonitas")

if 'files' not in st.session_state: st.session_state.files = []

up = st.file_uploader("📁 Arrastra PDFs / Word / JPG aquí", type=["pdf","docx","jpg","jpeg","png"], accept_multiple_files=True)
if up: st.session_state.files = up

tools = [
    ("🔗", "Unir PDF", "unir", "#ff6a00"),
    ("✂️", "Dividir PDF", "dividir", "#ee0979"),
    ("🗜️", "Comprimir", "comprimir", "#8a2be2"),
    ("📄", "PDF a Word", "pdf2word", "#00c9ff"),
    ("📝", "Word a PDF", "word2pdf", "#92fe9d"),
    ("🖼️", "JPG a PDF", "jpg2pdf", "#f7971e"),
    ("🎨", "PDF a JPG", "pdf2jpg", "#00f260"),
    ("📖", "Extraer Texto", "texto", "#ff5e62"),
]

cols = st.columns(4)
selected = None
for i, (icon, name, key, color) in enumerate(tools):
    with cols[i % 4]:
        if st.button(f"{icon}\n{name}", key=key, use_container_width=True):
            selected = key

if selected and st.session_state.files:
    try:
        if selected == "unir":
            out = fitz.open()
            for f in st.session_state.files:
                if f.name.lower().endswith(".pdf"): out.insert_pdf(fitz.open(stream=f.getvalue(), filetype="pdf"))
            buf = io.BytesIO(); out.save(buf)
            st.download_button("⬇️ Descargar Unido", buf.getvalue(), "unido.pdf", "application/pdf", type="primary", use_container_width=True)
        if selected == "dividir":
            for f in st.session_state.files:
                if f.name.lower().endswith(".pdf"):
                    doc = fitz.open(stream=f.getvalue(), filetype="pdf")
                    for i in range(len(doc)):
                        single = fitz.open(); single.insert_pdf(doc, from_page=i, to_page=i)
                        b = io.BytesIO(); single.save(b)
                        st.download_button(f"⬇️ Página {i+1} {f.name}", b.getvalue(), f"{f.name}_p{i+1}.pdf", use_container_width=True)
        if selected == "comprimir":
            for f in st.session_state.files:
                if f.name.lower().endswith(".pdf"):
                    doc = fitz.open(stream=f.getvalue(), filetype="pdf")
                    b = io.BytesIO(); doc.save(b, garbage=4, deflate=True)
                    st.download_button(f"⬇️ Comprimido {f.name}", b.getvalue(), f"comp_{f.name}", type="primary", use_container_width=True)
        if selected == "jpg2pdf":
            imgs = [Image.open(io.BytesIO(f.getvalue())).convert("RGB") for f in st.session_state.files if "image" in f.type or f.name.lower().endswith(("jpg","jpeg","png"))]
            if imgs:
                buf = io.BytesIO(); imgs[0].save(buf, "PDF", save_all=True, append_images=imgs[1:])
                st.download_button("⬇️ Descargar PDF", buf.getvalue(), "imagenes.pdf", type="primary", use_container_width=True)
        if selected == "pdf2jpg":
            for f in st.session_state.files:
                if f.name.lower().endswith(".pdf"):
                    doc = fitz.open(stream=f.getvalue(), filetype="pdf")
                    for i, page in enumerate(doc):
                        pix = page.get_pixmap(dpi=150)
                        st.image(pix.tobytes("png"), caption=f"{f.name} Pág {i+1}", use_container_width=True)
        if selected == "texto":
            full=""
            for f in st.session_state.files:
                if f.name.lower().endswith(".pdf"):
                    doc = fitz.open(stream=f.getvalue(), filetype="pdf")
                    for p in doc: full+=p.get_text()+"\n"
            st.text_area("Texto extraído", full, height=300)
            st.download_button("⬇️ Descargar texto", full, "texto.txt", use_container_width=True)
        if selected == "word2pdf":
            for f in st.session_state.files:
                if f.name.lower().endswith(".docx"):
                    docx = Document(io.BytesIO(f.getvalue()))
                    pdf = fitz.open(); page = pdf.new_page(); y=50
                    for p in docx.paragraphs:
                        if p.text.strip():
                            page.insert_text((50,y), p.text[:1000]); y+=20
                            if y>750: page=pdf.new_page(); y=50
                    buf = io.BytesIO(); pdf.save(buf)
                    st.download_button(f"⬇️ {f.name}.pdf", buf.getvalue(), f"{f.name}.pdf", type="primary", use_container_width=True)
        if selected == "pdf2word":
            for f in st.session_state.files:
                if f.name.lower().endswith(".pdf"):
                    open("temp.pdf","wb").write(f.getvalue())
                    cv = Converter("temp.pdf"); cv.convert("temp.docx"); cv.close()
                    with open("temp.docx","rb") as d:
                        st.download_button(f"⬇️ {f.name}.docx", d.read(), f"{f.name}.docx", type="primary", use_container_width=True)
        st.success("¡Listo! Hecho por Marco 🦙")
    except Exception as e:
        st.error(f"Error: {e}")
