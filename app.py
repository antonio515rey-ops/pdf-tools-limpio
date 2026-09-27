import streamlit as st, fitz, io
from PIL import Image
from docx import Document
from pdf2docx import Converter
import requests

st.set_page_config(page_title="PDF Tools + IA", layout="wide")
st.title("❤️ PDF Tools + IA - Simple")

# --- IA ARRIBA ---
st.header("🤖 IA - Chatea y Genera Imágenes")
api_key = st.secrets.get("GROQ_API_KEY", "")

prompt = st.chat_input("Pregunta a la IA o pide una imagen: 'genera un gato astronauta'")
if prompt:
    st.chat_message("user").write(prompt)
    # Si pide imagen
    if "genera" in prompt.lower() or "imagen" in prompt.lower() or "dibuja" in prompt.lower():
        with st.chat_message("assistant"):
            st.write(f"Generando imagen: {prompt}")
            # Usa Pollinations (gratis, sin API key)
            url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}"
            st.image(url, caption=prompt)
    else:
        # Chat de texto con Groq si tienes key
        if api_key:
            from groq import Groq
            client = Groq(api_key=api_key)
            resp = client.chat.completions.create(model="llama3-8b-8192", messages=[{"role":"user","content":prompt}])
            st.chat_message("assistant").write(resp.choices[0].message.content)
        else:
            st.chat_message("assistant").write("Pon tu GROQ_API_KEY en Secrets de Streamlit para activar el chat. La generación de imágenes ya funciona sin key.")

st.divider()

# --- 8 CUADROS ABAJO ---
st.header("📄 8 Herramientas Esenciales")
if 'files' not in st.session_state: st.session_state.files = []

up = st.file_uploader("Sube archivos (PDF, Word, JPG)", type=["pdf","docx","jpg","png"], accept_multiple_files=True)
if up:
    st.session_state.files = up

col1, col2, col3, col4 = st.columns(4)
tool = None
with col1:
    if st.button("1️⃣ Unir PDF", use_container_width=True): tool = "unir"
    if st.button("2️⃣ Dividir PDF", use_container_width=True): tool = "dividir"
with col2:
    if st.button("3️⃣ Comprimir PDF", use_container_width=True): tool = "comprimir"
    if st.button("4️⃣ PDF a Word", use_container_width=True): tool = "pdf2word"
with col3:
    if st.button("5️⃣ Word a PDF", use_container_width=True): tool = "word2pdf"
    if st.button("6️⃣ JPG a PDF", use_container_width=True): tool = "jpg2pdf"
with col4:
    if st.button("7️⃣ PDF a JPG", use_container_width=True): tool = "pdf2jpg"
    if st.button("8️⃣ Extraer Texto", use_container_width=True): tool = "texto"

if tool and st.session_state.files:
    # Lógica simple de cada una
    if tool == "unir":
        out = fitz.open()
        for f in st.session_state.files:
            if f.name.endswith(".pdf"): out.insert_pdf(fitz.open(stream=f.getvalue(), filetype="pdf"))
        buf = io.BytesIO(); out.save(buf)
        st.download_button("Descargar Unido", buf.getvalue(), "unido.pdf")

    if tool == "word2pdf":
        # Word a PDF básico con fitz
        for f in st.session_state.files:
            if f.name.endswith(".docx"):
                doc = Document(io.BytesIO(f.getvalue()))
                pdf = fitz.open(); page = pdf.new_page()
                text = "\n".join([p.text for p in doc.paragraphs])
                page.insert_text((50,50), text)
                buf = io.BytesIO(); pdf.save(buf)
                st.download_button(f"Descargar {f.name}.pdf", buf.getvalue(), f"{f.name}.pdf")

    if tool == "pdf2word":
        for f in st.session_state.files:
            if f.name.endswith(".pdf"):
                with open("temp.pdf","wb") as tmp: tmp.write(f.getvalue())
                docx_path = "temp.docx"
                cv = Converter("temp.pdf"); cv.convert(docx_path); cv.close()
                with open(docx_path,"rb") as d: st.download_button(f"Descargar {f.name}.docx", d, f"{f.name}.docx")

    if tool == "jpg2pdf":
        imgs = [Image.open(f) for f in st.session_state.files if f.type.startswith("image")]
        if imgs:
            buf = io.BytesIO(); imgs[0].save(buf, "PDF", save_all=True, append_images=imgs[1:])
            st.download_button("Descargar PDF de Imágenes", buf.getvalue(), "imagenes.pdf")

    if tool == "texto":
        txt = ""
        for f in st.session_state.files:
            if f.name.endswith(".pdf"):
                doc = fitz.open(stream=f.getvalue(), filetype="pdf")
                for p in doc: txt += p.get_text()
        st.text_area("Texto", txt, height=300)

    st.success(f"{tool} listo!")
