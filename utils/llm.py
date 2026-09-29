import os
import json
import re
import pdfplumber
from groq import Groq
from pydantic import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

def clean_text_unicode(text: str) -> str:
    """Replaces non-standard unicode characters with ASCII equivalents to prevent encoding and PDF rendering issues."""
    if not isinstance(text, str):
        return text
    replacements = {
        '‐': '-',
        '‑': '-',
        '‒': '-',
        '–': '-',
        '—': '-',
        '‘': "'",
        '’': "'",
        '‚': "'",
        '‛': "'",
        '“': '"',
        '”': '"',
        '„': '"',
        '…': '...',
        ' ': ' ',
        ' ': ' ',
        '​': '',
        '﻿': '',
        '•': '*',
    }
    for orig, target in replacements.items():
        text = text.replace(orig, target)
    return text

def sanitize_resume_dict(data: dict) -> dict:
    """Recursively clean strings in resume data dictionary."""
    if isinstance(data, dict):
        return {k: sanitize_resume_dict(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_resume_dict(item) for item in data]
    elif isinstance(data, str):
        return clean_text_unicode(data)
    return data

def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("GROQ_API_KEY")
        except Exception:
            pass
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

def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    hyperlinks = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
            # Extract hyperlink annotations (URIs) that pdfplumber doesn't include in text
            try:
                annots = getattr(page, 'annots', None) or []
                for annot in annots:
                    uri = annot.get('uri')
                    if not uri and isinstance(annot.get('data'), dict):
                        a_dict = annot['data'].get('A', {})
                        if isinstance(a_dict, dict):
                            uri = a_dict.get('URI')
                    if isinstance(uri, bytes):
                        uri = uri.decode('utf-8', errors='ignore')
                    if isinstance(uri, str):
                        uri = uri.strip()
                        if uri and uri not in hyperlinks:
                            hyperlinks.append(uri)
            except Exception as e:
                print(f"Error extracting annotations: {e}")

    # Append extracted hyperlinks so the LLM and regex can pick up LinkedIn/GitHub URLs
    if hyperlinks:
        text += "\n--- Extracted Hyperlinks ---\n"
        for link in hyperlinks:
            text += f"{link}\n"
    return clean_text_unicode(text)

def _normalize_url(url: str, default_domain: str = "") -> str:
    """Ensure URL has https:// prefix and is clean."""
    if not url:
        return ""
    url = url.strip()
    if url.startswith("http://"):
        url = "https://" + url[7:]
    elif not url.startswith("https://"):
        if default_domain and not url.startswith(default_domain):
            url = f"https://{default_domain}/{url.lstrip('/')}"
        else:
            url = f"https://{url.lstrip('/')}"
    return url.rstrip('/')

def parse_resume_text(text: str) -> dict:
    """Uses Groq to parse unstructured resume text into a structured JSON dict with deterministic contact extraction fallback."""
    client = get_groq_client()
    text = clean_text_unicode(text)
    schema = json.dumps(ResumeModel.model_json_schema(), indent=2)
    
    prompt = f"""
    You are an expert resume parser. Extract the following unstructured resume text into a structured JSON format adhering strictly to this JSON schema:
    {schema}
    
    IMPORTANT INSTRUCTIONS:
    - Extract the LinkedIn profile URL (e.g., https://linkedin.com/in/...) and put it in the "linkedin" field.
    - Extract the GitHub profile URL (e.g., https://github.com/...) and put it in the "github" field.
    - These URLs may appear in the text as embedded hyperlinks under "--- Extracted Hyperlinks ---" or inline.
    - If any field is missing or not applicable, provide an empty string or empty list.
    
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
        data = sanitize_resume_dict(data)

        # Guaranteed deterministic regex extraction for LinkedIn if LLM missed it or returned non-URL
        if not data.get("linkedin") or "linkedin.com" not in data.get("linkedin", "").lower():
            linkedin_match = re.search(r'(?:https?://)?(?:www\.)?linkedin\.com/(?:in/)?[a-zA-Z0-9_\-%]+', text, re.IGNORECASE)
            if linkedin_match:
                data["linkedin"] = _normalize_url(linkedin_match.group(0))
        else:
            data["linkedin"] = _normalize_url(data["linkedin"])

        # Guaranteed deterministic regex extraction for GitHub if LLM missed it
        if not data.get("github") or "github.com" not in data.get("github", "").lower():
            github_match = re.search(r'(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9_\-%]+', text, re.IGNORECASE)
            if github_match:
                data["github"] = _normalize_url(github_match.group(0))
        else:
            data["github"] = _normalize_url(data["github"])

        validated_data = ResumeModel(**data)
        return validated_data.model_dump()
    except Exception as e:
        print("Parsing error:", e)
        print("Raw output:", content)
        raise RuntimeError(f"Failed to parse resume text into JSON: {e}")

def tailor_resume_to_jd(base_resume_json: dict, job_description: str) -> dict:
    """Uses Groq to actively tailor and align resume bullet points, summary, skills, and target role to the Job Description."""
    client = get_groq_client()
    cleaned_base = sanitize_resume_dict(base_resume_json)
    cleaned_jd = clean_text_unicode(job_description)
    
    prompt = f"""
You are an elite executive technical resume writer and ATS optimization strategist.
Your task is to tailor and align the candidate's base resume to directly match the target Job Description (JD).

Base Resume JSON:
{json.dumps(cleaned_base, indent=2)}

Target Job Description:
{cleaned_jd}

STRICT TAILORING INSTRUCTIONS:
0. Contact Information (MUST PRESERVE EXACTLY):
   - Copy the following fields EXACTLY as-is from the base resume WITHOUT any changes:
     "name", "phone", "email", "linkedin", "github", "location"
   - Do NOT modify, omit, or rewrite any contact/personal information.

1. Target Job Title (`job_title`):
   - Align the target title with the role specified in the Job Description (e.g. if the JD is for "Senior Backend .NET & Cloud Engineer", adapt the title accordingly).

2. Professional Summary (`summary`):
   - Completely rewrite the 3-4 sentence professional summary.
   - Weave in the exact key technologies, domain keywords, and high-impact accomplishments required by the JD.
   - Highlight proven results (e.g., latency reduction, scalability, microservices, cloud deployments).

3. Technical Skills (`skills`):
   - Actively reorganize and tailor each category: languages, technologies, frontend, databases, tools, concepts.
   - Move JD-required skills to the front of each category.
   - Prominently include technical keywords, frameworks, databases, and cloud tools from the JD that match the candidate's engineering background.

4. Bullet Points (`experience` and `projects`):
   - Rewrite EVERY bullet point to aggressively showcase alignment with the JD requirements.
   - Begin each bullet point with a strong action verb (e.g., "Architected", "Engineered", "Optimized", "Spearheaded", "Streamlined").
   - Frame accomplishments using the X-Y-Z formula: accomplished [X], measured by [Y], by doing [Z].
   - Seamlessly integrate keywords, architectural patterns, and tools from the JD.
   - Retain true company names, dates, and degrees, but reframe and elevate all project duties and achievements.

5. JSON Schema:
   - Output ONLY a valid JSON object strictly conforming to the ResumeModel schema.
   - Do NOT include markdown code fences or explanatory text.
"""
    
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": "You are a world-class technical resume writer. Return strictly valid JSON conforming to the resume schema. Ensure high-impact tailoring across job title, summary, skills, and bullet points."
            },
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.3
    )
    
    content = response.choices[0].message.content
    try:
        data = json.loads(content)
        data = sanitize_resume_dict(data)

        # Force-preserve all contact fields from the base resume to guarantee nothing is lost
        contact_fields = ['name', 'phone', 'email', 'linkedin', 'github', 'location']
        for field in contact_fields:
            base_val = cleaned_base.get(field, '')
            if base_val:
                data[field] = base_val

        validated_data = ResumeModel(**data)
        return validated_data.model_dump()
    except Exception as e:
        print("Tailoring error:", e)
        print("Raw output:", content)
        raise RuntimeError(f"Failed to tailor resume: {e}")
