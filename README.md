# 🎬 Clip2Text – YouTube Video Summarizer

**Clip2Text** is a web-based application that allows users to summarize YouTube videos using AI. It extracts audio from videos, transcribes them using OpenAI's Whisper model, and generates concise summaries using Hugging Face's transformer models.

---

## 🚀 Features

- 🎥 Extract audio from YouTube videos
- 🧠 Transcribe speech to text using Whisper
- ✨ Summarize transcripts using Hugging Face models (BART, Pegasus, etc.)
- 📜 Download full transcript
- ⚡ Clean and responsive Bootstrap UI

---

## 🛠 Tech Stack

- **Backend:** Python, Flask, Whisper, Hugging Face API, yt-dlp
- **Frontend:** HTML, CSS, Bootstrap 5
- **APIs/Libraries:** `openai-whisper`, `yt-dlp`, `flask-cors`, `torch`, `requests`

## 🔧 Installation & Usage

#✅ Clone the Repository

git clone https://github.com/priyapulakhandam/Clip2Text.git

cd Clip2Text

---

#✅ Install Dependencies

pip install -r requirements.txt

---

#✅ Set Your Hugging Face API Key

Set your API key in your environment variables before running the app:

On Windows:

set HF_API_KEY=your_huggingface_api_key

On macOS/Linux:

export HF_API_KEY=your_huggingface_api_key

---

#✅ Run the Application

python app.py

Then open your browser and go to:

http://localhost:5000

---
