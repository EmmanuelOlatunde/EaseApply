import textwrap

class CoverLetterPrompts:
    """
    Optimized template prompts for generating ATS-ready cover letters.
    Designed for efficiency, maintainability, and high-quality outputs.
    """

    BASE_JOB_INFO = textwrap.dedent("""
        Job Title: {title}
        Company: {company}
        Location: {location}
        Job Type: {job_type}
        Salary Range: {salary_range}
        Requirements: {requirements}
        Skills Required: {skills_required}
        Experience Level: {experience_level}

        Candidate Resume:
        {resume_content}
    """)

    PROFESSIONAL_TEMPLATE = textwrap.dedent("""
        You are an expert cover letter writer and recruitment strategist.
        Write a complete, ATS-optimized, 4-paragraph professional cover letter using the job description and resume below.
        Use clear, confident language and align resume achievements with job requirements.

        {job_info}

        Instructions:
        - Focus on the 3–4 most important job requirements.
        - Use ONLY resume evidence to match those requirements (quantify where possible) without adding false details.
        - Naturally integrate relevant job keywords.
        - Paragraph 1: State the role, express enthusiasm, and provide a value-driven hook.
        - Paragraph 2: Align experience with job duties using strong examples.
        - Paragraph 3: Show interest in the company and cultural fit.
        - Paragraph 4: Reaffirm fit, express interest in an interview, and close professionally.

        Constraints:
        - No placeholders or incomplete letters.
        - If Some details are missing dont leave as placeholders, just remove such details from the cover 
        - Word count: 350–500 words.
        - Ready-to-use, natural, and human-like language.
        - End with a sign-off and the candidate’s full name.
    """)

    CREATIVE_TEMPLATE = textwrap.dedent("""
        You are a creative cover letter expert for marketing, design, and innovation roles.
        Write a memorable, story-driven, personality-rich cover letter using the job description and resume below.

        {job_info}

        Instructions:
        - Use ONLY resume evidence to match requirements (quantify where possible) without adding false details.
        - Avoid generic openings like “I’m applying for…” or “I am excited to apply…”.
        - Start with a bold hook: question, anecdote, or statement linking passion to the company.
        - Use storytelling (STAR method) to showcase 1–2 standout achievements.
        - Match the tone/style of the company (bold, quirky, mission-driven).
        - Express genuine excitement for the role and cultural fit.
        - End with a confident, creative call to action and suitable sign-off.

        Constraints:
        - No placeholders or incomplete letters.
        - Word count: 350–500 words.
        - Ready-to-use, natural, and human-like language.
    """)

    PROMPTS = {
        "professional": PROFESSIONAL_TEMPLATE,
        "creative": CREATIVE_TEMPLATE,
    }

    @classmethod
    def get_prompt(cls, template_type="professional", **kwargs):
        """
        Get a compiled prompt for the given template type.

        Args:
            template_type (str): 'professional' or 'creative'
            **kwargs: Variables for template formatting:
                title, company, location, job_type, salary_range,
                requirements, skills_required, experience_level, resume_content

        Returns:
            str: Fully formatted prompt ready for model input.
        """
        job_info = cls.BASE_JOB_INFO.format(**kwargs)
        template = cls.PROMPTS.get(template_type, cls.PROMPTS["professional"])
        return template.format(job_info=job_info)
