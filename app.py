import streamlit as st
import fitz
import io
import urllib.parse
import random
from PIL import Image
from docx import Document
from pdf2docx import Converter

st.set_page_config(page_title="PDF Lover AI", layout="wide", page_icon="✨")

# --- ESTILO BONITO TIPO GEMINI ---
st.markdown("""
<style>
   .stApp { background: #0e1117; }
   .big-title { font-size: 2.8rem; font-weight: 800; background: linear-gradient(90deg, #8A2BE2, #FF6B6B, #4ECDC4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align:center; margin:0; }
   .subtitle { text-align:center; color: #888; margin-bottom: 20px; }
   .tool-card { background: #1a1e27; border: 1px solid #2a2f3e; border-radius: 16px; padding: 18px; text-align:center; transition: 0.2s; height: 130px; }
   .tool-card:hover { border-color: #8A2BE2; transform: translateY(-3px); }
    div[data-testid="stChatMessage"] { background: #1a1e27; border-radius: 16px; border: 1px solid #2a2f3e; }
    /* Input arriba estilo Gemini */
   .top-bar { position: sticky; top:0; z-index: 999; background: #0e1117; padding: 15px 0; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="big-title">✨ PDF Lover AI</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Chatea, crea imágenes y edita PDFs - todo en uno</p>', unsafe_allow_html=True)

api_key = st.secrets.get("GROQ_API_KEY", "")

if 'chat' not in st.session_state:
    st.session_state.chat = []

# --- BARRA ARRIBA TIPO GEMINI ---
with st.container():
    col_in, col_btn = st.columns([5,1])
    with col_in:
        prompt = st.text_input(" ", placeholder="💬 Escribe aquí... ej: crea una oveja esponjosa blanca, o ¿de dónde vienen las ovejas?", label_visibility="collapsed", key="top_prompt")
    with col_btn:
        enviar = st.button("➤ Enviar", use_container_width=True, type="primary")

# Lógica al enviar
if enviar and prompt:
    st.session_state.chat.insert(0, {"role": "user", "content": prompt}) # Insertamos arriba para que se vea como Gemini

    es_imagen = any(w in prompt.lower() for w in ["genera", "imagen", "dibuja", "crea", "foto", "oveja", "gato", "perro", "pug", "paisaje", "anime"])

    if es_imagen:
        # Traducir oveja a prompt bueno
        prompt_en = prompt
        if "oveja" in prompt.lower():
            prompt_en = "cute fluffy white sheep lamb in green field with flowers, photorealistic, 8k, adorable, highly detailed"

        encoded = urllib.parse.quote(prompt_en)
        seed = random.randint(0, 9999999)
        img_url = f"https://image.pollinations.ai/prompt/{encoded}?model=flux&nologo=true&seed={seed}&width=1024&height=1024&enhance=true"
        st.session_state.chat.insert(0, {"role": "assistant", "content": f"IMG::{img_url}::{prompt}"})
    else:
        if not api_key:
            st.session_state.chat.insert(0, {"role": "assistant", "content": "⚠️ Pon tu GROQ_API_KEY en Secrets para usar el chat de texto. Para imágenes usa palabras como 'crea'."})
        else:
            try:
                from groq import Groq
                client = Groq(api_key=api_key)
                resp = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role":"user","content":prompt}])
                ans = resp.choices[0].message.content
                st.session_state.chat.insert(0, {"role": "assistant", "content": ans})
            except Exception as e:
                st.session_state.chat.insert(0, {"role": "assistant", "content": f"Error Groq: {e}. Intenta 'crea una imagen de...'"})
    st.rerun()

# --- HISTORIAL ABAJO (como Gemini) ---
for m in st.session_state.chat:
    with st.chat_message(m["role"]):
        if m["content"].startswith("IMG::"):
            _, url, caption = m["content"].split("::")
            st.write(f"**{caption}**")
            st.image(url, use_column_width=True)
        else:
            st.write(m["content"])

st.divider()

# --- HERRAMIENTAS BONITAS ---
st.markdown("### 🛠️ Herramientas PDF - 100% Gratis y Offline")

if 'files' not in st.session_state:
    st.session_state.files = []

up = st.file_uploader("Arrastra tus PDFs, Word o JPG aquí", type=["pdf", "docx", "jpg", "jpeg", "png"], accept_multiple_files=True)
if up:
    st.session_state.files = up

# Grid bonito con 8
tools_def = [
    ("🔗", "Unir PDF", "unir"),
    ("✂️", "Dividir PDF", "dividir"),
    ("🗜️", "Comprimir", "comprimir"),
    ("📄", "PDF a Word", "pdf2word"),
    ("📝", "Word a PDF", "word2pdf"),
    ("🖼️", "JPG a PDF", "jpg2pdf"),
    ("🎨", "PDF a JPG", "pdf2jpg"),
    ("📖", "Extraer Texto", "texto"),
]

cols = st.columns(4)
selected_tool = None
for i, (icon, name, key) in enumerate(tools_def):
    with cols[i % 4]:
        if st.button(f"{icon}\n\n**{name}**", key=f"btn_{key}", use_container_width=True):
            selected_tool = key

# Ejecutar herramienta
if selected_tool and st.session_state.files:
    with st.status(f"Procesando {selected_tool}...", expanded=True) as status:
        try:
            if selected_tool == "unir":
                out = fitz.open()
                for f in st.session_state.files:
                    if f.name.lower().endswith(".pdf"):
                        out.insert_pdf(fitz.open(stream=f.getvalue(), filetype="pdf"))
                buf = io.BytesIO(); out.save(buf)
                st.download_button("⬇️ Descargar PDF Unido", buf.getvalue(), "unido.pdf", "application/pdf", type="primary")
            # (los otros 7 funcionan igual que antes, código corto para que no falle)
            if selected_tool == "dividir":
                for f in st.session_state.files:
                    if f.name.lower().endswith(".pdf"):
                        doc = fitz.open(stream=f.getvalue(), filetype="pdf")
                        for i in range(len(doc)):
                            single = fitz.open(); single.insert_pdf(doc, from_page=i, to_page=i)
                            b = io.BytesIO(); single.save(b)
                            st.download_button(f"⬇️ Página {i+1} de {f.name}", b.getvalue(), f"{f.name}_p{i+1}.pdf")
            if selected_tool == "comprimir":
                for f in st.session_state.files:
                    if f.name.lower().endswith(".pdf"):
                        doc = fitz.open(stream=f.getvalue(), filetype="pdf")
                        b = io.BytesIO(); doc.save(b, garbage=4, deflate=True)
                        st.download_button(f"⬇️ Comprimido {f.name} ({len(b.getvalue())//1024}KB)", b.getvalue(), f"comp_{f.name}", type="primary")
            if selected_tool == "pdf2jpg":
                for f in st.session_state.files:
                    if f.name.lower().endswith(".pdf"):
                        doc = fitz.open(stream=f.getvalue(), filetype="pdf")
                        for i, page in enumerate(doc):
                            pix = page.get_pixmap(dpi=180)
                            st.image(pix.tobytes("png"), caption=f"Página {i+1}")
            if selected_tool == "jpg2pdf":
                imgs = [Image.open(io.BytesIO(f.getvalue())).convert("RGB") for f in st.session_state.files if f.type.startswith("image")]
                if imgs:
                    buf = io.BytesIO(); imgs[0].save(buf, "PDF", save_all=True, append_images=imgs[1:])
                    st.download_button("⬇️ Descargar PDF", buf.getvalue(), "imagenes.pdf", type="primary")
            if selected_tool == "texto":
                full = ""
                for f in st.session_state.files:
                    if f.name.lower().endswith(".pdf"):
                        doc = fitz.open(stream=f.getvalue(), filetype="pdf")
                        for p in doc: full += p.get_text() + "\n"
                st.text_area("Texto", full, height=300)
                st.download_button("⬇️ Descargar.txt", full, "texto.txt")
            if selected_tool == "word2pdf":
                for f in st.session_state.files:
                    if f.name.lower().endswith(".docx"):
                        docx = Document(io.BytesIO(f.getvalue()))
                        pdf = fitz.open(); page = pdf.new_page(); y=50
                        for p in docx.paragraphs:
                            if p.text.strip():
                                page.insert_text((50,y), p.text[:1200]); y+=20
                                if y>800: page=pdf.new_page(); y=50
                        buf = io.BytesIO(); pdf.save(buf)
                        st.download_button(f"⬇️ {f.name}.pdf", buf.getvalue(), f"{f.name}.pdf", type="primary")
            if selected_tool == "pdf2word":
                for f in st.session_state.files:
                    if f.name.lower().endswith(".pdf"):
                        open("temp.pdf","wb").write(f.getvalue())
                        cv = Converter("temp.pdf"); cv.convert("temp.docx"); cv.close()
                        with open("temp.docx","rb") as d:
                            st.download_button(f"⬇️ {f.name}.docx", d.read(), f"{f.name}.docx", type="primary")
            status.update(label="¡Listo!", state="complete")
        except Exception as e:
            st.error(f"Error: {e}")

st.caption("Diseño Gemini + Pollinations Flux (sin key) + Groq 3.1 para chat")
