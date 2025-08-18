---

# **EaseApply Backend: AI Resume & Job Match API**

🚀 **AI-powered Django REST Framework backend** that analyzes resumes, and generates **tailored ATS-friendly cover letters**.

Frontend (Vue.js) → [EaseApply Frontend](https://easeapply-hazel.vercel.app)
Backend (Django + DRF) → [EaseApply Backend](https://easeapply.onrender.com)
Swagger Docs → [API Documentation](https://easeapply.onrender.com/swagger/?format=openapi)

---

## ✨ Features

* **Authentication & User Management**

  * JWT-based login and registration (access + refresh tokens)
  * Email verification with tokenized links
  * Password reset, change password, and logout (refresh blacklist)
  * Resend verification endpoint

* **Resume Management**

  * Upload PDF/DOCX resumes
  * Parse resumes into structured JSON (skills, education, work experience)
  * Reparse resumes on demand
  * Analytics on extracted resume data

* **Job Description Management**

  * Upload or paste job descriptions
  * Store, edit, and delete postings
  * Reprocess jobs to improve parsing quality

* **AI-Powered Resume & Job Matching**

  * Analyze resume and job description
  * Create tailored ATS-optimized cover letters via OpenAI GPT-4o-mini (through OpenRouter/DeepSeek)

* **Developer-Friendly**

  * Swagger / ReDoc auto-generated API docs
  * Modular Django app structure
  * Scalable with PostgreSQL (Neon DB) and Render deployment

---

## 🏗️ Tech Stack

* **Backend:** Django REST Framework
* **Database:** PostgreSQL (Neon)
* **AI Layer:** OpenAI GPT-4o-mini via OpenRouter / DeepSeek GPT API
* **File Parsing:** PyPDF2, python-docx
* **Auth & Security:** JWT (djangorestframework-simplejwt), DRF throttling
* **Docs:** drf-yasg (Swagger / OpenAPI)
* **Deployment:** Backend on Render, Frontend on Vercel

---

## 📂 Project Structure

```
easeapply-backend/
├── config/          # Django project settings
├── users/           # Authentication & JWT
├── resumes/         # Resume upload & parsing
├── jobs/            # Job description management
├── analysis/        # AI-based analysis & cover letter generation
├── common/          # Shared utils, permissions
└── media/           # Uploaded files
```

---

## 🔑 Key Models

* **User** → Authentication & profile management
* **Resume** → Stores uploaded resume and extracted text
* **JobDescription** → Stores job postings and metadata
* **AnalysisResult** → Generated cover letter

---

## 🚀 Getting Started

### 1️⃣ Clone & Install

```bash
git clone https://github.com/yourusername/easeapply-backend.git
cd easeapply-backend

python -m venv venv
source venv/bin/activate  # (Windows: venv\Scripts\activate)

pip install -r requirements.txt
```

### 2️⃣ Environment Variables

Create a `.env` file:

```
SECRET_KEY=your-django-secret
DEBUG=True
DATABASE_URL=postgres://user:password@host:5432/easeapply

EMAIL_HOST=smtp.yourprovider.com
EMAIL_HOST_USER=your-email
EMAIL_HOST_PASSWORD=your-email-password

*_API_KEY=sk-your-openrouter-key
CORS_ALLOWED_ORIGINS=https://easeapply-hazel.vercel.app,http://localhost:5173
```

### 3️⃣ Run Migrations

```bash
python manage.py migrate
```

### 4️⃣ Start the Server

```bash
python manage.py runserver
```

* Local API: `http://127.0.0.1:8000/api/`
* Swagger docs: `http://127.0.0.1:8000/swagger/`

---

## 🧠 AI Features

### Cover Letter Generation

**POST** `/api/analysis/generate-cover-letter/`

Request:

```json
{
  "resume_id": "uuid-of-resume",
  "job_id": "uuid-of-job"
}
```

Response:

```json
{
  "cover_letter": "Dear Hiring Manager, I’m excited to apply for the Backend Engineer role at XYZ Company..."
}
```

---

## 🔗 API Overview (Key Endpoints)

### Auth

* `POST /api/users/register/` → Register new user
* `POST /api/users/login/` → Obtain JWT token pair
* `POST /api/users/logout/` → Logout and blacklist refresh token
* `GET /api/users/email-verify/{uidb64}/{token}/` → Verify email
* `POST /api/users/password-reset-request/` → Request reset link
* `POST /api/users/reset-password-confirm/` → Reset password
* `PUT /api/users/change-password/` → Change password
* `GET /api/users/profile/` → Get user profile

### Resumes

* `POST /api/resumes/` → Upload & parse resume
* `GET /api/resumes/{id}/` → Retrieve parsed resume
* `PUT /api/resumes/{id}/reparse/` → Reparse resume

### Jobs

* `POST /api/jobs/` → Create job posting
* `GET /api/jobs/my-jobs/` → List jobs for user
* `PUT /api/jobs/reprocess/{id}/` → Reprocess job posting

### Analysis

* `POST /api/analysis/generate-cover-letter/` → Generate cover letter

---

## 📌 Future Enhancements

* ✅ Async AI requests with Celery + Redis
* ✅ LinkedIn job scraping integration
* ✅ Multi-language resume parsing
* ✅ Local AI models (HuggingFace) for cheaper inference
* ✅ Recruiter analytics dashboard

---

## 🏆 Why EaseApply is Awesome

* Real **AI + Django REST Framework** integration
* Demonstrates **resume parsing, and cover letter generation**
* Solves a real HR tech pain point
* Perfect for **portfolio, SaaS MVP, or freelance projects**

---

## 📜 License

MIT License © 2025 Emmanuel Mobolaji

---

