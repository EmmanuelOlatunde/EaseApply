

# **EaseApply: AI Resume & Job Match API**

🚀 **AI-powered backend that analyzes resumes against job descriptions and generates tailored cover letters.**

This Django REST Framework project helps job seekers **optimize their resumes** and **instantly generate professional cover letters** for specific roles. It uses **OpenAI GPT-4o-mini** for smart text analysis and ATS-style scoring.

---

## ✨ **Features**

✅ **Resume Upload & Parsing** – Upload PDF/DOCX, extract clean text
✅ **Job Description Management** – Store and manage job postings
✅ **AI Resume Analysis** – Get a **match score**, **missing keywords**, and **improvement suggestions**
✅ **AI Cover Letter Generation** – Instantly generate a **tailored, ATS-friendly cover letter**
✅ **JWT Authentication** – Secure API access
✅ **Swagger API Docs** – Auto-generated API documentation
✅ **Scalable Modular Architecture** – Separate apps for `users`, `resumes`, `jobs`, `analysis`

---

## 🏗️ **Tech Stack**

* **Backend:** Django + Django REST Framework
* **AI Integration:** OpenAI GPT-4o-mini
* **Database:** PostgreSQL (or SQLite for development)
* **Auth:** JWT via `djangorestframework-simplejwt`
* **File Parsing:** PyPDF2, python-docx
* **Docs:** drf-yasg (Swagger/OpenAPI)

---

## 📂 **Project Structure**

```
resume_match_api/
├── config/            # Django project settings
├── users/             # Authentication & JWT
├── resumes/           # Resume upload & parsing
├── jobs/              # Job description management
├── analysis/          # AI resume-job analysis & cover letters
├── common/            # Shared utils, permissions
└── media/             # Uploaded files
```

---

## 🔑 **Key Models**

* **Resume** → Stores uploaded resume + extracted text
* **JobDescription** → Stores job title + description
* **AnalysisResult** → Stores AI match score, missing keywords, suggestions, cover letter

---

## 🚀 **Getting Started**

### 1️⃣ **Clone & Install**

```bash
git clone https://github.com/yourusername/ai-resume-match-api.git
cd ai-resume-match-api

python -m venv venv
source venv/bin/activate  # (Windows: venv\Scripts\activate)

pip install -r requirements.txt
```

---

### 2️⃣ **Environment Variables**

Create a `.env` file:

```
SECRET_KEY=your-django-secret
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3

OPENAI_API_KEY=sk-your-openai-key
```

---

### 3️⃣ **Run Migrations**

```bash
python manage.py migrate
```

---

### 4️⃣ **Start the Server**

```bash
python manage.py runserver
```

✅ API will run at `http://127.0.0.1:8000/`

✅ Swagger docs at `http://127.0.0.1:8000/swagger/`

---

## 🧠 **AI Features**

### **1. Resume-Job Analysis**

POST `/api/analyze/`

```json
{
  "resume_id": "uuid-of-resume",
  "job_id": "uuid-of-job"
}
```

✅ Returns:

```json
{
  "match_score": 82,
  "missing_keywords": ["GraphQL", "Docker", "CI/CD"],
  "suggestions": "Highlight cloud deployment experience and add Docker knowledge."
}
```

---

### **2. Cover Letter Generation**

POST `/api/cover-letter/`

```json
{
  "resume_id": "uuid-of-resume",
  "job_id": "uuid-of-job"
}
```

✅ Returns a tailored **cover letter**:

```
Dear Hiring Manager,  
I’m excited to apply for the Backend Engineer role at XYZ Company...
```

---

## 📌 **Future Enhancements**

* ✅ **Async AI requests** with Celery + Redis
* ✅ **LinkedIn job scraping** integration
* ✅ **Multi-language resume support**
* ✅ **Local AI models (HuggingFace) for cheaper inference**

---

## 🏆 **Why This Project is Awesome**

* Shows **real AI integration** with Django REST Framework
* Demonstrates **prompt engineering & JSON parsing**
* Solves a **real-world HR tech problem**
* Perfect for **portfolio, SaaS MVP, or freelance gigs**

---

## 📜 **License**

MIT License – feel free to use & modify.

---

## 💡 **Want to Try It?**

1. **Fork & clone this repo**
2. Get a **free OpenAI API key**
3. Run it locally & analyze your own resume!

---

Would you like me to:

✅ **Add a sample screenshot of API Swagger docs** in the README?
✅ Or **include an example Trello/Notion link for project planning?**

Also, should I **write a one-paragraph “Portfolio Summary”** you can use on LinkedIn/GitHub?
