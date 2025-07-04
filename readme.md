# 📄 Invoice Red Flag Detection - POC

This project is a Streamlit-based Proof of Concept (POC) that analyzes uploaded invoice documents (PDFs or images) and identifies potential **red flags** using OCR, LLMs, and structural comparison logic.

---

## ✅ Red Flags Detected

| Type                                          | Description                                               |
| --------------------------------------------- | --------------------------------------------------------- |
| 🚩 **Same contact info, different vendors**   | Identifies vendors sharing the same phone number or email |
| 🚩 **Same invoice format, different vendors** | Detects reused templates/layouts among different vendors  |
| 🚩 **Different format, same vendor**          | Flags inconsistent layouts for the same vendor            |
| ✅ **Green Flag**                             | Clean invoices with no detected anomalies                 |

---

## 🧠 Features

- Upload and analyze multiple invoice PDFs or images
- Extract vendor name, contact details, invoice layout using OCR + GPT
- Flag suspicious patterns
- Preview raw OCR and structured fields
- Download full red flag report as CSV
- Human-in-the-loop ready: extendable for manual correction

---

## 📦 Project Structure

```
invoice_red_flag_poc/
├── app.py                  # Main Streamlit app
├── requirements.txt
├── data/uploads/           # Uploaded invoice files
├── src/
│   ├── extractor.py        # PDF/Image to OCR
│   ├── llm_extractor.py    # LLM-based structured field extractor
│   ├── red_flags.py        # Red flag detection logic
│   ├── analyzer.py         # Layout similarity engine
│   ├── utils.py            # File handling and helpers
│   └── prompts.py          # Prompt templates for LLM
```

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the Repo

```bash
git clone https://github.com/yourusername/invoice-red-flag-poc.git
cd invoice-red-flag-poc
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate    # or venv\Scripts\activate on Windows
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Set OpenAI API Key

```bash
export OPENAI_API_KEY=sk-...       # Linux/macOS
# OR
set OPENAI_API_KEY=sk-...          # Windows
```

### 5️⃣ Run the App

```bash
streamlit run app.py
```

---

## 🔍 Example Use Case

Upload invoice files → see extracted vendor/contact info → detect suspicious similarities or inconsistencies → export full audit report for internal review or escalation.

---

## 📤 Output

- Interactive flag report (Streamlit table)
- Downloadable `red_flags_report.csv`

---

## 🛠 Tech Stack

- **Streamlit** (UI)
- **pytesseract** + **pdf2image** (OCR)
- **OpenAI GPT-4** (extraction from noisy OCR)
- **fuzzywuzzy**, **sklearn**, **difflib** (comparison logic)

---

## 🚀 Next Ideas

- Add embedded image previews
- Integrate LayoutLM or DocTR for visual embedding
- Deploy to Streamlit Cloud / Dockerize

---

## ✍️ Maintainers

Built and maintained by the [TailoredAI](https://tailoredai.co) team.
