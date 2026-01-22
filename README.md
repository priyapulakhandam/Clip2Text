# Clip2Text— YouTube Captions → Smart Summary 

Clip2Text is a modern **Streamlit-based web app** that extracts **YouTube captions (manual/auto)** and converts them into a **premium structured summary** using the **Groq LLM API**.

It includes  live logs, timeline steps, video thumbnail preview, and downloadable results.

---

  
## ✨ Key Features

- **YouTube Captions Extraction:** Automatically fetches subtitles using **yt-dlp**, supporting both **manual captions** and **auto-generated captions**.
- **Transcript Processing:** Cleans and de-duplicates subtitle text for smoother and more accurate summarization.
- **Multiple Summary Styles (Groq-powered):**
  - Short & Crisp (quick overview)
  - Detailed Notes (in-depth explanation)
  - Study Notes (structured learning format)
  - Job Interview Takeaways (skills + Q&A focused)
  - Executive Brief (decision-style summary)

- **Live Workflow Logs:** Real-time logs displayed in the UI for transparent processing and debugging.
- **Downloadable Results:** Export outputs instantly:
  - Summary as `.txt`
  - Transcript as `.txt`


---

## 🧰 Tech Stack

- **Frontend + Backend:** Streamlit
- **Captions extraction:** `yt-dlp`
- **Text processing:** Python (Regex + cleaning logic)
- **Summarization:** Groq API (`llama-3.1-8b-instant`)
- **Deployment:** Streamlit Community Cloud

---

## 📂 Project Structure

clip2text-premium/
├── app.py
├── requirements.txt
└── README.md

