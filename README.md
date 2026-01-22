# Clip2Text— YouTube Captions → Smart Summary 

Clip2Text is a modern **Streamlit-based web app** that extracts **YouTube captions (manual/auto)** and converts them into a **premium structured summary** using the **Groq LLM API**.

It includes  live logs, timeline steps, video thumbnail preview, and downloadable results.

---

## ✨ Features

  
✅ Captions extraction via **yt-dlp** (manual + auto captions)  
✅ Intelligent transcript cleaning  
✅ Groq-powered summary styles:
- Short & crisp
- Detailed notes
- Study notes (structured)
- Job interview takeaways
- Executive brief


✅ Live logs in UI  
✅ Download outputs:
- Summary `.txt`
- Transcript `.txt`

---

## 🧰 Tech Stack

- **Frontend + Backend:** Streamlit
- **Captions extraction:** `yt-dlp`
- **Text processing:** Python (Regex + cleaning logic)
- **Summarization:** Groq API (`llama-3.1-8b-instant`)
- **Deployment:** Streamlit Community Cloud

---

## 📂 Project Structure

```bash
clip2text-premium/
├── app.py
├── requirements.txt
└── README.md

---
