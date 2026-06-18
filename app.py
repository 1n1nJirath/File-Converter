import streamlit as st
from PIL import Image
import fitz  # PyMuPDF
import io
import zipfile

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Universal File Converter", layout="wide")
st.title("🔄 โปรแกรมแปลงไฟล์ครอบจักรวาล")
st.markdown("รองรับการแปลงไปมาระหว่าง: **PDF, JPG, PNG, WEBP**")

# แบ่งหน้าจอเป็น 2 ฝั่ง
col1, col2 = st.columns(2)

with col1:
    st.header("📥 1. อัปโหลดไฟล์")
    # ช่องอัปโหลดไฟล์ที่รองรับทั้งลากวางและคลิกเพื่อเปิด File Explorer
    uploaded_file = st.file_uploader(
        "ลากไฟล์มาวาง หรือคลิกที่ 'Browse files' เพื่อเปิดหน้าต่างเลือกไฟล์", 
        type=["pdf", "jpg", "jpeg", "png", "webp"]
    )

with col2:
    st.header("📤 2. ผลลัพธ์การแปลงไฟล์")
    
    if uploaded_file is not None:
        # ดึงนามสกุลไฟล์ต้นฉบับ
        file_ext = uploaded_file.name.split('.')[-1].lower()
        original_name = uploaded_file.name.rsplit('.', 1)[0]
        
        # -----------------------------------------
        # กรณีไฟล์ต้นฉบับเป็นรูปภาพ (JPG, PNG, WEBP)
        # -----------------------------------------
        if file_ext in ['jpg', 'jpeg', 'png', 'webp']:
            options = ["PDF", "PNG", "JPG", "WEBP"]
            # เอาสกุลไฟล์เดิมออกเพื่อไม่ให้แปลงเป็นตัวเองซ้ำ
            options = [opt for opt in options if opt.lower() != file_ext and opt.lower() != file_ext.replace('jpeg', 'jpg')]
            
            target_format = st.selectbox("เลือกสกุลไฟล์ที่ต้องการแปลง:", options)
            
            if st.button("✨ แปลงไฟล์เลย!"):
                with st.spinner('กำลังประมวลผล...'):
                    img = Image.open(uploaded_file)
                    out_io = io.BytesIO()
                    
                    # ป้องกัน Error กรณีรูปโปร่งใสแปลงเป็น JPG/PDF
                    if target_format in ["JPG", "PDF"] and img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    elif target_format == "PDF":
                        img = img.convert("RGB") # PDF บังคับใช้โหมด RGB
                        
                    # บันทึกไฟล์ลง Memory
                    img.save(out_io, format=target_format if target_format != "JPG" else "JPEG")
                    out_io.seek(0)
                    
                    st.success("✅ แปลงไฟล์สำเร็จ!")
                    st.download_button(
                        label=f"⬇️ ดาวน์โหลดไฟล์ {target_format}",
                        data=out_io,
                        file_name=f"{original_name}.{target_format.lower()}",
                        mime=f"image/{target_format.lower()}" if target_format != "PDF" else "application/pdf"
                    )

        # -----------------------------------------
        # กรณีไฟล์ต้นฉบับเป็นเอกสาร PDF
        # -----------------------------------------
        elif file_ext == 'pdf':
            target_format = st.selectbox("เลือกสกุลไฟล์ที่ต้องการแปลง:", ["JPG", "PNG"])
            
            if st.button("✨ แปลงไฟล์เลย!"):
                with st.spinner('กำลังแยกหน้า PDF เป็นรูปภาพ...'):
                    # อ่านไฟล์ PDF จาก Memory
                    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                    
                    # สร้างไฟล์ Zip ใน Memory เพื่อรวมรูปทุกหน้า
                    zip_io = io.BytesIO()
                    with zipfile.ZipFile(zip_io, 'w') as zipf:
                        for page_num in range(len(doc)):
                            page = doc.load_page(page_num)
                            # ปรับความคมชัด x2 เพื่อไม่ให้ภาพแตก
                            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0)) 
                            
                            # แปลงเป็น Byte ของรูปภาพ
                            img_ext = "jpeg" if target_format == "JPG" else "png"
                            img_bytes = pix.tobytes(img_ext)
                            
                            # นำไฟล์แต่ละหน้าใส่เข้าไปใน Zip
                            filename = f"{original_name}_page_{page_num + 1}.{target_format.lower()}"
                            zipf.writestr(filename, img_bytes)
                    
                    zip_io.seek(0)
                    st.success(f"✅ แยกรูปภาพสำเร็จทั้งหมด {len(doc)} หน้า (รวมเป็นไฟล์ Zip)")
                    st.download_button(
                        label=f"⬇️ ดาวน์โหลดไฟล์ Zip ({target_format})",
                        data=zip_io,
                        file_name=f"{original_name}_images.zip",
                        mime="application/zip"
                    )
