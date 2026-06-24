import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from groq import Groq
from dotenv import load_dotenv
from fpdf import FPDF
import os
import re

# ==========================================
# LOAD ENV
# ==========================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = None

if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)

# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="YouTube Learning Assistant",
    page_icon="🎓",
    layout="wide"
)

# ==========================================
# HEADER
# ==========================================

st.title("🎓 YouTube Learning Assistant")

st.markdown("""
Turn any YouTube video into:

✅ Smart Notes  
✅ Key Takeaways  
✅ Quiz Questions  
✅ Flashcards  
✅ PDF Study Material
""")

# ==========================================
# VIDEO ID EXTRACTION
# ==========================================

def extract_video_id(url):
    patterns = [
        r"v=([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})"
    ]

    for pattern in patterns:
        match = re.search(pattern, url)

        if match:
            return match.group(1)

    return None

# ==========================================
# PDF GENERATOR
# ==========================================

def create_pdf(content):

    pdf = FPDF()
    pdf.add_page()

    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=11)

    content = content.replace("•", "-")
    content = content.replace("—", "-")
    content = content.replace("–", "-")
    content = content.replace("✓", "[OK]")

    safe_content = (
        content.encode("latin-1", "replace")
        .decode("latin-1")
    )

    for line in safe_content.split("\n"):

        line = line.strip()

        if not line:
            pdf.ln(4)
            continue

        if len(line) > 100:
            chunks = [
                line[i:i+100]
                for i in range(0, len(line), 100)
            ]

            for chunk in chunks:
                pdf.multi_cell(190, 8, chunk)

        else:
            pdf.multi_cell(190, 8, line)

    pdf_path = "youtube_study_notes.pdf"
    pdf.output(pdf_path)

    return pdf_path

# ==========================================
# INPUT
# ==========================================

url = st.text_input("Paste YouTube URL")

# ==========================================
# ANALYZE
# ==========================================

if st.button("🚀 Analyze Video", use_container_width=True):

    video_id = extract_video_id(url)

    if not video_id:
        st.error("Invalid YouTube URL")

    else:

        try:

            # ----------------------------
            # FETCH TRANSCRIPT
            # ----------------------------

            with st.spinner("Loading transcript..."):

                api = YouTubeTranscriptApi()

                transcript = api.fetch(video_id)

                transcript_text = " ".join(
                    [snippet.text for snippet in transcript]
                )

            st.success("Transcript Loaded Successfully")

            # ----------------------------
            # AI GENERATION
            # ----------------------------

            if client is None:

                st.error(
                    "Groq API key not found."
                )

            else:

                with st.spinner(
                    "Generating Study Material..."
                ):

                    prompt = f"""
You are an expert study assistant.

Based on the transcript below, generate:

# SUMMARY
A concise summary.

# KEY TAKEAWAYS
5 important bullet points.

# QUIZ
5 multiple-choice questions with answers.

# FLASHCARDS
10 flashcards using:

Q: Question
A: Answer

Transcript:

{transcript_text}
"""

                    completion = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=0.4,
                    )

                    study_material = (
                        completion.choices[0]
                        .message.content
                    )

                # ----------------------------
                # RESULTS
                # ----------------------------

                st.markdown("---")

                st.subheader("📚 Study Material")

                st.markdown(study_material)

                # ----------------------------
                # PDF EXPORT
                # ----------------------------

                pdf_file = create_pdf(
                    study_material
                )

                with open(pdf_file, "rb") as file:

                    st.download_button(
                        label="📥 Download PDF Notes",
                        data=file.read(),
                        file_name="youtube_study_notes.pdf",
                        mime="application/pdf"
                    )

            # ----------------------------
            # TRANSCRIPT
            # ----------------------------

            with st.expander(
                "📜 View Full Transcript"
            ):

                st.text_area(
                    "Transcript",
                    transcript_text,
                    height=400
                )

        except Exception as e:

            st.error(
                f"Error: {str(e)}"
            )