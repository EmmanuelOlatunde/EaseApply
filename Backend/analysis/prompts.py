import textwrap

class CoverLetterPrompts:
    """
    Enhanced template prompts for generating high-quality cover letters.

    This class provides a structured way to generate different styles of cover letters
    by providing detailed, expert-level prompts to a language model.
    """

    # --- IMPROVED PROMPTS ---

    PROFESSIONAL_COVER_LETTER = textwrap.dedent("""
        You are an expert cover letter writer and recruitment strategist. Write a complete, ATS-optimized, 4-paragraph professional cover letter based on the job description and resume below. Use clear, confident language and match resume achievements to job requirements.

        Job Description:
            Job title = {title} ,
            company name ={company},
            location={location},
            job_type={job_type},
            salary_range={salary_range},
            requirements={requirements},
            skills_required={skills_required},
            experience_level={experience_level},

        Candidate Resume:
        {resume_content}

        Instructions:
        - Focus on the 3–4 most important job requirements.
        - Use Only resume evidence to match those requirements (quantified where possible) dont falsify any information.
        - Integrate relevant job keywords naturally.
        - Paragraph 1: State the role, express enthusiasm, give a value-driven hook.
        - Paragraph 2: Align experience with job duties using strong examples.
        - Paragraph 3: Show interest in the company and culture fit.
        - Paragraph 4: Reaffirm fit, express interest in interview, close professionally.

        Constraints:
        - Word count: 350–500 words.
        - Output must be ready-to-use. 
        - End with a sign-off and candidate's full name.
        - Use natural, simple words and gramatical expressions in human-like language.
        - Make sure there is No placeholders or incomplete letters.         
    """)

    CREATIVE_COVER_LETTER = textwrap.dedent("""
            You are a creative cover letter expert who helps candidates in marketing, design, and innovation roles stand out. Write a memorable, story-driven, and personality-rich cover letter based on the job description and resume below.

            Job Description:
                Job title = {title} ,
                company name ={company},
                location={location},
                job_type={job_type},
                salary_range={salary_range},
                requirements={requirements},
                skills_required={skills_required},
                experience_level={experience_level},

            Candidate Resume:
            {resume_content}

            Instructions:
            - Use Only resume evidence to match those requirements (quantified where possible) dont falsify any information.
            - Avoid generic openings like “I’m applying for..., I am excited to apply…”
            - Start with a bold hook: a question, anecdote, or statement linking passion to the company.
            - Use storytelling to showcase 1–2 standout achievements (STAR method recommended).
            - Reflect the tone/style of the company (e.g., bold, quirky, mission-driven).
            - Express genuine excitement for the role and cultural fit.
            - End with a confident, creative call to action.
            - Close with a suitable sign-off and the candidate's full name.

            Constraints:
            - Word count: 350–500 words.
            - Output must be ready-to-use. 
            - Use natural, human-like language that balances creativity with professionalism.
            - Use natural, simple words and gramatical expressions in human-like language.
            - Make sure there is No placeholders or incomplete letters.
             
    """)


    # Using a dictionary for scalability and easy management of templates
    PROMPTS = {
        "professional": PROFESSIONAL_COVER_LETTER,
        "creative": CREATIVE_COVER_LETTER,
    
    }

    @classmethod
    def get_prompt(cls, template_type="professional"):
        """
        Get prompt template by type.
        
        Args:
            template_type (str): Type of cover letter ('professional', 'creative', 'bullet_point')
            
        Returns:
            str: The prompt template
        """
        return cls.PROMPTS.get(template_type, cls.PROFESSIONAL_COVER_LETTER)