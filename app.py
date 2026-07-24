import streamlit as st
from PIL import Image
import fitz  # PyMuPDF
import io
import zipfile
import tempfile
import os
from moviepy.editor import VideoFileClip

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Universal File Converter", layout="wide")
st.title("🔄 โปรแกรมแปลงไฟล์ครอบจักรวาล")
st.markdown("รองรับการแปลงไปมาระหว่าง: **PDF, JPG, PNG, WEBP** และ **MP4 เป็น MP3**")

# แบ่งหน้าจอเป็น 2 ฝั่ง
col1, col2 = st.columns(2)

with col1:
    st.header("📥 1. อัปโหลดไฟล์")
    # เพิ่ม "mp4" เข้าไปในประเภทไฟล์ที่รองรับ
    uploaded_files = st.file_uploader(
        "ลากไฟล์มาวาง หรือคลิก 'Browse files' (เลือกได้หลายไฟล์พร้อมกัน)", 
        type=["pdf", "jpg", "jpeg", "png", "webp", "mp4"],
        accept_multiple_files=True
    )

with col2:
    st.header("📤 2. ผลลัพธ์และการแปลง")
    
    if uploaded_files:
        file_types = [f.name.split('.')[-1].lower() for f in uploaded_files]
        
        # -----------------------------------------
        # กรณีที่ 1: อัปโหลดหลายไฟล์ (รวมรูปภาพเป็น PDF)
        # -----------------------------------------
        if len(uploaded_files) > 1:
            st.info("💡 ตรวจพบว่าคุณอัปโหลดหลายไฟล์ ระบบจะรวมไฟล์เหล่านี้เป็น **PDF เดียว**")
            
            # ตรวจสอบว่าทุกไฟล์เป็นรูปภาพหรือไม่ (ไม่ให้เอาวิดีโอหรือ PDF มารวม)
            if all(ext in ['jpg', 'jpeg', 'png', 'webp'] for ext in file_types):
                file_dict = {f"{i+1}. {f.name}": f for i, f in enumerate(uploaded_files)}
                
                st.markdown("**จัดเรียงลำดับหน้า PDF:** *(หากต้องการเปลี่ยนลำดับ ให้กากบาทไฟล์ที่ต้องการย้ายออก แล้วคลิกเลือกใหม่)*")
                
                ordered_names = st.multiselect(
                    "ลำดับไฟล์ที่จะรวม:", 
                    options=list(file_dict.keys()),
                    default=list(file_dict.keys())
                )
                
                if st.button("✨ รวมเป็นไฟล์ PDF เลย!"):
                    if not ordered_names:
                        st.warning("⚠️ กรุณาเลือกไฟล์อย่างน้อย 1 ไฟล์")
                    else:
                        with st.spinner('กำลังประมวลผลและรวมไฟล์...'):
                            images = []
                            for name in ordered_names:
                                file_obj = file_dict[name]
                                img = Image.open(file_obj)
                                
                                if img.mode in ("RGBA", "P"):
                                    img = img.convert("RGB")
                                else:
                                    img = img.convert("RGB")
                                images.append(img)
                            
                            out_io = io.BytesIO()
                            
                            if len(images) == 1:
                                images[0].save(out_io, format="PDF")
                            else:
                                images[0].save(out_io, format="PDF", save_all=True, append_images=images[1:])
                                
                            out_io.seek(0)
                            
                            st.success("✅ รวมไฟล์และแปลงเป็น PDF สำเร็จ!")
                            st.download_button(
                                label="⬇️ ดาวน์โหลดไฟล์ PDF",
                                data=out_io,
                                file_name="combined_document.pdf",
                                mime="application/pdf"
                            )
            else:
                st.error("❌ ฟีเจอร์รวมหลายไฟล์ รองรับเฉพาะการนำไฟล์รูปภาพ (JPG, PNG, WEBP) มารวมกันเท่านั้นครับ กรุณาอัปโหลดใหม่ให้ถูกต้อง")

        # -----------------------------------------
        # กรณีที่ 2: อัปโหลดแค่ไฟล์เดียว (แปลงไฟล์ไปมาตามปกติ)
        # -----------------------------------------
        elif len(uploaded_files) == 1:
            uploaded_file = uploaded_files[0]
            file_ext = file_types[0]
            original_name = uploaded_file.name.rsplit('.', 1)[0]
            
            # --- แปลงรูปภาพ เป็น รูปภาพ/PDF ---
            if file_ext in ['jpg', 'jpeg', 'png', 'webp']:
                options = ["PDF", "PNG", "JPG", "WEBP"]
                options = [opt for opt in options if opt.lower() != file_ext and opt.lower() != file_ext.replace('jpeg', 'jpg')]
                
                target_format = st.selectbox("เลือกสกุลไฟล์ที่ต้องการแปลง:", options)
                
                if st.button("✨ แปลงไฟล์เลย!"):
                    with st.spinner('กำลังประมวลผล...'):
                        img = Image.open(uploaded_file)
                        out_io = io.BytesIO()
                        
                        if target_format in ["JPG", "PDF"] and img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")
                        elif target_format == "PDF":
                            img = img.convert("RGB")
                            
                        img.save(out_io, format=target_format if target_format != "JPG" else "JPEG")
                        out_io.seek(0)
                        
                        st.success("✅ แปลงไฟล์สำเร็จ!")
                        st.download_button(
                            label=f"⬇️ ดาวน์โหลดไฟล์ {target_format}",
                            data=out_io,
                            file_name=f"{original_name}.{target_format.lower()}",
                            mime=f"image/{target_format.lower()}" if target_format != "PDF" else "application/pdf"
                        )

            # --- แปลง PDF เป็น JPG/PNG (แยกหน้า) ---
            elif file_ext == 'pdf':
                target_format = st.selectbox("เลือกสกุลไฟล์ที่ต้องการแปลง:", ["JPG", "PNG"])
                
                if st.button("✨ แปลงไฟล์เลย!"):
                    with st.spinner('กำลังแยกหน้า PDF เป็นรูปภาพ...'):
                        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                        zip_io = io.BytesIO()
                        
                        with zipfile.ZipFile(zip_io, 'w') as zipf:
                            for page_num in range(len(doc)):
                                page = doc.load_page(page_num)
                                pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0)) 
                                
                                img_ext = "jpeg" if target_format == "JPG" else "png"
                                img_bytes = pix.tobytes(img_ext)
                                
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
                        
            # --- แปลง MP4 เป็น MP3 ---
            elif file_ext == 'mp4':
                st.info("🎵 ระบบพร้อมสำหรับแยกเสียงจากวิดีโอ (สกัด MP4 เป็น MP3)")
                
                if st.button("✨ สกัดไฟล์เสียงเลย!"):
                    with st.spinner('กำลังแยกเสียงจากวิดีโอ... อาจใช้เวลาสักครู่ขึ้นอยู่กับขนาดไฟล์'):
                        try:
                            # 1. บันทึกไฟล์ MP4 ต้นฉบับลง Temp file เพื่อให้ moviepy อ่านได้
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_mp4:
                                temp_mp4.write(uploaded_file.read())
                                mp4_path = temp_mp4.name
                            
                            mp3_path = mp4_path.replace(".mp4", ".mp3")
                            
                            # 2. ใช้ moviepy อ่านวิดีโอและเซฟเฉพาะเสียง
                            video = VideoFileClip(mp4_path)
                            video.audio.write_audiofile(mp3_path, logger=None) # logger=None ปิดการปริ้นท์ข้อความรกๆ
                            video.close() # ปิดไฟล์วิดีโอ
                            
                            # 3. อ่านไฟล์เสียงกลับเข้ามาเป็น Bytes เพื่อทำปุ่มโหลด
                            with open(mp3_path, "rb") as f:
                                mp3_bytes = f.read()
                                
                            st.success("✅ สกัดไฟล์เสียงสำเร็จ!")
                            st.download_button(
                                label="⬇️ ดาวน์โหลดไฟล์ MP3",
                                data=mp3_bytes,
                                file_name=f"{original_name}.mp3",
                                mime="audio/mpeg"
                            )
                            
                        except Exception as e:
                            st.error(f"❌ เกิดข้อผิดพลาดในการแปลงไฟล์: {e}")
                            
                        finally:
                            # 4. ลบไฟล์ชั่วคราวทิ้งทุกครั้ง เพื่อไม่ให้เปลืองพื้นที่เซิร์ฟเวอร์
                            if os.path.exists(mp4_path):
                                os.remove(mp4_path)
                            if os.path.exists(mp3_path):
                                os.remove(mp3_path)
