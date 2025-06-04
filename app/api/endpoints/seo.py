from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from openai import OpenAI
from ...core.config import settings
from ...core.logger import get_logger

logger = get_logger()
router = APIRouter()

class SEORequest(BaseModel):
    description: str

class SEOResponse(BaseModel):
    status_code: int
    message: str
    keywords: List[str]
    error: str = None

@router.post("/generate-keywords", response_model=SEOResponse)
async def generate_seo_keywords(request: SEORequest):
    """Generate SEO keywords based on the provided description using GPT"""
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Craft the prompt for SEO keyword generation
        prompt = f"""
        Generate a list of relevant SEO keywords based on the following description. 
        The keywords should be specific, relevant, and optimized for search engines.
        
        Description: {request.description}
        
        Please provide only the keywords, separated by commas.
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an SEO expert. Provide specific, relevant keywords based on the given description."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        # Extract and process keywords from the response
        keywords_text = response.choices[0].message.content.strip()
        keywords = [keyword.strip() for keyword in keywords_text.split(',')]
        
        logger.info(f"Generated {len(keywords)} SEO keywords")
        
        return SEOResponse(
            status_code=7000,
            message="SEO keywords generated successfully",
            keywords=keywords
        )
        
    except Exception as e:
        logger.error(f"SEO keyword generation failed: {str(e)}")
        return SEOResponse(
            status_code=7001,
            message="Failed to generate SEO keywords",
            keywords=[],
            error=str(e)
        )
