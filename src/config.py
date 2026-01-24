import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
TEMPLATES_DIR = BASE_DIR / "templates"

DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  
HASHNODE_ACCESS_TOKEN = os.getenv("HASHNODE_ACCESS_TOKEN") 
HASHNODE_PUBLICATION_ID = os.getenv("HASHNODE_PUBLICATION_ID") 

AMAZON_BASE_URL = "https://www.amazon.com"
EBAY_BASE_URL = "https://www.ebay.com"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# SEO Settings - TASK COMPLIANT & OPTIMIZED
TARGET_KEYWORDS_COUNT = 4  # Task requirement: 3-4 keywords
MIN_SEARCH_VOLUME = 5  # Lowered for realistic Trends data
MIN_RELEVANCE_SCORE = 0.35  # 35% minimum semantic match
BLOG_WORD_COUNT_MIN = 150  # Task requirement
BLOG_WORD_COUNT_MAX = 200  # Task requirement

# Keyword Research Settings
KEYWORD_SOURCES = {
    "google_autocomplete": True,
    "google_trends": True,
    "google_related": True,
    "amazon_autocomplete": True,
    "question_keywords": True,
}

# Quality Thresholds (adjusted for realistic volumes)
QUALITY_THRESHOLDS = {
    "excellent": 50,
    "good": 20,
    "acceptable": 10,
    "poor": 0
}

# Intent Patterns
INTENT_PATTERNS = {
    "transactional": ["buy", "price", "cheap", "deal", "sale", "discount", "coupon", "purchase", "order", "shop"],
    "commercial": ["best", "top", "review", "vs", "comparison", "alternative", "recommended", "rated", "worth"],
    "informational": ["how", "what", "why", "guide", "tutorial", "tips", "learn", "explained", "difference"],
    "navigational": ["amazon", "walmart", "official", "website"]
}

# Publishing
PUBLISH_TO_HASHNODE = True
AUTO_PUBLISH = True
PUBLISH_STATUS = "draft"  # or "published"