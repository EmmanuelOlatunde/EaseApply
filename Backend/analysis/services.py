import os
import re
import time
import logging
import asyncio
from typing import Dict, Any, Optional
from openai import AsyncOpenAI  

logger = logging.getLogger(__name__)


class OpenRouterService:
    """Service class for OpenRouter API integration with async parallel failover."""

    BASE_URL = "https://openrouter.ai/api/v1"

    FALLBACK_MODELS = [
        #("google/gemma-2-9b-it:free", "OPENROUTER_API_KEY_DEEPSEEK"),
        # ("qwen/qwen-2.5-72b-instruct:free", "OPENROUTER_API_KEY_KIMI"),
        ("moonshotai/kimi-k2:free", "OPENROUTER_API_KEY_KIMI"),
        ("cognitivecomputations/dolphin-mistral-24b-venice-edition:free", "OPENROUTER_API_KEY_DEEPSEEK"),
        ("qwen/qwen3-235b-a22b:free", "OPENROUTER_API_KEY_QWEN"),
    ]

    SYSTEM_PROMPT = (
        "You are a professional career advisor specializing in writing compelling cover letters."
    )

    def __init__(self):
        # Load API keys once
        self.api_keys = {env_key: os.getenv(env_key) for _, env_key in self.FALLBACK_MODELS}

    def _clean_text(self, text: Optional[str]) -> str:
        return (text or "").strip()

    def _remove_think_tags(self, text: str) -> str:
        return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    def _build_prompt(self, title: str, company: str, location: str, job_type: str, 
                    salary_range: str, requirements: str, skills_required: str, 
                    experience_level: str, resume_content: str, template_type: str) -> str:
        from .prompts import CoverLetterPrompts
        
        # Ensure all required fields have values
        params = {
            'title': self._clean_text(title) or 'Not specified',
            'company': self._clean_text(company) or 'Not specified',
            'location': self._clean_text(location) or 'Not specified',
            'job_type': self._clean_text(job_type) or 'Not specified',
            'salary_range': self._clean_text(salary_range) or 'Not specified',
            'requirements': self._clean_text(requirements) or 'Not specified',
            'skills_required': self._clean_text(skills_required) or 'Not specified',
            'experience_level': self._clean_text(experience_level) or 'Not specified',
            'resume_content': self._clean_text(resume_content) or 'No resume content provided'
        }
        
        return CoverLetterPrompts.get_prompt(template_type=template_type, **params)    


    async def _try_model(self, model_name: str, api_key: str, prompt: str) -> Optional[Dict[str, Any]]:
        """Try generating a cover letter with a specific model."""
        if not api_key:
            logger.warning(f"Skipping {model_name} - API key not found")
            return None

        try:
            client = AsyncOpenAI(base_url=self.BASE_URL, api_key=api_key)
            start_time = time.time()

            response = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.7,
                top_p=1.0
            )

            processing_time = round(time.time() - start_time, 2)
            tokens_used = getattr(response.usage, "total_tokens", None)

            cover_letter = self._remove_think_tags(response.choices[0].message.content.strip())

            return {
                "success": True,
                "cover_letter": cover_letter,
                "prompt_used": prompt,
                "metadata": {
                    "model": model_name,
                    "tokens_used": tokens_used,
                    "processing_time": processing_time,
                }
            }

        except Exception as e:
            logger.warning(f"Model {model_name} failed: {e}")
            return None

    async def generate_cover_letter(
        self,
        title: str,
        company: str,
        location: str,
        job_type: str,
        salary_range: str,
        requirements: str,
        skills_required: str,
        experience_level: str,
        resume_content: str,
        template_type: str = "professional",
    ) -> Dict[str, Any]:
        """Generate a cover letter using available models in parallel, returning the first success."""
        prompt = self._build_prompt(
            title, company, location, job_type, salary_range,
            requirements, skills_required, experience_level,
            resume_content, template_type
        )

        tasks = [
            self._try_model(model, self.api_keys[env_key], prompt)
            for model, env_key in self.FALLBACK_MODELS
        ]

        for task in asyncio.as_completed(tasks):
            result = await task
            if result:
                result["metadata"]["template_type"] = template_type
                return result

        return {"success": False, "error": "All model attempts failed", "error_type": "failover"}
