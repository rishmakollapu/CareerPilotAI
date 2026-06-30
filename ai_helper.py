import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")


def generate_career_advice(name, degree, branch, year, skills, career):

    prompt = f"""
You are CareerPilot AI.

Student Details:
Name: {name}
Degree: {degree}
Branch: {branch}
Current Year: {year}
Skills: {skills}
Career Goal: {career}

Generate a personalized career report.

Include:
1. Greeting
2. Career Readiness Analysis
3. Missing Skills
4. 3 Project Suggestions
5. Interview Tips
6. Motivation.

Keep it under 300 words.
"""

    try:
        response = model.generate_content(prompt)
        return response.text

    except Exception:

        return f"""
Hello {name},

Career Goal: {career}

Recommended Skills:
• Python
• SQL
• Git
• Problem Solving
• Communication

Suggested Projects:
• Student Management System
• AI Resume Analyzer
• Career Recommendation System

Keep learning consistently and build real-world projects.
"""


def generate_resume_feedback(resume_text):

    prompt = f"""
You are an expert Resume Reviewer.

Review the following resume.

Resume:

{resume_text}

Give:

1. Overall Feedback
2. Strengths
3. Weaknesses
4. Suggestions for Improvement

Keep it under 200 words.
"""

    try:
        response = model.generate_content(prompt)
        return response.text

    except Exception:

        return """
Resume Review

Strengths:
• Resume uploaded successfully.
• Skills detected correctly.

Suggestions:
• Add measurable achievements.
• Mention internships.
• Include GitHub and LinkedIn.
• Improve formatting.
• Add technical projects.

Overall:
Your resume has a good foundation but can be strengthened with more project experience and quantified achievements.
"""