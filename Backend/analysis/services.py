import time
import logging
#from django.conf import settings
from typing import Dict, Any
from openai import OpenAI  
import re
import os
logger = logging.getLogger(__name__)

class OpenRouterService:
    """Service class for OpenRouter API integration"""

    def __init__(self):
        self.base_url = "https://openrouter.ai/api/v1"
        self.api_keys = {
            "kimi": os.getenv("OPENROUTER_API_KEY_KIMI"),
            "qwen": os.getenv("OPENROUTER_API_KEY_QWEN"),
            "deepseek": os.getenv("OPENROUTER_API_KEY_DEEPSEEK"),
        }

    def _init_client(self, api_key: str):
        return OpenAI(
            base_url=self.base_url,
            api_key=api_key
        )
    def generate_cover_letter(
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
        from .prompts import CoverLetterPrompts
        prompt_template = CoverLetterPrompts.get_prompt(template_type)

        formatted_prompt = prompt_template.format(
            title=title.strip(),
            company=company.strip(),
            location=location.strip(),
            job_type=job_type.strip(),
            salary_range=salary_range.strip(),
            requirements=requirements.strip(),
            skills_required=skills_required.strip(),
            experience_level=experience_level.strip(),
            resume_content=resume_content.strip()
        )

        fallback_models = [
            ("moonshotai/kimi-k2:free", self.api_keys["kimi"]),
            ("cognitivecomputations/dolphin-mistral-24b-venice-edition:free", self.api_keys["deepseek"]),
            
            ("qwen/qwen3-235b-a22b-2507:free", self.api_keys["qwen"]),   
        ]

        for model_name, key in fallback_models:
            try:
                client = self._init_client(api_key=key)
                start_time = time.time()

                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are a professional career advisor specializing in writing compelling cover letters."},
                        {"role": "user", "content": formatted_prompt}
                    ],
                    max_tokens=800,
                    temperature=0.7,
                    top_p=1.0
                )

                processing_time = time.time() - start_time
                tokens_used = getattr(response.usage, "total_tokens", None)
                cover_letter_raw = response.choices[0].message.content.strip()
                cover_letter_cleaned = re.sub(r"<think>.*?</think>", "", cover_letter_raw, flags=re.DOTALL).strip()

                return {
                    "success": True,
                    "cover_letter": cover_letter_cleaned,
                    "prompt_used": formatted_prompt,
                    "metadata": {
                        "model": model_name,
                        "tokens_used": tokens_used,
                        "processing_time": round(processing_time, 2),
                        "template_type": template_type
                    }
                }

            except Exception as e:
                logger.warning(f"Model {model_name} with key failed: {str(e)}")
                continue  # Try the next model

        return {
            "success": False,
            "error": "All model attempts failed",
            "error_type": "failover"
        }


