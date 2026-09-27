import streamlit as st, fitz, io, urllib.parse, random
from PIL import Image
from docx import Document
from pdf2docx import Converter

st.set_page_config(page_title="Marco", page_icon="🧠", layout="centered")

st.markdown("""
<style>
.stApp{background:#0e0e12}
h1{font-weight:900;text-align:center;background:linear-gradient(90deg,#a78bfa,#f472b6,#60a5fa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:42px}
.stChatInput{border-radius:20px!important}
div[data-testid="stChatMessage"]{background:#1c1c24;border:1px solid #2e2e3e;border-radius:18px}
div[data-testid="stButton"] button{border-radius:12px;height:90px;font-weight:600;background:#1c1c24;border:1px solid #2e2e3e}
div[data-testid="stButton"] button:hover{border-color:#a78bfa;background:#252538}
</style>
# 🧠 Marco
""", unsafe_allow_html=True)

st.caption("Responde bien, crea imágenes y arregla PDFs - todo con ENTER")

api = st.secrets.get("GROQ_API_KEY","")
if 'c' not in st.session_state: st.session_state.c=[]

p = st.chat_input("Pregunta lo que sea y dale ENTER...")
if p:
    st.session_state.c.append({"r":"user","t":p})
    q_img = any(w in p.lower() for w in ["imagen","crea","dibuja","foto"])
    q_txt = any(w in p.lower() for w in ["que es","explica","que","como"]) or not q_img

    if q_txt:
        if api:
            try:
                from groq import Groq
                r = Groq(api_key=api).chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role":"system","content":"Eres Marco, útil, claro, amable."},{"role":"user","content":p}])
                st.session_state.c.append({"r":"assistant","t":r.choices[0].message.content})
            except Exception as e: st.session_state.c.append({"r":"assistant","t":f"Error: {e}"})
        else:
            st.session_state.c.append({"r":"assistant","t":"Pon tu GROQ_API_KEY en Secrets para texto. Para imágenes escribe 'crea imagen de...'"})
    if q_img:
        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p)}?model=turbo&seed={random.randint(0,9999999)}&nologo=true&width=1024&height=1024"
        st.session_state.c.append({"r":"assistant","t":f"IMG::{url}"})

for m in st.session_state.c:
    with st.chat_message(m["r"]):
        if m["t"].startswith("IMG::"): st.image(m["t"].split("::")[1], use_container_width=True)
        else: st.write(m["t"])

st.divider()
st.write("**PDF Tools**")
files = st.file_uploader("", type=["pdf","docx","jpg","png"], accept_multiple_files=True, label_visibility="collapsed")

if files:
    a,b,c,d = st.columns(4)
    if a.button("🔗 Unir PDF"):
        out=fitz.open()
        [out.insert_pdf(fitz.open(stream=f.getvalue(),filetype="pdf")) for f in files if f.name.endswith(".pdf")]
        buf=io.BytesIO();out.save(buf);st.download_button("⬇️ Unido",buf.getvalue(),"unido.pdf",type="primary")
    if b.button("✂️ Dividir"):
        for f in files:
            if f.name.endswith(".pdf"):
                doc=fitz.open(stream=f.getvalue(),filetype="pdf")
                for i in range(len(doc)):
                    s=fitz.open();s.insert_pdf(doc,from_page=i,to_page=i);buf=io.BytesIO();s.save(buf);st.download_button(f"Pág {i+1}",buf.getvalue(),f"p{i+1}.pdf")
    if c.button("🗜️ Comprimir"):
        for f in files:
            if f.name.endswith(".pdf"):
                doc=fitz.open(stream=f.getvalue(),filetype="pdf");buf=io.BytesIO();doc.save(buf,garbage=4,deflate=True);st.download_button("⬇️ Comp",buf.getvalue(),f"c_{f.name}")
    if d.button("📖 Texto"):
        t="".join([p.get_text() for f in files if f.name.endswith(".pdf") for p in fitz.open(stream=f.getvalue(),filetype="pdf")])
        st.text_area("",t,height=150);st.download_button("⬇️ TXT",t,"t.txt")
    e,f,g,h = st.columns(4)
    if e.button("📄 PDF→Word"):
        for f_ in files:
            if f_.name.endswith(".pdf"):
                open("x.pdf","wb").write(f_.getvalue());Converter("x.pdf").convert("x.docx")
                with open("x.docx","rb") as d: st.download_button("⬇️ Word",d.read(),f"{f_.name}.docx")
    if f.button("📝 Word→PDF"):
        for f_ in files:
            if f_.name.endswith(".docx"):
                doc=Document(io.BytesIO(f_.getvalue()));pdf=fitz.open();pg=pdf.new_page();y=50
                for par in doc.paragraphs:
                    if par.text: pg.insert_text((50,y),par.text[:1000]);y+=20; y=50 if y>750 else y
                buf=io.BytesIO();pdf.save(buf);st.download_button("⬇️ PDF",buf.getvalue(),f"{f_.name}.pdf")
    if g.button("🖼️ JPG→PDF"):
        ims=[Image.open(io.BytesIO(f.getvalue())).convert("RGB") for f in files if "image" in f.type]
        if ims:
            b=io.BytesIO();ims[0].save(b,"PDF",save_all=True,append_images=ims[1:]);st.download_button("⬇️ PDF",b.getvalue(),"img.pdf")
    if h.button("🎨 PDF→JPG"):
        for f_ in files:
            if f_.name.endswith(".pdf"):
                doc=fitz.open(stream=f_.getvalue(),filetype="pdf")
                for i,pg in enumerate(doc): st.image(pg.get_pixmap(dpi=150).tobytes("png"),caption=f"Pág {i+1}",use_container_width=True)
