# -*- coding: utf-8 -*-
import streamlit as st
import os
import math
import zipfile
import tempfile
from PyPDF2 import PdfReader, PdfWriter

# --- PDF 到圖片轉換所需 ---
# 提醒：此功能需要安裝 pdf2image 和 Poppler
# 1. 安裝函式庫: pip install streamlit pdf2image
# 2. 安裝 Poppler (請參考原腳本中的說明)
try:
    from pdf2image import convert_from_path
except ImportError:
    st.error("警告：未找到 'pdf2image' 函式庫。您將無法使用 JPG 輸出功能。請透過 'pip install pdf2image' 安裝它，並確保已安裝 Poppler。")
    convert_from_path = None

# --- 核心處理函式 (與原腳本相同) ---

def split_to_pdf(reader, total_pages, pages_per_split, output_filenames, output_dir):
    """處理 PDF 分割邏輯"""
    generated_files = []
    file_index = 0
    for i in range(0, total_pages, pages_per_split):
        writer = PdfWriter()
        start_page = i
        end_page = min(i + pages_per_split, total_pages)

        for page_num in range(start_page, end_page):
            writer.add_page(reader.pages[page_num])

        output_filename = f"{output_filenames[file_index]}.pdf"
        output_path = os.path.join(output_dir, output_filename)

        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        
        generated_files.append(output_path)
        st.write(f"已生成文件: '{output_filename}' (包含第 {start_page + 1} 到 {end_page} 頁)")
        file_index += 1
    return generated_files

def convert_to_jpg(pdf_path, total_pages, output_filenames, output_dir):
    """處理 PDF 到 JPG 的轉換邏輯"""
    if convert_from_path is None:
        st.error("錯誤：無法轉換為 JPG，因為 'pdf2image' 函式庫未成功導入。")
        return []
        
    generated_files = []
    images = convert_from_path(pdf_path, dpi=200)

    if len(images) != total_pages:
        st.warning(f"警告：PDF頁數 ({total_pages}) 與成功轉換的圖片數 ({len(images)}) 不匹配。")

    for i in range(min(total_pages, len(output_filenames))):
        output_filename = f"{output_filenames[i]}.jpg"
        output_path = os.path.join(output_dir, output_filename)
        images[i].save(output_path, 'JPEG')
        generated_files.append(output_path)
        st.write(f"已生成文件: '{output_filename}' (來自第 {i + 1} 頁)")
    return generated_files


# --- Streamlit 網頁介面 ---

st.set_page_config(page_title="PDF 分割與轉換工具", layout="wide")

st.title("📄 PDF 分割與轉換工具")
st.markdown("上傳一個 PDF 檔案，設定分割方式與檔名，即可將其分割為多個 PDF 或轉換為 JPG 圖片。")

# --- 側邊欄：設定選項 ---
with st.sidebar:
    st.header("⚙️ 設定")
    
    # 1. 上傳檔案
    uploaded_file = st.file_uploader("1. 上傳您的 PDF 檔案", type="pdf")
    
    # 2. 選擇格式
    output_format = st.radio(
        "2. 選擇輸出格式",
        ('pdf', 'jpg'),
        captions=["分割成多個 PDF", "每頁轉成一張 JPG"]
    )

    # 3. 設定每份頁數
    if output_format == 'pdf':
        pages_per_split = st.number_input("3. 每個分割檔案應包含幾頁？", min_value=1, value=1)
    else:
        pages_per_split = 1
        st.info("ℹ️ 輸出為 JPG 時，每個檔案固定為 1 頁。")

    # 4. 輸入檔名
    st.markdown("4. 輸入新檔名（每行一個，不需副檔名）")
    custom_names_text = st.text_area(
        "檔名列表", 
        height=250, 
        placeholder="例如：\n0047-张三\n0058-李四\n0068-王五"
    )

# --- 主畫面：執行與結果 ---
if uploaded_file is not None:
    # 解析檔名
    output_filenames = [name.strip() for name in custom_names_text.split('\n') if name.strip()]

    # 處理按鈕
    if st.button("🚀 開始處理", type="primary", use_container_width=True):
        if not output_filenames:
            st.error("錯誤：請在左側的檔名列表中輸入至少一個檔名。")
        else:
            with st.spinner('正在處理中，請稍候...'):
                try:
                    # 使用暫存目錄來處理檔案，避免檔案混亂
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # 將上傳的檔案寫入暫存區，因為 pdf2image 需要實體檔案路徑
                        input_pdf_path = os.path.join(temp_dir, uploaded_file.name)
                        with open(input_pdf_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        # 讀取 PDF
                        reader = PdfReader(input_pdf_path)
                        total_pages = len(reader.pages)
                        st.info(f"文件 '{uploaded_file.name}' 總共有 {total_pages} 頁。")
                        
                        # 檢查檔名數量
                        num_expected_files = math.ceil(total_pages / pages_per_split)
                        if num_expected_files != len(output_filenames):
                            st.error(f"錯誤：檔名數量不匹配！")
                            st.error(f"根據您的設置，預計會生成 {num_expected_files} 個文件，但您只提供了 {len(output_filenames)} 個檔名。")
                        else:
                            # 建立一個子目錄來存放輸出的檔案
                            output_dir = os.path.join(temp_dir, "output")
                            os.makedirs(output_dir)

                            generated_files = []
                            # 根據選擇的格式執行
                            if output_format == 'pdf':
                                st.write("正在分割成多個 PDF 文件...")
                                generated_files = split_to_pdf(reader, total_pages, pages_per_split, output_filenames, output_dir)
                            elif output_format == 'jpg':
                                st.write("正在將每一頁轉換為 JPG 圖片...")
                                generated_files = convert_to_jpg(input_pdf_path, total_pages, output_filenames, output_dir)
                            
                            if generated_files:
                                # 將所有生成的文件打包成 ZIP
                                zip_path = os.path.join(temp_dir, "分割結果.zip")
                                with zipfile.ZipFile(zip_path, 'w') as zipf:
                                    for file in generated_files:
                                        zipf.write(file, os.path.basename(file))
                                
                                # 提供 ZIP 檔案下載
                                st.success("🎉 全部分割完成！")
                                with open(zip_path, "rb") as f:
                                    st.download_button(
                                        label="📥 下載所有檔案 (ZIP)",
                                        data=f,
                                        file_name="分割結果.zip",
                                        mime="application/zip",
                                        use_container_width=True
                                    )
                except Exception as e:
                    st.error(f"處理過程中發生嚴重錯誤: {e}")
else:
    st.info("請從左側側邊欄開始，上傳您的 PDF 檔案並完成設定。")

st.markdown("---")
st.markdown("由 Gemini Pro 強力驅動")
