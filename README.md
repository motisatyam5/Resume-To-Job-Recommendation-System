# Resume to Job Recommendation System

## 📌 Overview
This project is a Streamlit-based web app that recommends jobs based on resume analysis using keyword and fuzzy matching.

## 🚀 Features
- Upload Resume (PDF, DOCX, TXT)
- Automatic Skill Detection
- Job Recommendations with Match Score
- Missing Skills Identification
- Download Results (CSV & JSON)

## 🛠 Tech Stack
- Python
- Streamlit
- Pandas
- PyPDF2
- python-docx

## ▶️ How to Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 📊 How It Works
- Extracts resume text
- Detects skills using keyword + fuzzy matching
- Matches with job roles
- Calculates match score

## 🔮 Future Improvements
- NLP-based recommendation (spaCy/BERT)
- Larger job dataset
- Resume ranking system
- OCR for scanned resumes
