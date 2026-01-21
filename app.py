# Clip2Text Premium - Streamlit Only (Single file)
# Features:
# ✅ Integrated Premium UI (HTML inside app.py)
# ✅ Real animated progress bar
# ✅ Timeline steps (Extracting → Cleaning → Summarizing)
# ✅ Dark glass download buttons matching theme
# ✅ Clip2Text heading in navbar + hero
# ✅ Browser tab icon (YouTube-like)
# ✅ YouTube thumbnail preview + badge under preview

import os
import time
import random
import re
import json
import logging
import requests
import streamlit as st
from dotenv import load_dotenv
from yt_dlp import YoutubeDL
from groq import Groq

# ============================================================
# 🔧 Setup
# ============================================================
load_dotenv()

logging.basicConfig(level=logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

GROQ_KEY = os.getenv("GROQ_KEY") or os.getenv("GROQ_API_KEY") or ""

# ============================================================
# 🧠 UI logger
# ============================================================
def ui_log(box, msg: str):
    print(msg)
    if box is not None:
        st.session_state.logs.append(msg)
        box.code("\n".join(st.session_state.logs[-35:]), language="bash")


# ============================================================
# 🎞️ YouTube helpers (thumbnail preview)
# ============================================================
def get_yt_id(url: str):
    if not url:
        return None
    patterns = [
        r"v=([A-Za-z0-9_-]{11})",
        r"youtu\.be/([A-Za-z0-9_-]{11})",
        r"shorts/([A-Za-z0-9_-]{11})",
        r"embed/([A-Za-z0-9_-]{11})",
    ]
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            return m.group(1)
    return None


def yt_thumbnail(video_id: str) -> str:
    # good quality thumbnail
    return f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"


# ============================================================
# 🧼 Transcript cleaning
# ============================================================
def clean_transcript(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned, prev = [], ""
    for line in lines:
        if "-->" in line:
            continue
        if line.startswith("WEBVTT"):
            continue
        if re.fullmatch(r"\[.*?\]", line):
            continue
        if line != prev:
            cleaned.append(line)
        prev = line
    return "\n".join(cleaned)


def json3_to_text(json3_text: str) -> str:
    data = json.loads(json3_text)
    lines = []
    for event in data.get("events", []):
        segs = event.get("segs")
        if not segs:
            continue
        txt = "".join(seg.get("utf8", "") for seg in segs).replace("\n", " ").strip()
        if txt:
            lines.append(txt)
    return "\n".join(lines)


# ============================================================
# 🌐 Fetch with retry (YouTube captions can 429)
# ============================================================
def fetch_with_retry(url: str, tries: int = 8, log_box=None) -> str:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.youtube.com/",
        "Origin": "https://www.youtube.com",
        "Connection": "keep-alive",
    })

    for attempt in range(tries):
        r = session.get(url, timeout=30)

        if r.status_code == 200:
            return r.text

        if r.status_code == 429:
            wait = (2 ** attempt) + random.uniform(0.5, 2.0)
            ui_log(log_box, f"⚠️ Rate-limited while fetching captions. Retry in {wait:.1f}s ...")
            time.sleep(wait)
            continue

        r.raise_for_status()

    raise RuntimeError("Still rate-limited while fetching captions. Try again later.")


# ============================================================
# 🎬 Extract captions (yt-dlp)
# ============================================================
def pick_best_subtitles(info):
    manual = info.get("subtitles") or {}
    auto = info.get("automatic_captions") or {}
    if manual:
        return manual, "manual"
    if auto:
        return auto, "auto"
    return None, None


def extract_transcript(yt_url: str, prefer_lang="en", log_box=None):
    ui_log(log_box, "🔎 Extracting video metadata...")
    ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True}

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(yt_url, download=False)

    title = info.get("title", "Unknown")
    channel = info.get("uploader", "Unknown")

    subs, subs_type = pick_best_subtitles(info)
    if not subs:
        raise RuntimeError("No captions/subtitles available for this video.")

    lang = prefer_lang if prefer_lang in subs else list(subs.keys())[0]
    ui_log(log_box, f"✅ Captions found ({subs_type}) | Language: {lang}")

    chosen = subs[lang]

    # prefer json3
    sub_url = None
    sub_ext = None
    for entry in chosen:
        if entry.get("ext") == "json3":
            sub_url = entry["url"]
            sub_ext = "json3"
            break

    if not sub_url:
        sub_url = chosen[0]["url"]
        sub_ext = chosen[0].get("ext", "vtt")

    ui_log(log_box, "📥 Fetching captions...")
    raw = fetch_with_retry(sub_url, log_box=log_box)

    if "fmt=json3" in sub_url or sub_ext == "json3":
        transcript = json3_to_text(raw)
    else:
        transcript = raw

    return {
        "title": title,
        "channel": channel,
        "lang": lang,
        "subs_type": subs_type,
        "raw_transcript": transcript
    }


# ============================================================
# ✨ Summarize with Groq (FIXED LIMITS ✅)
# ============================================================
def summarize_with_groq(transcript: str, title: str, style: str, log_box=None) -> str:
    ui_log(log_box, "🧠 Generating summary...")

    transcript = (transcript or "").strip()

    # ✅ limit transcript
    if len(transcript) > 14000:
        ui_log(log_box, f"✂️ Transcript too long ({len(transcript)} chars). Cutting to 14,000 chars.")
        transcript = transcript[:14000]

    client = Groq(api_key=GROQ_KEY)

    # ✅ Different instruction for each style (THIS makes output change)
    style_prompts = {
        "Short & crisp": """
Write a very short summary.
Rules:
- MAX 6 lines total
- MAX 5 bullet key points
- MAX 3 takeaways
- Keep it punchy & simple.
""",
        "Detailed notes": """
Write detailed structured notes.
Rules:
- Use headings and subpoints
- Explain important examples
- Include a mini conclusion at end
- Make it longer and richer than normal.
""",
        "Study notes (structured)": """
Create study notes for students.
Rules:
- Use sections: Overview, Concepts, Definitions, Examples, Common Mistakes, Quick Revision
- Add 5 practice questions at end (with short answers).
""",
        "Job interview takeaways": """
Write output for job interview preparation.
Rules:
- Extract skills, tools, frameworks mentioned
- Add 7 interview questions based on content
- Provide STAR-format answers (short)
""",
        "Executive brief": """
Write like an executive briefing memo.
Rules:
- Start with Decision Summary (3 bullet)
- Key Insights (5 bullet)
- Risks & Assumptions
- Recommendations (actionable)
- Keep tone professional.
""",
    }

    style_instruction = style_prompts.get(style, style_prompts["Short & crisp"])

    prompt = f"""
You are an expert YouTube transcript summarizer.

Video Title: {title}
Selected Style: {style}

IMPORTANT: follow the style rules below exactly:
{style_instruction}

Output must be clearly formatted using Markdown.

Transcript:
{transcript}
"""

    ui_log(log_box, "⚡ Running model...")
    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.45,   # ✅ slightly higher so styles differ
        max_tokens=22000,    # ✅ safe
    )

    ui_log(log_box, "✅ Summary ready.")
    return res.choices[0].message.content.strip()



# ============================================================
# 🎨 Streamlit UI
# ============================================================
st.set_page_config(
    page_title="Clip2Text Premium",
    page_icon="▶️",  # ✅ YouTube-like icon for browser tab
    layout="wide"
)

if "logs" not in st.session_state:
    st.session_state.logs = []

# Hide streamlit default
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.block-container {padding-top: 0 !important; padding-bottom: 2rem;}
</style>
""", unsafe_allow_html=True)

# Premium CSS + Header UI (Clip2Text heading added ✅)
st.markdown(r"""
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet" />
<style>
:root { --primary:#6366f1; --accent:#ec4899; --dark:#1e293b; }
body { background: var(--dark); color: white; }
.bg-animated {
  background: linear-gradient(-45deg, #1e293b, #312e81, #581c87, #1e293b);
  background-size: 400% 400%;
  animation: gradient 15s ease infinite;
}
@keyframes gradient { 0%{background-position:0% 50%;} 50%{background-position:100% 50%;} 100%{background-position:0% 50%;} }
.hero-title{
  font-size: clamp(2.7rem, 6vw, 5.0rem);
  font-weight: 950;
  line-height: 1.05;
  margin-bottom: 0.6rem;
  background: linear-gradient(135deg, #fff, #a5b4fc);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}
.hero-sub{color: rgba(255,255,255,.78); font-size: 1.2rem;}
.brand{
  font-weight: 95000;
  letter-spacing: -0.6px;
  font-size: 1.6rem;
  background: linear-gradient(135deg, #fff, #a5b4fc);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}
.btn-hero{
  padding: 1rem 3rem; border-radius: 50px;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  color: white !important;
  font-weight: 900; text-decoration: none;
  box-shadow: 0 10px 40px rgba(99,102,241,.4);
}
.upload-box{
  background: rgba(255,255,255,.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,.10);
  border-radius: 28px;
  padding: 2.2rem;
  box-shadow: 0 25px 70px rgba(0,0,0,.35);
}
.result-box{
  background: rgba(255,255,255,.06);
  border: 1px solid rgba(255,255,255,.10);
  border-radius: 22px;
  padding: 2rem;
}
.kpi{
  background: rgba(0,0,0,.15);
  border:1px solid rgba(255,255,255,.1);
  border-radius: 18px;
  padding: 14px 16px;
}
.small-muted{opacity:.7;font-size:13px}
.timeline{
  display:flex;
  gap:10px;
  flex-wrap:wrap;
  margin: 10px 0 0 0;
}
.step{
  padding: 9px 14px;
  border-radius: 999px;
  border: 1px solid rgba(255,255,255,.14);
  background: rgba(0,0,0,.18);
  font-size: 13px;
  opacity:.75;
}
.step.active{
  opacity: 1;
  border-color: rgba(255,255,255,.3);
  background: linear-gradient(135deg, rgba(99,102,241,.22), rgba(236,72,153,.18));
}
.glass-download button, .glass-download div[data-testid="stDownloadButton"] button{
  width: 100%;
  background: rgba(255,255,255,.08) !important;
  border: 1px solid rgba(255,255,255,.16) !important;
  border-radius: 16px !important;
  padding: 12px 14px !important;
  color: #fff !important;
  font-weight: 900 !important;
  transition: .25s ease;
}
.glass-download button:hover{
  transform: translateY(-2px);
  border-color: rgba(255,255,255,.28) !important;
}
.badge-yt{
  display:inline-flex;
  gap:8px;
  align-items:center;
  padding:6px 12px;
  border-radius: 999px;
  border: 1px solid rgba(255,255,255,.16);
  background: rgba(0,0,0,.25);
  font-weight: 800;
  font-size: 12px;
  opacity: .92;
}
.badge-dot{
  width:8px; height:8px; border-radius:999px;
  background: #ff0033;
  box-shadow: 0 0 0 3px rgba(255,0,51,.18);
}
</style>

<div class="bg-animated" style="padding: 3.0rem 0 2.0rem 0;">
  <div class="container text-center">
    <div class="hero-title" style="margin-top: .7rem;">Clip2Text</div>
    <h1 class="hero-title" style="margin-top: .7rem;">YouTube URL → Smart Summary</h1>
    <p class="hero-sub">Instant captions • Structured notes • Actionable takeaways</p>
    <div style="margin-top: 1.6rem;">
      <a href="#summarize" class="btn-hero">Start Summarizing</a>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# Upload section container
st.markdown('<div id="summarize"></div>', unsafe_allow_html=True)
st.markdown("""
<div class="container" style="padding: 1.6rem 0 0.8rem 0;">
  <div class="upload-box">
    <h2 style="font-weight:950; font-size: 2.2rem; text-align:center; margin-bottom: .4rem;
      background: linear-gradient(135deg, #fff, #a5b4fc);
      -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
      Summarize Any Video
    </h2>
    <p class="text-center" style="color: rgba(255,255,255,0.6); margin-bottom: 1.3rem;">
      Paste a YouTube URL → preview thumbnail → generate premium summary
    </p>
  </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# ✅ Functional form + Thumbnail Preview + YT Badge
# ============================================================
with st.form("premium_form"):
    yt_url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")

    vid = get_yt_id(yt_url)

    if vid:
        st.markdown("""
        <div style="margin-top: 10px; margin-bottom: 10px;">
          <div class="badge-yt">
            <div class="badge-dot"></div>
            YouTube Preview
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.image(yt_thumbnail(vid), width="stretch")

        st.markdown("""
        <div style="margin-top:8px; margin-bottom:16px;">
          <span class="badge-yt" style="opacity:.85;">
            ▶️ Thumbnail loaded • Ready to summarize
          </span>
        </div>
        """, unsafe_allow_html=True)

    colA, colB = st.columns(2)
    with colA:
        prefer_lang = st.selectbox("Caption language", ["en", "hi", "te", "ta", "ml", "kn", "es", "fr", "de"], index=0)
    with colB:
        style = st.selectbox(
            "Summary style",
            ["Short & crisp", "Detailed notes", "Study notes (structured)", "Job interview takeaways", "Executive brief"]
        )

    colC, colD = st.columns(2)
    with colC:
        show_logs = st.toggle("Show live logs", value=True)
    with colD:
        show_transcript = st.toggle("Show transcript", value=False)

    submitted = st.form_submit_button("✨ Generate Summary")

log_box = st.empty() if show_logs else None

# ============================================================
# ✅ Animated progress bar + timeline
# ============================================================
def animate_progress(progress_bar, start, end, duration=0.8):
    steps = max(1, int((end - start) / 2))
    if steps <= 0:
        progress_bar.progress(end)
        return
    delay = duration / steps
    for p in range(start, end + 1, 2):
        progress_bar.progress(min(p, 100))
        time.sleep(delay)

def render_timeline(active_step: int):
    steps = ["Extracting", "Cleaning", "Summarizing", "Done"]
    chips = []
    for idx, s in enumerate(steps):
        cls = "step active" if idx <= active_step else "step"
        chips.append(f'<div class="{cls}">{"✅ " if idx < active_step else "⏳ " if idx==active_step else "• "} {s}</div>')
    st.markdown(f'<div class="timeline">{"".join(chips)}</div>', unsafe_allow_html=True)


# ============================================================
# ✅ Run summarization
# ============================================================
if submitted:
    if not yt_url.strip():
        st.error("❌ Please enter a valid YouTube URL.")
        st.stop()

    if not GROQ_KEY:
        st.error("❌ Missing GROQ_KEY. Add it in .env file.")
        st.stop()

    st.session_state.logs = []
    t0 = time.time()

    # Progress containers
    st.markdown("### ⚡ Live Workflow")
    progress_bar = st.progress(0)

    # STEP 1 - Extracting
    render_timeline(active_step=0)
    animate_progress(progress_bar, 0, 25, duration=0.8)

    with st.spinner("📥 Extracting captions..."):
        try:
            meta = extract_transcript(yt_url, prefer_lang=prefer_lang, log_box=log_box)
        except Exception as e:
            ui_log(log_box, f"❌ Captions extraction failed: {e}")
            st.error(f"❌ Captions extraction failed: {e}")
            st.stop()

    # STEP 2 - Cleaning
    render_timeline(active_step=1)
    animate_progress(progress_bar, 25, 55, duration=0.8)
    ui_log(log_box, "🧼 Cleaning transcript...")
    cleaned_transcript = clean_transcript(meta["raw_transcript"])

    # STEP 3 - Summarizing
    render_timeline(active_step=2)
    animate_progress(progress_bar, 55, 90, duration=1.0)

    with st.spinner("🧠 Generating summary..."):
        try:
            summary = summarize_with_groq(cleaned_transcript, meta["title"], style, log_box=log_box)
        except Exception as e:
            ui_log(log_box, f"❌ Summary generation failed: {e}")
            st.error(f"❌ Summary generation failed: {e}")
            st.stop()

    # STEP 4 - Done
    animate_progress(progress_bar, 90, 100, duration=0.6)
    render_timeline(active_step=3)

    took = time.time() - t0

    # ============================================================
    # ✅ Result UI
    # ============================================================
    st.markdown("---")
    st.markdown(f"""
    <div class="container">
      <div class="result-box">
        <div style="display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap;">
          <div>
            <div class="small-muted">Video</div>
            <div style="font-size: 22px; font-weight: 950;">{meta["title"]}</div>
            <div class="small-muted">Channel: {meta["channel"]} • Captions: {meta["subs_type"]} • Lang: {meta["lang"]}</div>
          </div>
          <div class="kpi">
            <div class="small-muted">Time Taken</div>
            <div style="font-weight:950;font-size:20px;">{took:.1f}s</div>
          </div>
        </div>
        <hr style="border:none;height:1px;background:rgba(255,255,255,.12);margin:16px 0">
        <div style="font-weight:950; font-size:20px; margin-bottom:10px;">✅ Summary Output</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(summary)

    # Glass download buttons
    st.markdown("### ⬇️ Downloads")
    dl1, dl2 = st.columns(2)
    with dl1:
        st.markdown('<div class="glass-download">', unsafe_allow_html=True)
        st.download_button("⬇️ Download Summary (.txt)", data=summary, file_name="clip2text_summary.txt")
        st.markdown('</div>', unsafe_allow_html=True)

    with dl2:
        st.markdown('<div class="glass-download">', unsafe_allow_html=True)
        st.download_button("⬇️ Download Transcript (.txt)", data=cleaned_transcript, file_name="clip2text_transcript.txt")
        st.markdown('</div>', unsafe_allow_html=True)

    if show_transcript:
        st.text_area("Transcript", cleaned_transcript, height=300)

    st.success("🎉 Completed successfully!")
