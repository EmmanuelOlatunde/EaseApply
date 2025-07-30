
# ================================
# 13. Sample JSON Request & Response
# ================================
"""
SAMPLE REQUEST:
POST /api/analysis/generate-cover-letter/
Content-Type: application/json
Authorization: Bearer <your_jwt_token>

{
    "job_id": 123,
    "resume_id": 456,
    "template_type": "professional",
    "model": "gpt-4o"
}

SAMPLE SUCCESS RESPONSE:
HTTP 201 Created
{
    "success": true,
    "cover_letter": "Dear Hiring Manager,\n\nI am writing to express my strong interest in the Senior Software Engineer position at your company. With over 5 years of experience in full-stack development and a proven track record of delivering scalable web applications, I am excited about the opportunity to contribute to your team's success.\n\nYour job posting particularly caught my attention because of the emphasis on Django and React development. In my current role at TechCorp, I have successfully led the development of a customer management system using Django REST Framework and React, which improved operational efficiency by 40%. My experience with PostgreSQL, AWS deployment, and agile methodologies aligns perfectly with your requirements.\n\nI am particularly drawn to your company's commitment to innovation and would love to bring my expertise in API development and database optimization to help drive your next generation of products. I would welcome the opportunity to discuss how my background in building robust, user-centric applications can contribute to your team.\n\nThank you for your consideration. I look forward to hearing from you.\n\nSincerely,\n[Your name will be filled based on resume]",
    "analysis_id": 789,
    "metadata": {
        "job_title": "Senior Software Engineer",
        "processing_time": 3.45,
        "tokens_used": 542,
        "model_used": "gpt-4o",
        "created_at": "2025-01-15T10:30:45.123456Z"
    },
    "message": "Cover letter generated successfully"
}

SAMPLE ERROR RESPONSE:
HTTP 400 Bad Request
{
    "success": false,
    "errors": {
        "job_id": ["Job description not found or you don't have permission to access it."],
        "resume_id": ["Resume must have extracted text content for analysis."]
    },
    "message": "Invalid input data"
}

SAMPLE RATE LIMIT ERROR:
HTTP 500 Internal Server Error
{
    "success": false,
    "message": "API rate limit exceeded. Please try again later.",
    "error_type": "rate_limit"
}
"""