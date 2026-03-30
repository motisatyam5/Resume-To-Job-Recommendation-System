"""
Streamlit app: Resume -> Job Recommendation
File: app.py

Features:
- Upload resume (PDF, .docx, .txt)
- Extract text (PyPDF2, python-docx)
- Detect skills by keyword and fuzzy matching
- Recommend jobs from a small built-in job database with match scores
- Show detected skills, matched jobs with reasoning, and downloadable report

Run:
1. pip install -r requirements.txt
   (requirements: streamlit, PyPDF2, python-docx, pandas)
2. streamlit run app.py

Notes / Limitations:
- This is a lightweight prototype using keyword matching; replacing with an NLP model (spaCy) or embeddings will improve accuracy.
- OCR (images in PDF) is not supported here. For scanned resumes, add pytesseract.
"""

import io
import re
import json
import base64
from typing import List, Dict, Tuple, Set

import streamlit as st
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
from difflib import SequenceMatcher

# -------------------------
# Configuration / DB
# -------------------------

# Minimal skills lexicon (extendable)
SKILLS = [
    "python", "java", "c++", "c#", "r", "sql", "nosql", "mysql", "postgresql",
    "mongodb", "hadoop", "spark", "pyspark", "scala", "kafka", "airflow", "hive",
    "aws", "gcp", "azure", "docker", "kubernetes", "terraform",
    "pandas", "numpy", "matplotlib", "seaborn", "scikit-learn", "tensorflow", "pytorch",
    "keras", "nlp", "computer vision", "opencv", "deep learning", "machine learning",
    "data engineering", "data analyst", "etl", "power bi", "tableau", "excel",
    "javascript", "html", "css", "react", "node", "django", "flask",
    "git", "linux", "bash", "spark sql", "bigquery", "redshift", "presto",
    "statistical analysis", "time series", "nlp", "transformers", "llm"
]

# Minimal job database. In production store in a DB or JSON file.
JOBS = [
    {
        "title": "Data Engineer",
        "required_skills": ["python", "spark", "hadoop", "airflow", "sql", "aws"]
    },
    {
        "title": "Machine Learning Engineer",
        "required_skills": ["python", "tensorflow", "pytorch", "scikit-learn", "ml", "docker"]
    },
    {
        "title": "Data Analyst",
        "required_skills": ["sql", "excel", "tableau", "power bi", "pandas"]
    },
    {
        "title": "Full Stack Developer",
        "required_skills": ["javascript", "html", "css", "react", "node"]
    },
    {
        "title": "DevOps Engineer",
        "required_skills": ["docker", "kubernetes", "aws", "terraform", "linux"]
    },
    {
        "title": "NLP Engineer",
        "required_skills": ["nlp", "python", "transformers", "pytorch", "tensorflow"]
    }
]

# -------------------------
# Utility functions
# -------------------------

def read_pdf(file_stream: io.BytesIO) -> str:
    try:
        reader = PdfReader(file_stream)
        text = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
        return "\n".join(text)
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""


def read_docx(file_stream: io.BytesIO) -> str:
    try:
        doc = Document(file_stream)
        text = []
        for para in doc.paragraphs:
            text.append(para.text)
        return "\n".join(text)
    except Exception as e:
        st.error(f"Error reading DOCX: {e}")
        return ""


def read_txt(file_stream: io.BytesIO) -> str:
    try:
        return file_stream.getvalue().decode(errors="ignore")
    except Exception as e:
        st.error(f"Error reading TXT: {e}")
        return ""


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s+\-._]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def detect_skills(text: str, skills_lexicon: List[str], fuzzy_thresh: float = 0.85) -> Set[str]:
    found = set()
    t = text
    for skill in skills_lexicon:
        # exact word
        pattern = r"\\b" + re.escape(skill.lower()) + r"\\b"
        if re.search(pattern, t):
            found.add(skill)
            continue
        # fuzzy check against short phrases
        for chunk in t.split():
            if similar(skill.lower(), chunk) >= fuzzy_thresh:
                found.add(skill)
                break
    return found


def score_job_match(candidate_skills: Set[str], job_required: List[str]) -> Tuple[float, List[str], List[str]]:
    required = set([s.lower() for s in job_required])
    candidate = set([s.lower() for s in candidate_skills])
    matched = sorted(list(required & candidate))
    missing = sorted(list(required - candidate))
    score = 0.0
    if required:
        score = len(matched) / len(required)
    return score, matched, missing

# -------------------------
# Streamlit UI
# -------------------------

st.set_page_config(page_title="Resume → Job Recommender", page_icon="📄🔎", layout="wide")
st.title("📄 → 🔎 Resume to Job Recommender")
st.markdown("Upload a resume and get job recommendations based on detected skills.")

with st.sidebar:
    st.header("Settings")
    top_k = st.number_input("Number of job recommendations", min_value=1, max_value=10, value=5)
    fuzzy_thresh = st.slider("Fuzzy matching threshold", min_value=0.6, max_value=1.0, value=0.85, step=0.01)
    show_raw = st.checkbox("Show extracted raw text", value=False)
    expand_skills = st.checkbox("Show full skills lexicon", value=False)

uploaded_file = st.file_uploader("Upload resume (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])

if uploaded_file is not None:
    file_bytes = uploaded_file.read()
    file_stream = io.BytesIO(file_bytes)
    filename = uploaded_file.name.lower()

    if filename.endswith(".pdf"):
        text = read_pdf(file_stream)
    elif filename.endswith(".docx"):
        # python-docx expects a file-like object at start
        file_stream.seek(0)
        text = read_docx(file_stream)
    else:
        file_stream.seek(0)
        text = read_txt(file_stream)

    if not text:
        st.warning("Couldn't extract text from the uploaded file. Try a different format or check file integrity.")
    else:
        normalized = normalize_text(text)

        if show_raw:
            st.subheader("Extracted resume text")
            st.text_area("Raw text", value=text, height=300)

        # Detect skills
        detected = detect_skills(normalized, SKILLS, fuzzy_thresh=fuzzy_thresh)

        st.subheader("🔎 Detected skills")
        if detected:
            st.write(sorted(detected))
        else:
            st.info("No skills detected from the built-in lexicon. Try lowering fuzzy threshold or expand the lexicon.")

        if expand_skills:
            st.caption("Current skills lexicon (edit in app code to extend)")
            st.write(sorted(SKILLS))

        # Match jobs
        results = []
        for job in JOBS:
            score, matched, missing = score_job_match(detected, job["required_skills"])
            results.append({
                "title": job["title"],
                "score": round(score, 3),
                "matched_skills": ", ".join(matched) if matched else "",
                "missing_skills": ", ".join(missing) if missing else ""
            })

        df = pd.DataFrame(results).sort_values(by="score", ascending=False)

        st.subheader("📋 Job recommendations")
        if df['score'].max() == 0:
            st.warning("No good matches found. Consider expanding the skills lexicon or adding more skills to your resume.")

        top_df = df.head(top_k)
        st.table(top_df)

        # Provide explanation cards
        st.subheader("Why these recommendations?")
        for idx, row in top_df.iterrows():
            st.markdown(f"**{row['title']}** — match score: **{row['score']}**")
            st.write(f"Matched skills: {row['matched_skills'] or 'None'}")
            st.write(f"Missing skills: {row['missing_skills'] or 'None'}")
            st.markdown("---")

        # Downloadable report
        st.subheader("📥 Download report")
        report = {
            "filename": uploaded_file.name,
            "detected_skills": sorted(list(detected)),
            "recommendations": df.to_dict(orient='records')
        }
        report_bytes = json.dumps(report, indent=2).encode()
        st.download_button("Download JSON report", data=report_bytes, file_name="resume_recommendations.json", mime="application/json")

        # Also offer CSV of recommendations
        csv_bytes = df.to_csv(index=False).encode()
        st.download_button("Download CSV (recommendations)", data=csv_bytes, file_name="recommendations.csv", mime="text/csv")

        st.success("Done — review the recommendations and adjust settings from the sidebar to refine results.")

else:
    st.info("Upload a resume file to begin. The app accepts PDF, DOCX and TXT files.")

# -------------------------
# Optional: Admin / demo data
# -------------------------

st.markdown("---")

