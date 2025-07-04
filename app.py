import os
import uuid
import pandas as pd
import streamlit as st
import concurrent.futures

from src.extractor import process_file_ocr, extract_images_from_file, cleanup_images
from src.llm_extractor import extract_invoice_fields_with_llm
from src.red_flags import detect_red_flags
from src.utils import save_uploaded_file
from src.logger_config import get_logger

# Set up logger
logger = get_logger(__name__)

st.set_page_config(page_title="Invoice Red Flag Detector", layout="wide")
st.title("📄 Invoice Red Flag Detection - POC")

logger.info("Application started - Invoice Red Flag Detection POC")

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
logger.info(f"Upload directory created/verified: {UPLOAD_DIR}")

st.sidebar.header("Upload Invoices")
uploaded_files = st.sidebar.file_uploader(
    "Upload one or more invoice files (PDF or image)", 
    type=["pdf", "png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

analyze_btn = st.sidebar.button("Analyze Invoices")

if uploaded_files:
    logger.info(f"Files uploaded: {len(uploaded_files)} files")
    for file in uploaded_files:
        logger.debug(f"Uploaded file: {file.name} ({file.size} bytes)")
    st.success(f"{len(uploaded_files)} file(s) uploaded successfully.")

def process_invoice(uploaded_file):
    """Process a single invoice file with comprehensive logging."""
    logger.info(f"Starting processing for file: {uploaded_file.name}")
    
    file_id = str(uuid.uuid4())[:8]
    logger.debug(f"Generated file ID: {file_id}")
    
    result = {
        "file_name": uploaded_file.name,
        "error": None,
        "ocr_result": None,
        "structured": None
    }
    
    try:
        logger.debug(f"Saving uploaded file: {uploaded_file.name}")
        file_path = save_uploaded_file(uploaded_file, upload_dir=UPLOAD_DIR, uid=file_id)
        logger.info(f"File saved successfully: {file_path}")
        
        logger.debug("Starting OCR processing")
        ocr_result = process_file_ocr(file_path)
        result["ocr_result"] = ocr_result
        logger.info(f"OCR completed for {uploaded_file.name}, extracted {len(ocr_result.get('ocr_text', ''))} characters")
        
    except Exception as e:
        error_msg = f"OCR failed: {e}"
        logger.error(f"OCR processing failed for {uploaded_file.name}: {e}", exc_info=True)
        result["error"] = error_msg
        return result
    
    try:
        logger.debug("Extracting images from file")
        image_paths = extract_images_from_file(file_path)
        logger.debug(f"Extracted {len(image_paths)} images from {uploaded_file.name}")
        
        logger.debug("Starting LLM extraction")
        structured = extract_invoice_fields_with_llm(ocr_result["ocr_text"], image_paths=image_paths)
        result["structured"] = structured
        logger.info(f"LLM extraction completed for {uploaded_file.name}")
        
    except Exception as e:
        error_msg = f"LLM extraction failed: {e}"
        logger.error(f"LLM extraction failed for {uploaded_file.name}: {e}", exc_info=True)
        result["error"] = error_msg
        cleanup_images(image_paths)
        return result
    
    if isinstance(structured, dict) and "error" in structured:
        error_msg = f"LLM Error: {structured.get('error')}"
        logger.error(f"LLM returned error for {uploaded_file.name}: {structured.get('error')}")
        result["error"] = error_msg
        result["raw_output"] = structured.get("raw_output", "")
    
    logger.debug("Cleaning up extracted images")
    cleanup_images(image_paths)
    
    logger.info(f"Processing completed successfully for {uploaded_file.name}")
    return result

if uploaded_files and analyze_btn:
    logger.info("Starting batch processing of invoices")
    all_invoice_data = []
    results = []
    
    with st.spinner("Processing all invoices in parallel..."):
        logger.debug(f"Using ThreadPoolExecutor with max_workers=7")
        with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
            future_to_file = {executor.submit(process_invoice, uf): uf for uf in uploaded_files}
            logger.info(f"Submitted {len(future_to_file)} tasks to thread pool")
            
            for future in concurrent.futures.as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.debug(f"Completed processing: {file.name}")
                except Exception as e:
                    logger.error(f"Exception occurred while processing {file.name}: {e}", exc_info=True)
                    results.append({
                        "file_name": file.name,
                        "error": f"Processing failed: {e}",
                        "ocr_result": None,
                        "structured": None
                    })
    
    logger.info(f"Batch processing completed. {len(results)} results obtained")
    
    # Display results
    for res in results:
        st.subheader(f"📎 {res['file_name']}")
        if res.get("error"):
            logger.error(f"Error in result for {res['file_name']}: {res['error']}")
            st.error(res["error"])
            if "raw_output" in res:
                st.code(res["raw_output"])
            continue
        
        logger.debug(f"Displaying results for {res['file_name']}")
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
    
    logger.info(f"Prepared {len(all_invoice_data)} invoices for red flag analysis")
    
    # Step 3: Detect Red Flags
    st.subheader("🚨 Red Flag Report")
    logger.info("Starting red flag detection")
    flagged = detect_red_flags(all_invoice_data)
    logger.info(f"Red flag detection completed. {len(flagged)} invoices analyzed")
    
    df = pd.DataFrame(flagged)
    required_cols = ["file_name", "vendor_name", "flag_type", "flag_reason"]
    if all(col in df.columns for col in required_cols):
        logger.debug("Displaying red flag report")
        st.dataframe(df[required_cols], use_container_width=True)
        
        # Step 4: Group Red Flags by Type
        st.subheader("📊 Grouped Red Flags by Type")
        
        # Filter only red flags (exclude green flags)
        red_flags_df = df[df['flag_type'] != '✅ Green Flag'].copy()
        logger.info(f"Found {len(red_flags_df)} red flags out of {len(df)} total invoices")
        
        if not red_flags_df.empty:
            # Group by flag type first
            for flag_type in red_flags_df['flag_type'].unique():
                flag_group = red_flags_df[red_flags_df['flag_type'] == flag_type]
                logger.debug(f"Processing flag type: {flag_type} with {len(flag_group)} instances")
                
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
                    
                    logger.debug(f"Found {len(contact_groups)} contact groups")
                    for contact, group in contact_groups.items():
                        logger.info(f"Shared contact group: {contact} with {len(group)} documents")
                        st.markdown(f"**Shared Contact:** {contact}")
                        group_df = pd.DataFrame(group)
                        display_df = group_df[['file_name', 'vendor_name', 'canonical_vendor', 'flag_reason']].copy()
                        display_df.columns = ['Document', 'Vendor Name', 'Canonical Vendor', 'Issue Detected']
                        st.table(display_df.reset_index(drop=True))
                        st.markdown("---")
                
                elif flag_type == "🚩 Same Format, Different Vendor":
                    # Group by format group ID
                    format_groups = flag_group.groupby('format_group_id')
                    logger.debug(f"Found {len(format_groups)} format groups")
                    for group_id, group in format_groups:
                        if group_id is not None:
                            logger.info(f"Format group {group_id} with {len(group)} documents")
                            st.markdown(f"**Format Group {group_id}**")
                            group_df = pd.DataFrame(group)
                            display_df = group_df[['file_name', 'vendor_name', 'canonical_vendor', 'flag_reason']].copy()
                            display_df.columns = ['Document', 'Vendor Name', 'Canonical Vendor', 'Issue Detected']
                            st.table(display_df.reset_index(drop=True))
                            st.markdown("---")
                
                elif flag_type == "🚩 Different Format, Same Vendor":
                    # Group by canonical vendor
                    vendor_groups = flag_group.groupby('canonical_vendor')
                    logger.debug(f"Found {len(vendor_groups)} vendor groups")
                    for vendor, group in vendor_groups:
                        logger.info(f"Vendor group: {vendor} with {len(group)} documents")
                        st.markdown(f"**Vendor:** {vendor}")
                        display_df = group[['file_name', 'vendor_name', 'canonical_vendor', 'flag_reason']].copy()
                        display_df.columns = ['Document', 'Vendor Name', 'Canonical Vendor', 'Issue Detected']
                        st.table(display_df.reset_index(drop=True))
                        st.markdown("---")
                
                else:
                    # For any other flag types, group by reason
                    reason_groups = flag_group.groupby('flag_reason')
                    logger.debug(f"Found {len(reason_groups)} reason groups")
                    for reason, group in reason_groups:
                        logger.info(f"Reason group: {reason} with {len(group)} documents")
                        st.markdown(f"**Reason:** {reason}")
                        display_df = group[['file_name', 'vendor_name', 'canonical_vendor', 'flag_reason']].copy()
                        display_df.columns = ['Document', 'Vendor Name', 'Canonical Vendor', 'Issue Detected']
                        st.table(display_df.reset_index(drop=True))
                        st.markdown("---")
        else:
            logger.info("No red flags detected - all invoices appear legitimate")
            st.success("🎉 No red flags detected! All invoices appear to be legitimate.")
        
        # Step 5: Download CSV
        logger.debug("Preparing CSV download")
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Download Red Flag Report as CSV",
            csv,
            "red_flags_report.csv",
            "text/csv"
        )
        logger.info("CSV download prepared successfully")
    else:
        logger.warning("Missing required columns in red flag results")
        st.warning("No valid invoice data to display. Please check for errors above.")

elif uploaded_files and not analyze_btn:
    logger.debug("Files uploaded but analysis not started yet")
    st.info("👇 Click 'Analyze Invoices' to start analysis.")
else:
    logger.debug("No files uploaded yet")
    st.info("👈 Upload invoice files from the sidebar to begin.")

logger.info("Application session completed")