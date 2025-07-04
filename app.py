import os
import uuid
import pandas as pd
import streamlit as st
import concurrent.futures

from src.extractor import process_file_ocr, extract_images_from_file, cleanup_images
from src.llm_extractor import extract_invoice_fields_with_llm
from src.red_flags import detect_red_flags
from src.utils import save_uploaded_file

st.set_page_config(page_title="Invoice Red Flag Detector", layout="wide")
st.title("📄 Invoice Red Flag Detection - POC")

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.sidebar.header("Upload Invoices")
uploaded_files = st.sidebar.file_uploader(
    "Upload one or more invoice files (PDF or image)", 
    type=["pdf", "png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

analyze_btn = st.sidebar.button("Analyze Invoices")

if uploaded_files:
    st.success(f"{len(uploaded_files)} file(s) uploaded successfully.")

def process_invoice(uploaded_file):
    file_id = str(uuid.uuid4())[:8]
    file_path = save_uploaded_file(uploaded_file, upload_dir=UPLOAD_DIR, uid=file_id)
    result = {
        "file_name": uploaded_file.name,
        "error": None,
        "ocr_result": None,
        "structured": None
    }
    try:
        ocr_result = process_file_ocr(file_path)
        result["ocr_result"] = ocr_result
    except Exception as e:
        result["error"] = f"OCR failed: {e}"
        return result
    image_paths = extract_images_from_file(file_path)
    try:
        structured = extract_invoice_fields_with_llm(ocr_result["ocr_text"], image_paths=image_paths)
        result["structured"] = structured
    except Exception as e:
        result["error"] = f"LLM extraction failed: {e}"
        cleanup_images(image_paths)
        return result
    if isinstance(structured, dict) and "error" in structured:
        result["error"] = f"LLM Error: {structured.get('error')}"
        result["raw_output"] = structured.get("raw_output", "")
    cleanup_images(image_paths)
    return result

if uploaded_files and analyze_btn:
    all_invoice_data = []
    results = []
    with st.spinner("Processing all invoices in parallel..."):
        with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
            future_to_file = {executor.submit(process_invoice, uf): uf for uf in uploaded_files}
            for future in concurrent.futures.as_completed(future_to_file):
                results.append(future.result())
    for res in results:
        st.subheader(f"📎 {res['file_name']}")
        if res.get("error"):
            st.error(res["error"])
            if "raw_output" in res:
                st.code(res["raw_output"])
            continue
        ocr_result = res["ocr_result"]
        structured = res["structured"]
        with st.expander("📝 OCR Text (Preview)", expanded=False):
            st.code(ocr_result["ocr_text"][:2000])
        with st.expander("📦 Extracted Fields", expanded=False):
            st.json(structured)
        all_invoice_data.append({
            "file_name": res["file_name"],
            "vendor_name": structured.get("vendor_name", ""),
            "phone_numbers": structured.get("phone_numbers", []),
            "email_addresses": structured.get("email_addresses", []),
            "gst_or_pan": structured.get("gst_or_pan", ""),
            "table_headers": structured.get("table_headers", []),
            "table_row_data": structured.get("table_row_data", []),
            "table_size": structured.get("table_size", None),
            "scanned_or_typed": structured.get("scanned_or_typed", ""),
            "handwritten_or_typed": structured.get("handwritten_or_typed", ""),
        })
    # Step 3: Detect Red Flags
    st.subheader("🚨 Red Flag Report")
    flagged = detect_red_flags(all_invoice_data)
    df = pd.DataFrame(flagged)
    required_cols = ["file_name", "vendor_name", "flag_type", "flag_reason"]
    if all(col in df.columns for col in required_cols):
        st.dataframe(df[required_cols], use_container_width=True)
        
        # Step 4: Group Red Flags by Type
        st.subheader("📊 Grouped Red Flags by Type")
        
        # Filter only red flags (exclude green flags)
        red_flags_df = df[df['flag_type'] != '✅ Green Flag'].copy()
        
        if not red_flags_df.empty:
            # Group by flag type first
            for flag_type in red_flags_df['flag_type'].unique():
                flag_group = red_flags_df[red_flags_df['flag_type'] == flag_type]
                
                st.markdown(f"### {flag_type}")
                
                if flag_type == "🚩 Shared Contact Info":
                    # Group by the specific contact that's shared
                    contact_groups = {}
                    for _, row in flag_group.iterrows():
                        # Extract contact from reason
                        reason = row['flag_reason']
                        if "Contact " in reason and " used by multiple vendors" in reason:
                            contact = reason.split("Contact ")[1].split(" used by")[0]
                            if contact not in contact_groups:
                                contact_groups[contact] = []
                            contact_groups[contact].append(row)
                    
                    for contact, group in contact_groups.items():
                        st.markdown(f"**Shared Contact:** {contact}")
                        group_df = pd.DataFrame(group)
                        display_df = group_df[['file_name', 'vendor_name', 'canonical_vendor', 'flag_reason']].copy()
                        display_df.columns = ['Document', 'Vendor Name', 'Canonical Vendor', 'Issue Detected']
                        st.table(display_df.reset_index(drop=True))
                        st.markdown("---")
                
                elif flag_type == "🚩 Same Format, Different Vendor":
                    # Group by format group ID
                    format_groups = flag_group.groupby('format_group_id')
                    for group_id, group in format_groups:
                        if group_id is not None:
                            st.markdown(f"**Format Group {group_id}**")
                            group_df = pd.DataFrame(group)
                            display_df = group_df[['file_name', 'vendor_name', 'canonical_vendor', 'flag_reason']].copy()
                            display_df.columns = ['Document', 'Vendor Name', 'Canonical Vendor', 'Issue Detected']
                            st.table(display_df.reset_index(drop=True))
                            st.markdown("---")
                
                elif flag_type == "🚩 Different Format, Same Vendor":
                    # Group by canonical vendor
                    vendor_groups = flag_group.groupby('canonical_vendor')
                    for vendor, group in vendor_groups:
                        st.markdown(f"**Vendor:** {vendor}")
                        display_df = group[['file_name', 'vendor_name', 'canonical_vendor', 'flag_reason']].copy()
                        display_df.columns = ['Document', 'Vendor Name', 'Canonical Vendor', 'Issue Detected']
                        st.table(display_df.reset_index(drop=True))
                        st.markdown("---")
                
                else:
                    # For any other flag types, group by reason
                    reason_groups = flag_group.groupby('flag_reason')
                    for reason, group in reason_groups:
                        st.markdown(f"**Reason:** {reason}")
                        display_df = group[['file_name', 'vendor_name', 'canonical_vendor', 'flag_reason']].copy()
                        display_df.columns = ['Document', 'Vendor Name', 'Canonical Vendor', 'Issue Detected']
                        st.table(display_df.reset_index(drop=True))
                        st.markdown("---")
        else:
            st.success("🎉 No red flags detected! All invoices appear to be legitimate.")
        
        # Step 5: Download CSV
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Download Red Flag Report as CSV",
            csv,
            "red_flags_report.csv",
            "text/csv"
        )
    else:
        st.warning("No valid invoice data to display. Please check for errors above.")

elif uploaded_files and not analyze_btn:
    st.info("👇 Click 'Analyze Invoices' to start analysis.")
else:
    st.info("👈 Upload invoice files from the sidebar to begin.")