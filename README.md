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

---
🔧 Installation & Usage
1. Clone the Repository
bash
Copy
Edit
git clone https://github.com/priyapulakhandam/Clip2Text.git
cd Clip2Text
---
3. Install Dependencies
bash
Copy
Edit
pip install -r requirements.txt
---
5. Set Your Hugging Face API Key
Set your API key in your environment variables before running the app:

On Windows:
bash
Copy
Edit
set HF_API_KEY=your_huggingface_api_key
On macOS/Linux:
bash
Copy
Edit
export HF_API_KEY=your_huggingface_api_key
---
4. Run the Application
bash
Copy
Edit
python app.py
Then open your browser and go to:
http://localhost:5000
---

📂 File Structure
bash
Copy
Edit
Clip2Text/
├── app.py            # Flask backend (YouTube, Whisper, Hugging Face)
├── index.html        # Frontend HTML interface
├── requirements.txt  # Python dependencies
---
📜 Example Output
Paste a YouTube video link like:

arduino
Copy
Edit
https://www.youtube.com/watch?v=dQw4w9WgXcQ
---
And get a summary like:

cpp
Copy
Edit
📋 Summary:

🔹 The video explains the concept of...
🔹 It highlights the importance of...
---
