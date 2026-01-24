import google.generativeai as genai
from pathlib import Path
import json
import time
from typing import Dict, List
from src.utils import setup_logger

logger = setup_logger("blog_generator")

class BlogGenerator:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
        self.generated_blogs = []
    
    def create_blog_post(self, product: Dict, keywords: List[Dict], 
                        word_count_min=150, word_count_max=200, retries=3) -> Dict:
        logger.info(f"Generating blog for: {product['title'][:50]}...")
        
        target_keywords = [kw['keyword'] for kw in keywords[:4]]
        primary_keyword = target_keywords[0]
        
        logger.info(f"Target keywords: {', '.join(target_keywords)}")
        
        prompt = f"""You are an expert SEO content writer and product reviewer.

TASK: Write a compelling, SEO-optimized blog post about this product.

PRODUCT DETAILS:
- Title: {product['title']}
- Price: {product.get('price', 'N/A')}
- Platform: {product.get('platform', 'E-commerce')}
- Rating: {product.get('rating', 'N/A')}

SEO REQUIREMENTS:
- Primary Keyword: "{primary_keyword}" (use 2-3 times naturally)
- Secondary Keywords: {', '.join(target_keywords[1:])} (use once each)
- Word Count: {word_count_min}-{word_count_max} words
- Include a catchy headline with primary keyword
- Write in engaging, conversational tone
- Focus on benefits, not just features
- Add a call-to-action at the end

CONTENT STRUCTURE:
1. Attention-grabbing intro (30-40 words)
2. Key product highlights (80-100 words)
3. Why customers love it (30-40 words)
4. Closing with CTA (20-30 words)

OUTPUT FORMAT (JSON):
{{
  "title": "Blog post title with primary keyword",
  "content": "Full blog post content ({word_count_min}-{word_count_max} words)",
  "meta_description": "SEO meta description (150-160 characters)",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}

IMPORTANT: 
- Make keyword usage natural, not forced
- Focus on reader value, not just SEO
- Keep paragraphs short (2-3 sentences)
- No fluff or filler content
- Return ONLY valid JSON, no markdown formatting
"""
        
        for attempt in range(retries):
            try:
                logger.info(f"Generating with Gemini AI (Attempt {attempt + 1}/{retries})...")
                response = self.model.generate_content(prompt)
                
                response_text = response.text.strip()
                
                if response_text.startswith('```json'):
                    response_text = response_text.split('```json')[1].split('```')[0].strip()
                elif response_text.startswith('```'):
                    response_text = response_text.split('```')[1].split('```')[0].strip()
                
                blog_data = json.loads(response_text)
                
                blog_post = {
                    "product_id": product.get('asin') or product.get('url', ''),
                    "product_title": product['title'],
                    "product_url": product.get('url', ''),
                    "product_price": product.get('price', 'N/A'),
                    "platform": product.get('platform', 'E-commerce'),
                    "blog_title": blog_data.get('title', ''),
                    "blog_content": blog_data.get('content', ''),
                    "meta_description": blog_data.get('meta_description', ''),
                    "tags": blog_data.get('tags', []),
                    "target_keywords": target_keywords,
                    "word_count": len(blog_data.get('content', '').split()),
                    "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                actual_words = blog_post['word_count']
                if actual_words < word_count_min - 10:
                    logger.warning(f"Content too short ({actual_words} words), regenerating...")
                    pass 
                elif actual_words > word_count_max + 50:
                    logger.warning(f"Content too long ({actual_words} words), truncating...")
                    words = blog_post['blog_content'].split()
                    blog_post['blog_content'] = ' '.join(words[:word_count_max])
                    blog_post['word_count'] = word_count_max
                
                logger.info(f"Blog generated: {blog_post['blog_title']} ({blog_post['word_count']} words)")
                
                self.generated_blogs.append(blog_post)
                return blog_post
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response: {e}")
                return None
            except Exception as e:
                if "429" in str(e):
                    logger.warning(f"Quota exceeded. Waiting 35 seconds before retry...")
                    time.sleep(35) 
                    continue
                else:
                    logger.error(f"Blog generation failed: {e}")
                    return None
        
        logger.error("Max retries reached. Could not generate blog.")
        return None
    
    def save_blogs(self, filepath="data/blogs.json"):
        Path(filepath).parent.mkdir(exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.generated_blogs, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(self.generated_blogs)} blogs to {filepath}")
        return filepath