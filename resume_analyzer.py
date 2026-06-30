from ai_helper import generate_resume_feedback
import pdfplumber

def analyze_resume(filepath):
    text = ""

    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    score = 0

    skills = []

    keywords = [
        "python",
        "java",
        "sql",
        "html",
        "css",
        "javascript",
        "flask",
        "mongodb",
        "git",
        "api"
    ]

    for keyword in keywords:
        if keyword.lower() in text.lower():
            skills.append(keyword)
            score += 10

    score = min(score, 100)
    ai_feedback = generate_resume_feedback(text)
    
    missing = []

    for keyword in keywords:
        if keyword not in skills:
            missing.append(keyword)

    return {
        "score": score,
        "skills": skills,
        "missing": missing,
        "feedback": ai_feedback
    }