import os
import subprocess
import shutil

def escape_latex(text: str) -> str:
    """Escapes characters that are special in LaTeX."""
    if not isinstance(text, str):
        return str(text)
    
    chars = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
        '\\': r'\textbackslash{}'
    }
    for char, escaped in chars.items():
        text = text.replace(char, escaped)
    return text

def format_experience(experiences: list) -> str:
    latex_str = ""
    for exp in experiences:
        company = escape_latex(exp.get("company", ""))
        title = escape_latex(exp.get("title", ""))
        dates = escape_latex(exp.get("dates", ""))
        location = escape_latex(exp.get("location", ""))
        
        latex_str += f"\\subsection*{{{title} \\hfill {dates}}}\n"
        latex_str += f"\\textbf{{{company}, {location}}}\n\n"
        latex_str += "\\begin{itemize}[leftmargin=*, nosep]\n"
        for bullet in exp.get("bullets", []):
            latex_str += f"    \\item {escape_latex(bullet)}\n"
        latex_str += "\\end{itemize}\n\n"
    return latex_str

def format_projects(projects: list) -> str:
    latex_str = ""
    if not projects:
        return ""
    for proj in projects:
        name = escape_latex(proj.get("name", ""))
        tech = escape_latex(proj.get("technologies", ""))
        dates = escape_latex(proj.get("dates", ""))
        
        latex_str += f"\\subsection*{{{name} \\hfill {dates}}}\n"
        latex_str += f"\\textbf{{{tech}}}\n\n"
        latex_str += "\\begin{itemize}[leftmargin=*, nosep]\n"
        for bullet in proj.get("bullets", []):
            latex_str += f"    \\item {escape_latex(bullet)}\n"
        latex_str += "\\end{itemize}\n\n"
    return latex_str

def format_education(education: list) -> str:
    latex_str = ""
    for edu in education:
        institution = escape_latex(edu.get("institution", ""))
        degree = escape_latex(edu.get("degree", ""))
        dates = escape_latex(edu.get("dates", ""))
        
        latex_str += f"\\textbf{{{degree}}} \\hfill {dates} \\\\\n"
        latex_str += f"{institution}\n\n"
    return latex_str

def generate_pdf_reportlab(resume_data: dict, output_pdf_path: str) -> str:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'ResumeTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        alignment=1,
        textColor=colors.HexColor('#111827')
    )
    subtitle_style = ParagraphStyle(
        'ResumeSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        alignment=1,
        textColor=colors.HexColor('#374151')
    )
    contact_style = ParagraphStyle(
        'ResumeContact',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        alignment=1,
        textColor=colors.HexColor('#4B5563')
    )
    section_style = ParagraphStyle(
        'ResumeSection',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        spaceBefore=8,
        spaceAfter=2,
        textColor=colors.HexColor('#1E3A8A')
    )
    body_style = ParagraphStyle(
        'ResumeBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#1F2937')
    )
    bullet_style = ParagraphStyle(
        'ResumeBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        leftIndent=15,
        firstLineIndent=-10,
        textColor=colors.HexColor('#1F2937')
    )
    subhead_left = ParagraphStyle(
        'SubheadLeft',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#111827')
    )
    subhead_right = ParagraphStyle(
        'SubheadRight',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        alignment=2,
        textColor=colors.HexColor('#4B5563')
    )

    story = []

    # Header
    name = resume_data.get('name', 'Name')
    job_title = resume_data.get('job_title', 'Software Engineer')
    story.append(Paragraph(name.upper(), title_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph(job_title, subtitle_style))
    story.append(Spacer(1, 4))

    contacts = []
    if resume_data.get('phone'): contacts.append(resume_data['phone'])
    if resume_data.get('email'): contacts.append(resume_data['email'])
    if resume_data.get('linkedin'): contacts.append("LinkedIn: " + resume_data['linkedin'])
    if resume_data.get('github'): contacts.append("GitHub: " + resume_data['github'])
    if resume_data.get('location'): contacts.append(resume_data['location'])
    
    if contacts:
        story.append(Paragraph(" | ".join(contacts), contact_style))
    story.append(Spacer(1, 6))

    def add_section(title):
        story.append(Paragraph(title.upper(), section_style))
        story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor('#9CA3AF'), spaceAfter=4, spaceBefore=1))

    # Summary
    if resume_data.get('summary'):
        add_section("Professional Summary")
        story.append(Paragraph(resume_data['summary'], body_style))
        story.append(Spacer(1, 4))

    # Technical Skills
    skills = resume_data.get('skills', {})
    skill_entries = []
    if skills.get('languages'): skill_entries.append(('Languages:', ", ".join(skills['languages'])))
    if skills.get('technologies'): skill_entries.append(('Technologies:', ", ".join(skills['technologies'])))
    if skills.get('frontend'): skill_entries.append(('Frontend:', ", ".join(skills['frontend'])))
    if skills.get('databases'): skill_entries.append(('Databases:', ", ".join(skills['databases'])))
    if skills.get('tools'): skill_entries.append(('Cloud & Tools:', ", ".join(skills['tools'])))
    if skills.get('concepts'): skill_entries.append(('Concepts:', ", ".join(skills['concepts'])))

    if skill_entries:
        add_section("Technical Skills")
        for label, val in skill_entries:
            story.append(Paragraph(f"<b>{label}</b> {val}", body_style))
        story.append(Spacer(1, 4))

    # Professional Experience
    experiences = resume_data.get('experience', [])
    if experiences:
        add_section("Professional Experience")
        for exp in experiences:
            title = exp.get('title', '')
            dates = exp.get('dates', '')
            company = exp.get('company', '')
            location = exp.get('location', '')
            
            loc_str = f" | {location}" if location else ""
            header_table = Table(
                [[Paragraph(f"<b>{title}</b> — <i>{company}</i>", subhead_left), Paragraph(f"{dates}{loc_str}", subhead_right)]],
                colWidths=[380, 160]
            )
            header_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ('TOPPADDING', (0,0), (-1,-1), 2),
            ]))
            story.append(header_table)
            
            for bullet in exp.get('bullets', []):
                story.append(Paragraph(f"• &nbsp; {bullet}", bullet_style))
            story.append(Spacer(1, 4))

    # Projects
    projects = resume_data.get('projects', [])
    if projects:
        add_section("Projects")
        for proj in projects:
            pname = proj.get('name', '')
            dates = proj.get('dates', '')
            tech = proj.get('technologies', '')
            
            proj_table = Table(
                [[Paragraph(f"<b>{pname}</b>" + (f" ({tech})" if tech else ""), subhead_left), Paragraph(dates, subhead_right)]],
                colWidths=[380, 160]
            )
            proj_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ('TOPPADDING', (0,0), (-1,-1), 2),
            ]))
            story.append(proj_table)
            for bullet in proj.get('bullets', []):
                story.append(Paragraph(f"• &nbsp; {bullet}", bullet_style))
            story.append(Spacer(1, 4))

    # Education
    education = resume_data.get('education', [])
    if education:
        add_section("Education")
        for edu in education:
            deg = edu.get('degree', '')
            dates = edu.get('dates', '')
            inst = edu.get('institution', '')
            
            edu_table = Table(
                [[Paragraph(f"<b>{deg}</b> — {inst}", subhead_left), Paragraph(dates, subhead_right)]],
                colWidths=[380, 160]
            )
            edu_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ('TOPPADDING', (0,0), (-1,-1), 2),
            ]))
            story.append(edu_table)
            story.append(Spacer(1, 4))

    doc.build(story)
    return output_pdf_path

def generate_pdf(resume_data: dict, output_dir: str = "data") -> str:
    """
    Takes JSON resume data, injects into template, and generates PDF.
    Returns the path to the generated PDF.
    """
    template_path = os.path.join("templates", "resume.tex")
    
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()
        
    # Replace simple variables
    template_content = template_content.replace("<<NAME>>", escape_latex(resume_data.get("name", "Name")))
    template_content = template_content.replace("<<TITLE>>", escape_latex(resume_data.get("job_title", "Software Engineer")))
    template_content = template_content.replace("<<PHONE>>", escape_latex(resume_data.get("phone", "")))
    template_content = template_content.replace("<<EMAIL>>", escape_latex(resume_data.get("email", "email@example.com")))
    template_content = template_content.replace("<<LINKEDIN>>", resume_data.get("linkedin", "#"))
    template_content = template_content.replace("<<GITHUB>>", resume_data.get("github", "#"))
    template_content = template_content.replace("<<LOCATION>>", escape_latex(resume_data.get("location", "")))
    template_content = template_content.replace("<<SUMMARY>>", escape_latex(resume_data.get("summary", "")))
    
    # Replace skills
    skills = resume_data.get("skills", {})
    template_content = template_content.replace("<<SKILLS_LANGUAGES>>", escape_latex(", ".join(skills.get("languages", []))))
    template_content = template_content.replace("<<SKILLS_TECHNOLOGIES>>", escape_latex(", ".join(skills.get("technologies", []))))
    template_content = template_content.replace("<<SKILLS_FRONTEND>>", escape_latex(", ".join(skills.get("frontend", []))))
    template_content = template_content.replace("<<SKILLS_DATABASES>>", escape_latex(", ".join(skills.get("databases", []))))
    template_content = template_content.replace("<<SKILLS_TOOLS>>", escape_latex(", ".join(skills.get("tools", []))))
    template_content = template_content.replace("<<SKILLS_CONCEPTS>>", escape_latex(", ".join(skills.get("concepts", []))))
    
    # Replace sections
    template_content = template_content.replace("<<EXPERIENCE_SECTION>>", format_experience(resume_data.get("experience", [])))
    
    projects_content = format_projects(resume_data.get("projects", []))
    if not projects_content:
        # Remove projects section entirely if no projects
        template_content = template_content.replace("% Projects\n\\section*{Projects}\n<<PROJECTS_SECTION>>\n\n", "")
    else:
        template_content = template_content.replace("<<PROJECTS_SECTION>>", projects_content)
        
    template_content = template_content.replace("<<EDUCATION_SECTION>>", format_education(resume_data.get("education", [])))
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    tex_path = os.path.join(output_dir, "generated_resume.tex")
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(template_content)
        
    pdf_path = os.path.join(output_dir, "generated_resume.pdf")

    # If pdflatex is available, use it; otherwise, fall back to ReportLab
    pdflatex_bin = shutil.which("pdflatex")
    if pdflatex_bin:
        try:
            subprocess.run(
                [pdflatex_bin, "-interaction=nonstopmode", "-output-directory", output_dir, tex_path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return pdf_path
        except subprocess.CalledProcessError as e:
            print("LaTeX Compilation Error, falling back to direct PDF generator:", e.stderr.decode("utf-8", errors="ignore"))
        except Exception as e:
            print("pdflatex execution failed, falling back to direct PDF generator:", e)

    # Fallback to direct Python PDF generation
    return generate_pdf_reportlab(resume_data, pdf_path)

