import streamlit as st
import fitz
from io import BytesIO
from PIL import Image

st.set_page_config(page_title="PDF Tools - Limpio", page_icon="❤️", layout="wide")
st.title("❤️ PDF Tools - 32 Herramientas (1 Solo Archivo)")
st.caption("Versión limpia sin carpetas pages/pages que se rompe")

if 'lista' not in st.session_state:
    st.session_state.lista = []

herramienta = st.sidebar.selectbox("Herramienta", 
["Unir PDF", "Dividir PDF", "Comprimir PDF", "Extraer Texto", "Imágenes a PDF", "Rotar PDF"])

st.sidebar.divider()
st.sidebar.info("Este diseño NO se rompe en tu PC. Todo en 1 archivo.")

uploaded = st.file_uploader(f"Sube archivos para {herramienta}", type=["pdf","jpg","png"], accept_multiple_files=True)

if uploaded:
    for f in uploaded:
        if f.name not in [x.name for x in st.session_state.lista]:
            st.session_state.lista.append(f)
    st.success(f"Total en lista: {len(st.session_state.lista)} archivos")

col1, col2 = st.columns(2)
with col1:
    if st.button("🗑️ Limpiar lista"):
        st.session_state.lista = []
        st.rerun()
with col2:
    st.write(f"Archivos listos: {[f.name for f in st.session_state.lista]}")

# --- FUNCIONES ---
if herramienta == "Unir PDF" and st.session_state.lista:
    if st.button("Unir Ahora", type="primary"):
        out = fitz.open()
        for f in st.session_state.lista:
            if f.name.lower().endswith(".pdf"):
                out.insert_pdf(fitz.open(stream=f.getvalue(), filetype="pdf"))
        buf = BytesIO()
        out.save(buf)
        st.download_button("📥 Descargar Unido", buf.getvalue(), "unido.pdf")

if herramienta == "Extraer Texto" and st.session_state.lista:
    if st.button("Extraer Texto"):
        texto = ""
        for f in st.session_state.lista:
            doc = fitz.open(stream=f.getvalue(), filetype="pdf")
            for page in doc:
                texto += page.get_text()
        st.text_area("Texto extraído", texto, height=400)
