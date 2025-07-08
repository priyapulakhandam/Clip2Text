from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import whisper
import tempfile
import uuid
import os
import subprocess
import requests

app = Flask(__name__, static_folder=".")
CORS(app)

UPLOAD_FOLDER = tempfile.gettempdir()
HF_API_KEY =  # Set this in your environment
HF_SUMMARIZATION_MODEL = "facebook/bart-large-cnn"  # You can change to long-t5, pegasus, etc.

# Load Whisper model (base for balance of speed and accuracy)
whisper_model = whisper.load_model("base")


@app.route("/")
def serve_index():
    return send_from_directory(".", "index.html")


@app.route("/api/summarize", methods=["POST"])
def summarize_video():
    try:
        data = request.get_json()
        url = data.get("url")

        if not url:
            return jsonify({"error": "YouTube URL is required"}), 400

        print(f"🎥 Downloading video: {url}")
        audio_path, title = download_audio_from_youtube(url)

        print("🧠 Transcribing audio...")
        segments = transcribe_audio(audio_path)

        print("📜 Saving transcript...")
        file_id = str(uuid.uuid4())
        transcript_path = save_transcript_to_file(segments, file_id)

        print("🤖 Summarizing via Hugging Face API...")
        summary = summarize_via_hf(segments)

        return jsonify({
            "title": title,
            "summary": summary,
            "transcript_download": f"/download/{file_id}.txt"
        })

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


def download_audio_from_youtube(url):
    unique_id = str(uuid.uuid4())
    output_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}.%(ext)s")
    audio_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}.mp3")

    command = [
        "yt-dlp",
        "-f", "bestaudio",
        "--extract-audio",
        "--audio-format", "mp3",
        "--output", output_path,
        url
    ]
    subprocess.run(command, check=True)

    title = "Video"
    try:
        result = subprocess.run(["yt-dlp", "--get-title", url], capture_output=True, text=True)
        if result.returncode == 0:
            title = result.stdout.strip()
    except:
        pass

    return audio_path, title


def transcribe_audio(audio_path):
    result = whisper_model.transcribe(audio_path, fp16=False, verbose=False)
    return result["segments"]


def save_transcript_to_file(segments, file_id):
    filepath = os.path.join(UPLOAD_FOLDER, f"{file_id}.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        for seg in segments:
            timestamp = seconds_to_timestamp(seg['start'])
            f.write(f"[{timestamp}] {seg['text'].strip()}\n")
    return filepath


def seconds_to_timestamp(seconds):
    mins, secs = divmod(int(seconds), 60)
    hrs, mins = divmod(mins, 60)
    return f"{hrs:02}:{mins:02}:{secs:02}"


def summarize_via_hf(segments):
    if not HF_API_KEY:
        raise ValueError("Hugging Face API key not set (HF_API_KEY)")

    full_text = " ".join([seg["text"].strip() for seg in segments])
    max_chunk_size = 3800  # Characters per chunk
    overlap = 400
    summaries = []

    # Chunk large transcript into overlapping blocks
    start = 0
    while start < len(full_text):
        end = start + max_chunk_size
        chunk = full_text[start:end]
        summary = hf_summarize_chunk(chunk)
        summaries.append(summary)
        start += max_chunk_size - overlap

    final_summary = "\n\n".join(f"🔹 {s.strip()}" for s in summaries)
    return final_summary


def hf_summarize_chunk(text):
    response = requests.post(
        f"https://api-inference.huggingface.co/models/{HF_SUMMARIZATION_MODEL}",
        headers={"Authorization": f"Bearer {HF_API_KEY}"},
        json={"inputs": text.strip()}
    )

    if response.status_code != 200:
        raise RuntimeError(f"HF API error: {response.status_code} - {response.text}")

    result = response.json()
    if isinstance(result, list) and "summary_text" in result[0]:
        return result[0]["summary_text"]
    else:
        return "[No summary returned]"


@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
