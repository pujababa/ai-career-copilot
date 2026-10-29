"""
ATS Resume Analyzer Engine for AI Career Copilot
Provides realistic, transparent, and accurate resume analysis, section detection,
contact information extraction, skill matching, job description comparison,
and dynamic scoring without hardcoded/inflated results.
"""

import os
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Tuple

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import docx
except Exception:
    docx = None


# Comprehensive Skill Catalog with Canonical Names & Aliases
TECH_SKILLS_MAP = {
    # Programming Languages
    "python": "Python",
    "python3": "Python",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "java": "Java",
    "c++": "C++",
    "cpp": "C++",
    "c#": "C#",
    "csharp": "C#",
    "ruby": "Ruby",
    "go": "Go",
    "golang": "Go",
    "rust": "Rust",
    "php": "PHP",
    "swift": "Swift",
    "kotlin": "Kotlin",
    "scala": "Scala",
    "dart": "Dart",
    "r": "R",
    "matlab": "MATLAB",
    "sql": "SQL",
    "html": "HTML",
    "html5": "HTML5",
    "css": "CSS",
    "css3": "CSS3",

    # Web & Frameworks
    "react": "React",
    "reactjs": "React",
    "react.js": "React",
    "angular": "Angular",
    "angularjs": "Angular",
    "vue": "Vue",
    "vuejs": "Vue",
    "vue.js": "Vue",
    "nextjs": "Next.js",
    "next.js": "Next.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "express": "Express",
    "expressjs": "Express",
    "express.js": "Express",
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "spring": "Spring",
    "spring boot": "Spring Boot",
    "springboot": "Spring Boot",
    "asp.net": "ASP.NET",
    "dotnet": ".NET",
    ".net": ".NET",
    "laravel": "Laravel",
    "rails": "Ruby on Rails",
    "ruby on rails": "Ruby on Rails",
    "graphql": "GraphQL",
    "rest api": "REST APIs",
    "rest apis": "REST APIs",
    "restful api": "REST APIs",
    "restful apis": "REST APIs",
    "restful": "REST APIs",
    "rest": "REST APIs",
    "bootstrap": "Bootstrap",
    "tailwind": "Tailwind CSS",
    "tailwindcss": "Tailwind CSS",
    "jquery": "jQuery",
    "redux": "Redux",

    # Databases & Storage
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mysql": "MySQL",
    "sqlite": "SQLite",
    "sqlite3": "SQLite",
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    "redis": "Redis",
    "cassandra": "Cassandra",
    "dynamodb": "DynamoDB",
    "oracle": "Oracle DB",
    "firebase": "Firebase",
    "firestore": "Firestore",
    "elasticsearch": "Elasticsearch",

    # Cloud & DevOps
    "aws": "AWS",
    "amazon web services": "AWS",
    "azure": "Azure",
    "microsoft azure": "Azure",
    "gcp": "Google Cloud",
    "google cloud": "Google Cloud",
    "google cloud platform": "Google Cloud",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "terraform": "Terraform",
    "ansible": "Ansible",
    "jenkins": "Jenkins",
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "git": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",
    "bitbucket": "Bitbucket",
    "linux": "Linux",
    "unix": "Unix",
    "bash": "Bash",
    "powershell": "PowerShell",
    "nginx": "Nginx",
    "apache": "Apache",

    # Data Science & AI / ML
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "artificial intelligence": "Artificial Intelligence",
    "data science": "Data Science",
    "nlp": "Natural Language Processing",
    "natural language processing": "Natural Language Processing",
    "computer vision": "Computer Vision",
    "cv": "Computer Vision",
    "tensorflow": "TensorFlow",
    "pytorch": "PyTorch",
    "scikit-learn": "Scikit-Learn",
    "sklearn": "Scikit-Learn",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "matplotlib": "Matplotlib",
    "seaborn": "Seaborn",
    "opencv": "OpenCV",
    "keras": "Keras",
    "tableau": "Tableau",
    "power bi": "Power BI",
    "powerbi": "Power BI",
    "statistics": "Statistics",

    # Methodologies & Architecture
    "agile": "Agile",
    "scrum": "Scrum",
    "jira": "Jira",
    "microservices": "Microservices",
    "system design": "System Design",
    "data structures": "Data Structures",
    "algorithms": "Algorithms",
    "unit testing": "Unit Testing",
    "postman": "Postman"
}

# Strong action verbs for ATS impact evaluation
ACTION_VERBS = [
    "developed", "built", "implemented", "designed", "engineered",
    "architected", "created", "led", "managed", "optimized",
    "analyzed", "delivered", "integrated", "spearheaded", "accelerated",
    "automated", "reduced", "increased", "enhanced", "resolved",
    "coordinated", "executed", "formulated", "established", "deployed"
]


def extract_text_from_file(filepath: str, original_filename: str = "") -> Tuple[Optional[str], Optional[str]]:
    """
    Safely extract readable text from PDF or DOCX resume file.
    Returns (extracted_text, error_message).
    If extraction fails or text is unreadable/image-only, returns (None, clean_error_message).
    """
    if not filepath or not os.path.exists(filepath):
        return None, "File not found on server."

    fname = (original_filename or filepath).lower()

    # 1. PDF EXTRACTION
    if fname.endswith(".pdf"):
        if PyPDF2 is None:
            return None, "PDF processing library is currently unavailable on the server."
        try:
            reader = PyPDF2.PdfReader(filepath)
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception:
                    return None, "The uploaded PDF is password-protected. Please upload an unlocked PDF document."

            extracted_pages = []
            for i, page in enumerate(reader.pages):
                try:
                    txt = page.extract_text()
                    if txt and txt.strip():
                        extracted_pages.append(txt.strip())
                except Exception:
                    continue

            full_text = "\n\n".join(extracted_pages).strip()
            if not full_text or len(full_text.split()) < 15:
                return None, (
                    "The uploaded PDF contains no readable text layer (it may be a scanned image or photo). "
                    "OCR (Optical Character Recognition) is not configured in this environment. "
                    "Please upload a PDF generated directly from text (e.g. Word, Google Docs, LaTeX) or a .docx document."
                )
            return full_text, None
        except Exception:
            return None, "Unable to read the uploaded PDF document. The file may be corrupted, truncated, or invalid."

    # 2. DOCX EXTRACTION
    elif fname.endswith(".docx"):
        # Primary: Pure standard-library ZIP + XML extraction (safe on all Python versions)
        try:
            with zipfile.ZipFile(filepath, "r") as z:
                if "word/document.xml" not in z.namelist():
                    return None, "The uploaded DOCX archive does not contain a valid Word document body."
                xml_data = z.read("word/document.xml")
                root = ET.fromstring(xml_data)
                
                paragraphs = []
                w_namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
                for p in root.iter(f"{w_namespace}p"):
                    texts = [node.text for node in p.iter(f"{w_namespace}t") if node.text]
                    if texts:
                        paragraphs.append("".join(texts).strip())
                
                full_text = "\n".join(paragraphs).strip()
                if not full_text or len(full_text.split()) < 15:
                    return None, "The uploaded Word (.docx) document is empty or contains insufficient readable text."
                return full_text, None
        except zipfile.BadZipFile:
            return None, "The uploaded Word file is corrupted or not a valid .docx format."
        except Exception:
            # Fallback to python-docx if available
            if docx is not None:
                try:
                    doc = docx.Document(filepath)
                    paras = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
                    for table in doc.tables:
                        for row in table.rows:
                            for cell in row.cells:
                                if cell.text.strip():
                                    paras.append(cell.text.strip())
                    text = "\n".join(paras).strip()
                    if text and len(text.split()) >= 15:
                        return text, None
                except Exception:
                    pass
            return None, "Unable to read the uploaded Word (.docx) document. Please ensure the file is not corrupted."

    else:
        return None, "Unsupported file format. Please upload a PDF (.pdf) or Word document (.docx)."


def extract_contact_info(raw_text: str) -> Dict[str, Any]:
    """Detect contact info from resume: Name, Email, Phone, Location, LinkedIn, GitHub, Portfolio."""
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    text_lower = raw_text.lower()

    # 1. Email detection
    email_match = re.search(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b", raw_text)
    email = email_match.group(0).lower() if email_match else None

    # 2. Phone detection
    phone_match = re.search(
        r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b\+?\d{10,13}\b",
        raw_text
    )
    phone = phone_match.group(0).strip() if phone_match else None

    # 3. LinkedIn detection
    linkedin_match = re.search(
        r"(?:https?:\/\/)?(?:www\.)?linkedin\.com\/(?:in\/[a-zA-Z0-9_%-]+|[a-zA-Z0-9_%-]+)",
        raw_text,
        re.IGNORECASE
    )
    has_linkedin = bool(linkedin_match or "linkedin.com" in text_lower)
    linkedin_val = linkedin_match.group(0) if linkedin_match else ("linkedin.com profile" if has_linkedin else None)

    # 4. GitHub detection
    github_match = re.search(
        r"(?:https?:\/\/)?(?:www\.)?github\.com\/[a-zA-Z0-9_%-]+",
        raw_text,
        re.IGNORECASE
    )
    has_github = bool(github_match or "github.com" in text_lower or ("github" in text_lower and ("repo" in text_lower or "profile" in text_lower or "code" in text_lower)))
    github_val = github_match.group(0) if github_match else ("github.com profile" if has_github else None)

    # 5. Portfolio detection
    portfolio_match = re.search(
        r"(?:https?:\/\/)?(?:www\.)?(?:[a-zA-Z0-9-]+\.(?:vercel\.app|netlify\.app|github\.io|me|dev|io|tech))|(?:portfolio|personal website)[:\s]+(https?:\/\/[^\s]+)",
        raw_text,
        re.IGNORECASE
    )
    has_portfolio = bool(portfolio_match or "portfolio" in text_lower and ("website" in text_lower or "link" in text_lower or "http" in text_lower))
    portfolio_val = portfolio_match.group(0) if portfolio_match else ("Portfolio Link" if has_portfolio else None)

    # 6. Name detection (heuristic: top 1-4 lines, 2-4 words, no digits, no email symbols)
    name = None
    for line in lines[:5]:
        cleaned = re.sub(r"[^a-zA-Z\s]", "", line).strip()
        words = cleaned.split()
        if 2 <= len(words) <= 4 and "@" not in line and "resume" not in cleaned.lower() and "curriculum" not in cleaned.lower():
            if not any(header in cleaned.lower() for header in ["education", "experience", "skills", "projects", "summary", "contact", "address", "phone"]):
                name = cleaned.title()
                break

    # 7. Location detection
    location = None
    location_keywords = [
        "bangalore", "bengaluru", "mumbai", "delhi", "hyderabad", "pune", "chennai", "kolkata",
        "bhubaneswar", "noida", "gurgaon", "remote", "new york", "san francisco", "london", "india", "usa", "california"
    ]
    for loc in location_keywords:
        if re.search(rf"\b{re.escape(loc)}\b", text_lower):
            location = loc.title()
            break

    return {
        "name": {
            "present": bool(name),
            "status": "Present" if name else "Needs manual review",
            "value": name or "Not Detected"
        },
        "email": {
            "present": bool(email),
            "status": "Present" if email else "Missing",
            "value": email or "Not Detected"
        },
        "phone": {
            "present": bool(phone),
            "status": "Present" if phone else "Missing",
            "value": phone or "Not Detected"
        },
        "location": {
            "present": bool(location),
            "status": "Present" if location else "Not Specified",
            "value": location or "Not Specified"
        },
        "linkedin": {
            "present": has_linkedin,
            "status": "Present" if has_linkedin else "Missing",
            "value": linkedin_val or "Not Detected"
        },
        "github": {
            "present": has_github,
            "status": "Present" if has_github else "Missing",
            "value": github_val or "Not Detected"
        },
        "portfolio": {
            "present": has_portfolio,
            "status": "Present" if has_portfolio else "Missing",
            "value": portfolio_val or "Not Detected"
        }
    }


def detect_sections(raw_text: str) -> List[Dict[str, Any]]:
    """
    Detect whether standard resume sections are present based on realistic heading variations.
    Uses line-level heading inspection to avoid false positives inside regular sentence text.
    """
    lines = [line.strip().lower() for line in raw_text.splitlines() if line.strip()]
    text_lower = raw_text.lower()

    # Helper: checks if any line starts with or exactly contains the section heading
    def heading_exists(patterns: List[str]) -> bool:
        for line in lines:
            # Strip numbering, bullet points, colons
            cleaned_line = re.sub(r"^[\d\.\-\*\•\>\:\s]+", "", line).strip()
            cleaned_line = re.sub(r"[\:\-\|]+$", "", cleaned_line).strip()
            for pat in patterns:
                if cleaned_line == pat or cleaned_line.startswith(pat + " ") or cleaned_line.endswith(" " + pat):
                    return True
        # Secondary fallback: isolated regex check with boundaries
        for pat in patterns:
            if re.search(rf"(?:^|\n)\s*{re.escape(pat)}\s*(?:\:|\n|$)", text_lower):
                return True
        return False

    section_defs = [
        {
            "name": "Education",
            "patterns": ["education", "academic background", "academics", "educational qualifications", "qualifications", "academic credentials"],
            "fallback_keywords": ["b.tech", "btech", "m.tech", "b.e", "bca", "mca", "b.sc", "bachelor", "master", "degree", "university", "cgpa"],
            "required_for_students": True
        },
        {
            "name": "Technical Skills",
            "patterns": ["skills", "technical skills", "core competencies", "technologies", "tools & technologies", "tech stack", "skills & abilities", "key skills", "proficiencies"],
            "fallback_keywords": ["programming languages", "technical proficiencies", "developer tools"],
            "required_for_students": True
        },
        {
            "name": "Projects",
            "patterns": ["projects", "academic projects", "personal projects", "key projects", "project experience", "capstone projects", "major projects"],
            "fallback_keywords": ["project 1", "project 2", "github.com/"],
            "required_for_students": True
        },
        {
            "name": "Experience / Work History",
            "patterns": ["experience", "work experience", "professional experience", "employment history", "work history", "employment"],
            "fallback_keywords": [],
            "required_for_students": False
        },
        {
            "name": "Internship Experience",
            "patterns": ["internship", "internships", "internship experience", "summer internship", "industrial training"],
            "fallback_keywords": ["software engineering intern", "intern at", "internship trainee"],
            "required_for_students": False
        },
        {
            "name": "Summary / Objective",
            "patterns": ["summary", "professional summary", "career objective", "objective", "profile", "about me", "executive summary"],
            "fallback_keywords": ["motivated software", "seeking an entry-level", "aspiring software"],
            "required_for_students": False
        },
        {
            "name": "Certifications",
            "patterns": ["certifications", "certificates", "certified", "licenses & certifications", "professional certifications"],
            "fallback_keywords": ["aws certified", "coursera", "udemy certified"],
            "required_for_students": False
        },
        {
            "name": "Achievements / Extracurricular",
            "patterns": ["achievements", "honors & awards", "accomplishments", "extracurricular", "extracurricular activities", "publications", "leadership"],
            "fallback_keywords": ["hackathon", "first place", "runner up", "dean's list"],
            "required_for_students": False
        }
    ]

    detected_sections = []
    for sdef in section_defs:
        is_detected = heading_exists(sdef["patterns"])
        if not is_detected and sdef["fallback_keywords"]:
            # Fallback if prominent keywords occur
            is_detected = any(re.search(rf"\b{re.escape(k)}\b", text_lower) for k in sdef["fallback_keywords"])

        status = "Present" if is_detected else "Missing"
        detected_sections.append({
            "name": sdef["name"],
            "present": is_detected,
            "status": status,
            "required_for_students": sdef["required_for_students"]
        })

    return detected_sections


def extract_skills_from_text(text: str) -> List[str]:
    """Extract recognized technical and professional skills from text with alias normalization."""
    found_skills = set()
    text_lower = text.lower()

    # Search each alias in text with strict boundary checking
    for alias, canonical in TECH_SKILLS_MAP.items():
        # Handle special symbols like c++, c#, .net, ci/cd
        if alias in ["c++", "c#", ".net", "ci/cd"]:
            pattern = rf"(?:^|[\s,;/()\[\]]){re.escape(alias)}(?:$|[\s,;/()\[\]])"
        elif alias in ["r", "c", "go"]:
            # Avoid single letters matching common words; match only in skill listings or specific context
            pattern = rf"(?:^|[\s,;/()\[\]]){re.escape(alias)}(?:$|[\s,;/()\[\]])"
        else:
            pattern = rf"\b{re.escape(alias)}\b"

        if re.search(pattern, text_lower):
            found_skills.add(canonical)

    return sorted(list(found_skills))


def compare_job_description(resume_text: str, resume_skills: List[str], jd_text: str) -> Dict[str, Any]:
    """Compare resume content against a target Job Description."""
    if not jd_text or not jd_text.strip():
        return {
            "has_jd": False,
            "keywords_found": False,
            "matched_keywords": [],
            "missing_keywords": [],
            "match_rate": 0,
            "total_jd_keywords": 0,
            "note": "No Job Description provided: A reliable job-specific ATS match score cannot be calculated without target role requirements. General resume quality audit performed instead."
        }

    # Extract skills mentioned in the Job Description
    jd_skills = extract_skills_from_text(jd_text)

    if not jd_skills:
        return {
            "has_jd": True,
            "keywords_found": False,
            "matched_keywords": [],
            "missing_keywords": [],
            "match_rate": 0,
            "total_jd_keywords": 0,
            "note": "No recognizable technical keywords could be identified in the supplied Job Description text."
        }

    resume_lower = resume_text.lower()
    matched = []
    missing = []

    for skill in jd_skills:
        # Check canonical match first
        if skill in resume_skills:
            matched.append(skill)
            continue
        # Check aliases
        aliases = [k for k, v in TECH_SKILLS_MAP.items() if v == skill]
        is_matched = False
        for a in aliases:
            if a in ["c++", "c#", ".net", "ci/cd", "r", "c", "go"]:
                p = rf"(?:^|[\s,;/()\[\]]){re.escape(a)}(?:$|[\s,;/()\[\]])"
            else:
                p = rf"\b{re.escape(a)}\b"
            if re.search(p, resume_lower):
                is_matched = True
                break
        if is_matched:
            matched.append(skill)
        else:
            missing.append(skill)

    total_jd = len(jd_skills)
    match_rate = round((len(matched) / max(total_jd, 1)) * 100) if total_jd > 0 else 0

    return {
        "has_jd": True,
        "keywords_found": True,
        "matched_keywords": sorted(matched),
        "missing_keywords": sorted(missing),
        "match_rate": match_rate,
        "total_jd_keywords": total_jd,
        "note": (
            f"Matched {len(matched)} of {total_jd} identified keywords ({match_rate}%). "
            "Note: Missing keywords mean not detected in the submitted resume; it does not prove the applicant lacks the skill."
        )
    }


def generate_job_match_suggestions(
    matched_skills: List[str],
    missing_skills: List[str],
    match_rate: int,
    total_jd_keywords: int
) -> List[str]:
    """
    Generate evidence-based recommendations tailored directly to detected gaps
    between the resume and the target job description.
    """
    suggestions = []

    if total_jd_keywords == 0:
        return [
            "The supplied Job Description did not contain recognized technical skill keywords.",
            "Paste a more detailed Job Description listing required programming languages, frameworks, databases, or tools."
        ]

    if missing_skills:
        top_missing = missing_skills[:4]
        suggestions.append(
            f"Prioritize incorporating evidence or projects demonstrating high-value missing requirements: {', '.join(top_missing)}."
        )
        if len(missing_skills) > 4:
            suggestions.append(
                f"Consider bridging other undetected job requirements: {', '.join(missing_skills[4:8])}."
            )
        suggestions.append(
            f"If you already possess experience with {missing_skills[0]}, ensure it is explicitly listed using industry-standard terminology in your Technical Skills or Experience bullet points."
        )

    if match_rate == 100:
        suggestions.append(
            f"Exceptional alignment! Your resume covers all {total_jd_keywords} technical requirements identified in the target Job Description."
        )
        suggestions.append(
            "Reinforce these matched competencies with quantifiable outcomes (e.g. latency reduction, cost savings, user scale) to maximize interview conversion."
        )
    elif match_rate >= 75:
        suggestions.append(
            f"Strong match ({match_rate}%). You cover {len(matched_skills)} of {total_jd_keywords} target requirements. Minor keyword alignment will place your profile in the top tier."
        )
    elif match_rate >= 40:
        suggestions.append(
            f"Moderate match ({match_rate}%). Highlighting transferable skills and adding a targeted project showcasing {missing_skills[0] if missing_skills else 'core stack'} will bridge the gap."
        )
    else:
        suggestions.append(
            f"Low match ({match_rate}%). Significant gaps detected against this role's requirements. Consider tailoring your resume or acquiring experience in {', '.join(missing_skills[:3]) if missing_skills else 'the core requirements'} before applying."
        )

    return suggestions


def analyze_job_match(resume_text: str, jd_text: str) -> Dict[str, Any]:
    """
    Unified Job Match Analysis combining canonical skill extraction, alias resolution,
    deterministic keyword overlap calculation, and actionable suggestions.
    """
    resume_skills = extract_skills_from_text(resume_text)
    comp = compare_job_description(resume_text, resume_skills, jd_text)

    matched = comp.get("matched_keywords", [])
    missing = comp.get("missing_keywords", [])
    match_rate = comp.get("match_rate", 0)
    total_jd = comp.get("total_jd_keywords", 0)

    suggestions = generate_job_match_suggestions(matched, missing, match_rate, total_jd)

    return {
        "score": match_rate,
        "matching_skills": matched,
        "missing_keywords": missing,
        "total_jd_keywords": total_jd,
        "resume_skills_count": len(resume_skills),
        "suggestions": suggestions,
        "note": comp.get("note", ""),
        "keywords_found": comp.get("keywords_found", False),
        "has_jd": comp.get("has_jd", False)
    }



def analyze_formatting_and_readability(raw_text: str) -> Dict[str, Any]:
    """Audit document length, action verbs, quantitative impact, and text cleanliness."""
    words = raw_text.split()
    word_count = len(words)
    text_lower = raw_text.lower()

    # 1. Action verbs count
    detected_verbs = sorted(list(set(verb for verb in ACTION_VERBS if re.search(rf"\b{verb}\b", text_lower))))

    # 2. Measurable metrics (e.g. percentages, numbers, quantitative values)
    metrics_matches = re.findall(
        r"\b(?:\d+%\b|\d+\+\b|\$\d+|\d+\s*(?:ms|k|m|users|clients|projects|percent|seconds|hours|queries|qps))",
        raw_text,
        re.IGNORECASE
    )

    # 3. Special character noise check (excessive unreadable symbols)
    non_ascii = [c for c in raw_text if ord(c) > 127]
    noise_ratio = len(non_ascii) / max(1, len(raw_text))

    findings = []

    # Document length
    if word_count < 100:
        findings.append({
            "label": "Document Length",
            "status": "fail",
            "text": f"Resume is critically brief ({word_count} words). ATS parsers may mark this as incomplete."
        })
    elif word_count < 220:
        findings.append({
            "label": "Document Length",
            "status": "warning",
            "text": f"Resume is relatively brief ({word_count} words). Recommended length is 350–800 words."
        })
    elif word_count <= 900:
        findings.append({
            "label": "Document Length",
            "status": "pass",
            "text": f"Optimal resume length detected ({word_count} words)."
        })
    else:
        findings.append({
            "label": "Document Length",
            "status": "warning",
            "text": f"Resume is lengthy ({word_count} words). Aim for a concise 1–2 page format."
        })

    # Action Verbs
    if len(detected_verbs) >= 5:
        findings.append({
            "label": "Action Verbs",
            "status": "pass",
            "text": f"Strong action verbs detected ({len(detected_verbs)} verbs, e.g. {', '.join(detected_verbs[:3])})."
        })
    elif len(detected_verbs) >= 2:
        findings.append({
            "label": "Action Verbs",
            "status": "warning",
            "text": f"Few action verbs detected ({len(detected_verbs)}). Use dynamic verbs like 'engineered', 'built', 'optimized'."
        })
    else:
        findings.append({
            "label": "Action Verbs",
            "status": "fail",
            "text": "No strong action verbs identified in project or experience descriptions."
        })

    # Quantifiable Metrics
    if len(metrics_matches) >= 3:
        findings.append({
            "label": "Quantifiable Metrics",
            "status": "pass",
            "text": f"Good quantitative metrics identified ({len(metrics_matches)} instances)."
        })
    elif len(metrics_matches) >= 1:
        findings.append({
            "label": "Quantifiable Metrics",
            "status": "warning",
            "text": "Limited quantitative data found. Quantify impact with numbers (e.g. 'reduced latency by 25%')."
        })
    else:
        findings.append({
            "label": "Quantifiable Metrics",
            "status": "fail",
            "text": "No quantifiable metrics found. Recruiter ATS algorithms favor quantified achievements."
        })

    # Text cleanliness
    if noise_ratio > 0.15:
        findings.append({
            "label": "Text Cleanliness",
            "status": "warning",
            "text": "High ratio of non-standard characters detected. May indicate complex encoding or symbols."
        })
    else:
        findings.append({
            "label": "Text Cleanliness",
            "status": "pass",
            "text": "Clean plain-text extraction with standard character encoding."
        })

    return {
        "word_count": word_count,
        "action_verb_count": len(detected_verbs),
        "detected_verbs": detected_verbs,
        "metrics_count": len(metrics_matches),
        "noise_ratio": round(noise_ratio, 3),
        "findings": findings
    }


def compute_ats_score(
    contact_info: Dict[str, Any],
    sections: List[Dict[str, Any]],
    skills: List[str],
    formatting: Dict[str, Any],
    jd_analysis: Dict[str, Any]
) -> Tuple[int, Dict[str, Any]]:
    """
    Computes a transparent, deterministic ATS score out of 100 based strictly on extracted evidence.
    Two deterministic models:
    - Mode A (With Job Description, 100 pts): Contact (10) + Sections (20) + Skills (20) + Impact (15) + Readability (15) + JD Match (20)
    - Mode B (Without Job Description, 100 pts): Contact (15) + Sections (25) + Skills (25) + Impact (20) + Readability (15)
    """
    has_jd = jd_analysis.get("has_jd", False) and jd_analysis.get("keywords_found", False)
    categories = {}

    sec_map = {s["name"]: s["present"] for s in sections}
    skill_cnt = len(skills)
    v_cnt = formatting["action_verb_count"]
    m_cnt = formatting["metrics_count"]
    w_cnt = formatting["word_count"]

    if has_jd:
        # ---------------- MODE A: WITH JOB DESCRIPTION (100 PTS) ----------------
        # 1. Contact Info (Max 10)
        c_score = 0
        if contact_info["name"]["present"]: c_score += 2
        if contact_info["email"]["present"]: c_score += 3
        if contact_info["phone"]["present"]: c_score += 3
        if contact_info["linkedin"]["present"] or contact_info["github"]["present"]: c_score += 2
        categories["contact_info"] = {
            "name": "Contact Information",
            "score": c_score,
            "max": 10,
            "status": "Good" if c_score >= 8 else ("Fair" if c_score >= 5 else "Needs Improvement")
        }

        # 2. Section Completeness (Max 20)
        # Entry-level friendly: strong projects + education + internship/experience
        s_score = 0
        if sec_map.get("Education"): s_score += 5
        if sec_map.get("Technical Skills"): s_score += 5
        if sec_map.get("Projects"): s_score += 5
        if sec_map.get("Experience / Work History") or sec_map.get("Internship Experience"):
            s_score += 3
        elif sec_map.get("Projects"): # Student bonus if projects exist
            s_score += 2
        if sec_map.get("Summary / Objective") or sec_map.get("Certifications") or sec_map.get("Achievements / Extracurricular"):
            s_score += 2
        categories["section_completeness"] = {
            "name": "Section Completeness",
            "score": min(20, s_score),
            "max": 20,
            "status": "Good" if s_score >= 15 else ("Fair" if s_score >= 10 else "Needs Improvement")
        }

        # 3. Technical Skills Coverage (Max 20)
        if skill_cnt == 0: sk_score = 0
        elif skill_cnt <= 2: sk_score = 5
        elif skill_cnt <= 5: sk_score = 10
        elif skill_cnt <= 8: sk_score = 15
        elif skill_cnt <= 12: sk_score = 18
        else: sk_score = 20
        categories["skills"] = {
            "name": "Technical Skills Breadth",
            "score": sk_score,
            "max": 20,
            "status": "Good" if sk_score >= 15 else ("Fair" if sk_score >= 10 else "Needs Improvement")
        }

        # 4. Experience & Impact Quality (Max 15)
        v_pts = 8 if v_cnt >= 5 else (6 if v_cnt >= 3 else (3 if v_cnt >= 1 else 0))
        m_pts = 7 if m_cnt >= 3 else (4 if m_cnt >= 1 else 0)
        exp_score = v_pts + m_pts
        categories["experience_projects"] = {
            "name": "Action Verbs & Impact",
            "score": exp_score,
            "max": 15,
            "status": "Good" if exp_score >= 11 else ("Fair" if exp_score >= 7 else "Needs Improvement")
        }

        # 5. Formatting & Readability (Max 15)
        if 250 <= w_cnt <= 850: len_pts = 10
        elif 150 <= w_cnt < 250 or 850 < w_cnt <= 1100: len_pts = 6
        elif w_cnt < 150: len_pts = 2
        else: len_pts = 4
        clean_pts = 5 if s_score >= 10 else 3
        read_score = len_pts + clean_pts
        categories["readability_formatting"] = {
            "name": "Formatting & Readability",
            "score": read_score,
            "max": 15,
            "status": "Good" if read_score >= 12 else ("Fair" if read_score >= 8 else "Needs Improvement")
        }

        # 6. Job Description Keyword Match (Max 20)
        match_rate = jd_analysis["match_rate"]
        jd_score = round((match_rate / 100.0) * 20)
        categories["job_match"] = {
            "name": "Target Job Match",
            "score": jd_score,
            "max": 20,
            "status": "Good" if jd_score >= 14 else ("Fair" if jd_score >= 8 else "Needs Improvement")
        }

    else:
        # ---------------- MODE B: GENERAL RESUME QUALITY (100 PTS) ----------------
        # 1. Contact Info (Max 15)
        c_score = 0
        if contact_info["name"]["present"]: c_score += 3
        if contact_info["email"]["present"]: c_score += 4
        if contact_info["phone"]["present"]: c_score += 4
        if contact_info["location"]["present"]: c_score += 2
        if contact_info["linkedin"]["present"] or contact_info["github"]["present"] or contact_info["portfolio"]["present"]:
            c_score += 2
        categories["contact_info"] = {
            "name": "Contact Information",
            "score": c_score,
            "max": 15,
            "status": "Good" if c_score >= 12 else ("Fair" if c_score >= 8 else "Needs Improvement")
        }

        # 2. Section Completeness (Max 25)
        s_score = 0
        if sec_map.get("Education"): s_score += 6
        if sec_map.get("Technical Skills"): s_score += 6
        if sec_map.get("Projects"): s_score += 6
        if sec_map.get("Experience / Work History") or sec_map.get("Internship Experience"):
            s_score += 4
        elif sec_map.get("Projects"): # Fair student allowance
            s_score += 3
        if sec_map.get("Summary / Objective") or sec_map.get("Certifications") or sec_map.get("Achievements / Extracurricular"):
            s_score += 3
        categories["section_completeness"] = {
            "name": "Section Completeness",
            "score": min(25, s_score),
            "max": 25,
            "status": "Good" if s_score >= 19 else ("Fair" if s_score >= 12 else "Needs Improvement")
        }

        # 3. Technical Skills Coverage (Max 25)
        if skill_cnt == 0: sk_score = 0
        elif skill_cnt <= 2: sk_score = 6
        elif skill_cnt <= 5: sk_score = 12
        elif skill_cnt <= 8: sk_score = 18
        elif skill_cnt <= 12: sk_score = 22
        else: sk_score = 25
        categories["skills"] = {
            "name": "Technical Skills Breadth",
            "score": sk_score,
            "max": 25,
            "status": "Good" if sk_score >= 18 else ("Fair" if sk_score >= 12 else "Needs Improvement")
        }

        # 4. Experience & Impact Quality (Max 20)
        v_pts = 10 if v_cnt >= 5 else (7 if v_cnt >= 3 else (4 if v_cnt >= 1 else 0))
        m_pts = 10 if m_cnt >= 3 else (6 if m_cnt >= 1 else 0)
        exp_score = v_pts + m_pts
        categories["experience_projects"] = {
            "name": "Action Verbs & Impact",
            "score": exp_score,
            "max": 20,
            "status": "Good" if exp_score >= 15 else ("Fair" if exp_score >= 10 else "Needs Improvement")
        }

        # 5. Formatting & Readability (Max 15)
        if 250 <= w_cnt <= 850: len_pts = 10
        elif 150 <= w_cnt < 250 or 850 < w_cnt <= 1100: len_pts = 6
        elif w_cnt < 150: len_pts = 2
        else: len_pts = 4
        clean_pts = 5 if s_score >= 12 else 3
        read_score = len_pts + clean_pts
        categories["readability_formatting"] = {
            "name": "Formatting & Readability",
            "score": read_score,
            "max": 15,
            "status": "Good" if read_score >= 12 else ("Fair" if read_score >= 8 else "Needs Improvement")
        }

    total_score = max(0, min(100, sum(c["score"] for c in categories.values())))
    return total_score, categories


def generate_problems_and_recommendations(
    contact_info: Dict[str, Any],
    sections: List[Dict[str, Any]],
    skills: List[str],
    formatting: Dict[str, Any],
    jd_analysis: Dict[str, Any],
    score: int
) -> Tuple[List[str], List[str]]:
    """Generate dynamic, genuine problems found and actionable recommendations."""
    problems = []
    recommendations = []

    # 1. Contact checks
    if not contact_info["email"]["present"]:
        problems.append("Direct email address was not detected.")
        recommendations.append("Ensure your primary professional email is prominently placed in the contact header.")

    if not contact_info["phone"]["present"]:
        problems.append("Direct phone number was not detected.")
        recommendations.append("Add a valid phone number with area/country code to the top of your resume.")

    if not contact_info["linkedin"]["present"]:
        problems.append("LinkedIn profile link was not detected.")
        recommendations.append("Include your customized LinkedIn URL to provide recruiters quick access to your professional network.")

    if not contact_info["github"]["present"] and not contact_info["portfolio"]["present"]:
        problems.append("Neither GitHub nor technical portfolio URL was detected.")
        recommendations.append("Add a link to your GitHub profile or live project portfolio to demonstrate practical coding ability.")

    # 2. Section checks
    sec_map = {s["name"]: s["present"] for s in sections}
    if not sec_map.get("Education"):
        problems.append("Education section was not detected.")
        recommendations.append("Add an Education section specifying your degree, university, branch, and graduation year.")

    if not sec_map.get("Technical Skills"):
        problems.append("Technical Skills section was not detected.")
        recommendations.append("Create a dedicated Technical Skills section organized by Languages, Frameworks, and Tools.")

    if not sec_map.get("Projects"):
        problems.append("Projects section was not detected.")
        recommendations.append("Include at least 2 substantial technical projects detailing your role, tech stack, and impact.")

    if not sec_map.get("Experience / Work History") and not sec_map.get("Internship Experience"):
        problems.append("No Work Experience or Internship section was identified.")
        recommendations.append("Include technical internships, freelance projects, or open-source contributions to demonstrate applied experience.")

    if not sec_map.get("Summary / Objective"):
        problems.append("Professional Summary or Career Objective is absent.")
        recommendations.append("Add a 2–3 line summary highlighting your core tech competencies and career focus.")

    # 3. Skills checks
    if len(skills) < 4:
        problems.append(f"Only {len(skills)} technical skills were detected. ATS systems score higher on robust skill coverage.")
        recommendations.append("Expand your skills list with relevant programming languages, databases, libraries, and tools you have used.")

    # 4. Job Description checks
    if jd_analysis.get("has_jd") and jd_analysis.get("keywords_found"):
        missing = jd_analysis["missing_keywords"]
        if missing:
            top_missing = missing[:5]
            problems.append(f"{len(missing)} target skills from Job Description were not detected in your resume (e.g. {', '.join(top_missing)}).")
            recommendations.append(f"Incorporate missing keywords ({', '.join(top_missing)}) if you possess those skills truthfully.")

    # 5. Formatting & metrics checks
    if formatting["word_count"] < 150:
        problems.append(f"Resume text is very short ({formatting['word_count']} words), which ATS parsers often flag as incomplete.")
        recommendations.append("Expand your project and role descriptions with context, technical challenges, and achievements.")

    if formatting["metrics_count"] == 0:
        problems.append("No quantifiable metrics (e.g. %, numbers, scale) were detected in your bullet points.")
        recommendations.append("Quantify your achievements (e.g. 'improved performance by 25%', 'handled 500+ daily requests').")

    if formatting["action_verb_count"] < 2:
        problems.append("Few action verbs detected. Descriptions should begin with active past-tense verbs.")
        recommendations.append("Start your bullet points with dynamic verbs such as 'Engineered', 'Built', 'Optimized', 'Architected'.")

    # Fallbacks if resume is already very strong
    if not problems:
        problems.append("No critical ATS disqualifiers found. Continue tailoring keywords for each job application.")
    if not recommendations:
        recommendations.append("Maintain clean, single-column formatting and ensure all contact links remain active.")

    return problems, recommendations


def analyze_resume(text: str, job_description: str = "") -> Dict[str, Any]:
    """
    Main entry point for ATS resume analysis.
    Takes extracted text and optional job description, executes comprehensive audit,
    and returns a fully dynamic, realistic ATS report.
    """
    if not text or not text.strip() or len(text.strip().split()) < 15:
        return {
            "error": "The uploaded document contains insufficient readable text. Please upload a valid PDF or DOCX file with readable text content.",
            "success": False
        }

    raw_text = text.strip()

    # 1. Contact Information
    contact_info = extract_contact_info(raw_text)

    # 2. Section Detection
    sections = detect_sections(raw_text)

    # 3. Skills Extraction
    skills = extract_skills_from_text(raw_text)

    # 4. Job Description Matching
    jd_analysis = compare_job_description(raw_text, skills, job_description)

    # 5. Formatting & Readability Audit
    formatting = analyze_formatting_and_readability(raw_text)

    # 6. ATS Scoring Calculation
    score, category_scores = compute_ats_score(contact_info, sections, skills, formatting, jd_analysis)

    # 7. Problems & Recommendations
    problems, recommendations = generate_problems_and_recommendations(
        contact_info, sections, skills, formatting, jd_analysis, score
    )

    # Score rating label
    if score >= 80:
        score_rating = "Excellent / Highly Competitive"
        score_badge = "pill-good"
    elif score >= 60:
        score_rating = "Moderate / Competitive with Improvements"
        score_badge = "pill-warn"
    else:
        score_rating = "Needs Significant Improvement"
        score_badge = "pill-bad"

    # Project count heuristic from projects section
    projects_detected = next((s["present"] for s in sections if s["name"] == "Projects"), False)
    project_mentions = max(1 if projects_detected else 0, raw_text.lower().count("project"))

    return {
        "success": True,
        "score": score,
        "score_rating": score_rating,
        "score_badge": score_badge,
        "category_scores": category_scores,
        "contact_info": contact_info,
        "sections": sections,
        "missing_sections": [s["name"] for s in sections if not s["present"]],
        "skills_analysis": {
            "detected_skills": skills,
            "skill_count": len(skills)
        },
        "job_match": jd_analysis,
        "formatting_audit": formatting,
        "problems": problems,
        "suggestions": recommendations,
        "recommendations": recommendations,
        "project_count": min(10, project_mentions),
        "limitations": (
            "This ATS analysis is based on text parsing, section heuristics, and keyword taxonomy. "
            "It does not visually evaluate complex multi-column graphic layouts, tables, or non-text image elements. "
            "Scores reflect compliance with standard applicant tracking heuristics and should be used as guidance."
        ),
        "summary": f"ATS Analysis complete: Overall score is {score}/100 with {len(skills)} skills detected."
    }
