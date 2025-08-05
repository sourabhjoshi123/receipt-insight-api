# 🧾 Receipt Insight App

An AI-powered app to extract, categorize, and analyze receipt data using OCR and GPT. Built with **FastAPI** (backend) and **Streamlit** (frontend), with support for image uploads, editable receipt names, insights generation via agents, and smart expense summaries.

---

## 🚀 Features

- 📸 Upload receipts (JPEG, PNG, HEIC supported)
- 🧠 OCR with Tesseract + GPT parsing of line items
- ✏️ Editable receipt names (defaults to filename)
- 🗂 Preview and remove individual line items before saving
- 🧾 Store parsed data into a SQLite database
- 📊 Summary view with breakdowns by category, date, and receipt
- 📈 Trend insights via **OpenAI Jot Agent**
- 🔍 View uploaded receipt images
- 🧹 Admin tab to drop all data
- 📱 Mobile-friendly UI for uploading via camera

---

## 🗂 Project Structure

```
receipt-insight-api/
│
├── app/                      # FastAPI backend
│   ├── main.py               # API routes
│   ├── ocr_gpt.py            # OCR & GPT parsing logic
│   ├── db.py                 # DB models & insert/query
│   ├── models.py             # SQLAlchemy models
│   └── data/receipts/        # Saved receipt images
│
├── services/                 # Agent logic (Jot, etc.)
│   └── jot_analysis.py
│
├── ui/                       # Streamlit frontend
│   └── app.py
│
├── requirements.txt
├── start.sh
└── .env                      # Secrets (e.g., OPENAI_API_KEY)
```

---

## ✅ Requirements

- Python 3.10+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) installed and in your `PATH`
- OpenAI API key (and Jot agent ID if using trend insights)

---

## 🔧 Setup

### 1. Clone the Repo

```bash
git clone https://github.com/your-username/receipt-insight-api.git
cd receipt-insight-api
```

### 2. Create a `.env` file

```env
OPENAI_API_KEY=your-openai-key
JOT_AGENT_ID=your-jot-assistant-id
```

### 3. Install Requirements

```bash
pip install -r requirements.txt
```

Make sure `tesseract` is installed. On Ubuntu:

```bash
sudo apt update && sudo apt install tesseract-ocr
```

### 4. Start Backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Start Frontend (Streamlit)

```bash
cd ui
streamlit run app.py
```

---

## 📌 Deployment Notes

- Streamlit Cloud only hosts the frontend. To host the backend (FastAPI), use:
  - [Render](https://render.com)
  - [Railway](https://railway.app)
  - [Fly.io](https://fly.io)
- Or consolidate both into a single Streamlit app with embedded FastAPI logic (less modular).

---

## 🧠 Future Enhancements

- ✅ Async insights with background threads
- 📱 Camera-based receipt capture
- 🔁 Auto-refresh dashboards
- 🧩 MCP-style orchestration layer
- ☁️ Render / Docker deploy scripts
- 🧪 Add unit tests, linting, CI

---

## 👨‍💻 Author

Built by SJ.
