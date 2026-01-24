import google.generativeai as genai
from pathlib import Path
import json
import time
import re

class BatchBlogGenerator:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Gemini API Key is missing.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')

    def generate_all_blogs(self, products_with_keywords: list, word_count_min: int = 150, word_count_max: int = 200) -> list:
        """
        Generate all blogs in a single API call.
        """
        prompt = self._build_batch_prompt(products_with_keywords, word_count_min, word_count_max)

        try:
            response = self.model.generate_content(prompt)

            blogs_data = self._parse_response(response.text)

            if not blogs_data:
                print("Error: AI did not return valid JSON.")
                return []

            validated_blogs = []
            for i, blog_data in enumerate(blogs_data):
                if i >= len(products_with_keywords):
                    break

                product = products_with_keywords[i]['product']
                keywords = products_with_keywords[i]['keywords']

                blog = self._validate_and_build_blog(blog_data, product, keywords, word_count_min, word_count_max)
                if blog:
                    validated_blogs.append(blog)

            return validated_blogs

        except Exception as e:
            print(f"Gemini API Error: {e}")
            return []

    def _build_batch_prompt(self, products_with_keywords: list, word_count_min: int, word_count_max: int) -> str:
        products_info = []

        for i, item in enumerate(products_with_keywords, 1):
            p = item['product']
            kws = item['keywords'].get('keywords', [])

            primary = kws[0]['keyword'] if kws else p['title']
            secondary = [k['keyword'] for k in kws[1:4]] if len(kws) > 1 else []

            products_info.append(f"""
PRODUCT {i} DETAILS:
- Title: {p['title']}
- Price: {p.get('price', 'N/A')}
- Platform: Amazon
- Primary Keyword: "{primary}"
- Secondary Keywords: {', '.join(secondary)}
""")

        return f"""
You are an expert SEO content writer and product reviewer.

TASK:
Generate {len(products_with_keywords)} HIGH-QUALITY, SEO-OPTIMIZED blog posts.
Each blog must strictly follow its own product and keyword data.

IMPORTANT GLOBAL RULES:
- Write in an engaging, conversational tone
- Focus on BENEFITS, not just features
- Short paragraphs (2–3 sentences max)
- No fluff, no filler, no repetition
- NO markdown formatting
- RETURN ONLY VALID JSON
- Output must be a JSON ARRAY
- Each array item = ONE blog post

WORD COUNT RULE (MANDATORY):
- Each blog must be between 150 to 200 words.
- Do NOT go below this range.

PER-BLOG SEO RULES:
- Use the Primary Keyword naturally:
  • In the blog title
  • 2–3 times in the content
- Use each Secondary Keyword ONCE (if provided)
- Keyword stuffing is NOT allowed

CONTENT STRUCTURE (PER BLOG):
1. Catchy headline including Primary Keyword
2. Introduction (30–40 words)
3. Key product highlights & benefits (80–100 words)
4. Why customers love it (30–40 words)
5. Closing paragraph with a clear call-to-action (20–30 words)

INPUT DATA:
{''.join(products_info)}

OUTPUT FORMAT (JSON ARRAY ONLY):
[
  {{
    "title": "SEO-optimized title with primary keyword",
    "content": "Full blog post content ({word_count_min}-{word_count_max} words)",
    "meta_description": "SEO meta description (150–160 characters)",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
  }}
]

FINAL REMINDERS:
- Each blog must match its PRODUCT number
- No explanations
- No markdown
- JSON ONLY
"""

    def _parse_response(self, text: str):
        try:
            # Remove code blocks if present
            text = re.sub(r"```json|```", "", text).strip()
            return json.loads(text)
        except Exception as e:
            print(f"Failed to parse AI response: {e}")
            return None

    def _validate_and_build_blog(self, blog_data: dict, product: dict, keywords: dict,
                                 word_count_min: int, word_count_max: int) -> dict:
        required = ['title', 'content']
        if not all(key in blog_data for key in required):
            return None

        # Extract keywords safely
        kws_list = keywords.get('keywords', [])
        primary = kws_list[0]['keyword'] if kws_list else ""
        secondary = [k['keyword'] for k in kws_list[1:4]] if len(kws_list) > 1 else []

        content_word_count = len(blog_data.get('content', '').split())
        #if content_word_count < word_count_min or content_word_count > word_count_max:
            #return None  # discard blogs outside word count range

        return {
            "product_id": product.get('asin', ''),
            "product_title": product['title'],
            "product_url": product.get('url', ''),
            "product_price": product.get('price', 'N/A'),
            "platform": "Amazon",
            "blog_title": blog_data.get('title', ''),
            "blog_content": blog_data.get('content', ''),
            "meta_description": blog_data.get('meta_description', ''),
            "tags": blog_data.get('tags', [])[:5],
            "keywords_used": {
                "primary": primary,
                "secondary": secondary
            },
            "word_count": content_word_count,
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    def save_blogs(self, blogs: list, filepath="data/blogs.json"):
        Path(filepath).parent.mkdir(exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(blogs, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(blogs)} blogs to {filepath}")
        return filepath
