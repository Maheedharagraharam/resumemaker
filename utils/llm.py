import os
import json
import pdfplumber
from groq import Groq
from pydantic import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set")
    return Groq(api_key=api_key)

class Experience(BaseModel):
    company: str = ""
    title: str = ""
    dates: str = ""
    location: str = ""
    bullets: List[str] = Field(default_factory=list)

class Project(BaseModel):
    name: str = ""
    technologies: str = ""
    dates: str = ""
    bullets: List[str] = Field(default_factory=list)

class Education(BaseModel):
    institution: str = ""
    degree: str = ""
    dates: str = ""

class Skills(BaseModel):
    languages: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    frontend: List[str] = Field(default_factory=list)
    databases: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    concepts: List[str] = Field(default_factory=list)

class ResumeModel(BaseModel):
    name: str = ""
    job_title: str = ""
    phone: str = ""
    email: str = ""
    linkedin: str = ""
    github: str = ""
    location: str = ""
    summary: str = ""
    experience: List[Experience] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    skills: Skills = Field(default_factory=Skills)

def parse_resume_text(text: str) -> dict:
    """Uses Groq to parse unstructured resume text into a structured JSON dict."""
    client = get_groq_client()
    schema = json.dumps(ResumeModel.model_json_schema(), indent=2)
    
    prompt = f"""
    You are an expert resume parser. Extract the following unstructured resume text into a structured JSON format adhering strictly to this JSON schema:
    {schema}
    
    If any field is missing or not applicable, provide an empty string or empty list.
    
    Resume Text:
    {text}
    """
    
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that outputs ONLY valid JSON based on the schema requested."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    content = response.choices[0].message.content
    try:
        data = json.loads(content)
        validated_data = ResumeModel(**data)
        return validated_data.model_dump()
    except Exception as e:
        print("Parsing error:", e)
        print("Raw output:", content)
        raise RuntimeError(f"Failed to parse resume text into JSON: {e}")

def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def tailor_resume_to_jd(base_resume_json: dict, job_description: str) -> dict:
    """Uses Groq to rewrite resume bullet points and summary based on the Job Description."""
    client = get_groq_client()
    
    prompt = f"""
    You are an expert career coach and resume writer. 
    I will provide you with a base resume in JSON format and a Job Description.
    Your task is to tailor the resume to perfectly match the Job Description.
    
    Rules:
    1. Rewrite the "summary" to highlight skills relevant to the JD.
    2. Rewrite the "bullets" for each "experience" and "project" to emphasize achievements and keywords present in the JD. Maintain a professional tone.
    3. Do NOT make up fake experiences. Only reframe existing experiences.
    4. Keep the exact same JSON structure. Output ONLY valid JSON matching the provided structure.
    
    Base Resume JSON:
    {json.dumps(base_resume_json, indent=2)}
    
    Job Description:
    {job_description}
    """
    
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": "You are a precise JSON formatting assistant. Return ONLY valid JSON."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    content = response.choices[0].message.content
    try:
        data = json.loads(content)
        validated_data = ResumeModel(**data)
        return validated_data.model_dump()
    except Exception as e:
        print("Tailoring error:", e)
        print("Raw output:", content)
        raise RuntimeError("Failed to tailor resume.")

