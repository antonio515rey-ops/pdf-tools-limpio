import streamlit as st
import fitz
import io
import urllib.parse
import random
from PIL import Image
from docx import Document
from pdf2docx import Converter

st.set_page_config(page_title="PDF Tools + IA", layout="wide", page_icon="❤️")
st.title("❤️ PDF Tools + IA - Simple")

# --- IA ARRIBA ---
st.header("🤖 IA - Chatea y Genera Imágenes")

api_key = st.secrets.get("GROQ_API_KEY", "")

if 'chat' not in st.session_state:
    st.session_state.chat = []

for m in st.session_state.chat:
    st.chat_message(m["role"]).write(m["content"])

prompt = st.chat_input("Pregunta a la IA o pide una imagen: 'crea una oveja esponjosa'")

if prompt:
    st.session_state.chat.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    es_imagen = any(w in prompt.lower() for w in ["genera", "imagen", "dibuja", "crea", "foto", "oveja", "gato", "perro", "pug", "dibuja"])

    with st.chat_message("assistant"):
        if es_imagen:
            # Mejora el prompt para que salga bien
            prompt_mejorado = prompt
            if "oveja" in prompt.lower():
                prompt_mejorado = "cute fluffy white sheep in green field, photorealistic, highly detailed, adorable lamb"

            st.write(f"Generando: {prompt_mejorado}")
            encoded = urllib.parse.quote(prompt_mejorado)
            seed = random.randint(0, 9999999)
            url = f"https://image.pollinations.ai/prompt/{encoded}?model=flux&nologo=true&seed={seed}&width=1024&height=1024&enhance=true"
            st.image(url, caption=prompt)
            st.session_state.chat.append({"role": "assistant", "content": f"Imagen generada: {prompt}"})
        else:
            if not api_key:
                st.warning("Pon tu GROQ_API_KEY en Secrets para chat de texto. Mientras usa 'crea una imagen de...'")
            else:
                try:
                    from groq import Groq
                    client = Groq(api_key=api_key)
                    resp = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    ans = resp.choices[0].message.content
                    st.write(ans)
                    st.session_state.chat.append({"role": "assistant", "content": ans})
                except Exception as e:
                    st.error(f"Error Groq: {e}")

st.divider()

# --- 8 CUADROS ABAJO ---
st.header("📄 8 Herramientas Esenciales")

if 'files' not in st.session_state:
    st.session_state.files = []

up = st.file_uploader("Sube archivos (PDF, Word, JPG)", type=["pdf", "docx", "jpg", "jpeg", "png"], accept_multiple_files=True)
if up:
    st.session_state.files = up
    st.success(f"{len(up)} archivos cargados")

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
    try:
        if tool == "unir":
            out = fitz.open()
            for f in st.session_state.files:
                if f.name.lower().endswith(".pdf"):
                    out.insert_pdf(fitz.open(stream=f.getvalue(), filetype="pdf"))
            buf = io.BytesIO()
            out.save(buf)
            st.download_button("⬇️ Descargar Unido", buf.getvalue(), "unido.pdf", "application/pdf")
        if tool == "dividir":
            for f in st.session_state.files:
                if f.name.lower().endswith(".pdf"):
                    doc = fitz.open(stream=f.getvalue(), filetype="pdf")
                    for i in range(len(doc)):
                        single = fitz.open()
                        single.insert_pdf(doc, from_page=i, to_page=i)
                        b = io.BytesIO()
                        single.save(b)
                        st.download_button(f"⬇️ Página {i+1}", b.getvalue(), f"{f.name}_pag{i+1}.pdf")
        if tool == "comprimir":
            for f in st.session_state.files:
                if f.name.lower().endswith(".pdf"):
                    doc = fitz.open(stream=f.getvalue(), filetype="pdf")
                    b = io.BytesIO()
                    doc.save(b, garbage=4, deflate=True)
                    st.download_button(f"⬇️ Comprimido {f.name}", b.getvalue(), f"comprimido_{f.name}")
        if tool == "word2pdf":
            for f in st.session_state.files:
                if f.name.lower().endswith(".docx"):
                    docx = Document(io.BytesIO(f.getvalue()))
                    pdf = fitz.open()
                    page = pdf.new_page()
                    y = 50
                    for p in docx.paragraphs:
                        if p.text.strip():
                            page.insert_text((50, y), p.text[:1000])
                            y += 20
                            if y > 750:
                                page = pdf.new_page()
                                y = 50
                    buf = io.BytesIO()
                    pdf.save(buf)
                    st.download_button(f"⬇️ {f.name}.pdf", buf.getvalue(), f"{f.name}.pdf")
        if tool == "pdf2word":
            for f in st.session_state.files:
                if f.name.lower().endswith(".pdf"):
                    open("temp.pdf","wb").write(f.getvalue())
                    cv = Converter("temp.pdf")
                    cv.convert("temp.docx")
                    cv.close()
                    with open("temp.docx","rb") as d:
                        st.download_button(f"⬇️ {f.name}.docx", d.read(), f"{f.name}.docx")
        if tool == "jpg2pdf":
            imgs = [Image.open(io.BytesIO(f.getvalue())).convert("RGB") for f in st.session_state.files if f.type.startswith("image")]
            if imgs:
                buf = io.BytesIO()
                imgs[0].save(buf, "PDF", save_all=True, append_images=imgs[1:])
                st.download_button("⬇️ Descargar PDF de Imágenes", buf.getvalue(), "imagenes.pdf")
        if tool == "pdf2jpg":
            for f in st.session_state.files:
                if f.name.lower().endswith(".pdf"):
                    doc = fitz.open(stream=f.getvalue(), filetype="pdf")
                    for i, page in enumerate(doc):
                        pix = page.get_pixmap(dpi=150)
                        img_bytes = pix.tobytes("png")
                        st.image(img_bytes, caption=f"{f.name} - Pág {i+1}")
                        st.download_button(f"⬇️ Descargar Pág {i+1}", img_bytes, f"{f.name}_pag{i+1}.png")
        if tool == "texto":
            full = ""
            for f in st.session_state.files:
                if f.name.lower().endswith(".pdf"):
                    doc = fitz.open(stream=f.getvalue(), filetype="pdf")
                    for p in doc:
                        full += p.get_text() + "\n"
            st.text_area("Texto extraído", full, height=400)
            st.download_button("⬇️ Descargar texto.txt", full, "texto.txt")
        st.success("¡Listo!")
    except Exception as e:
        st.error(f"Error: {e}")
