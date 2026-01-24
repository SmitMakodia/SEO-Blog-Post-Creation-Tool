import sys
from src.scraper import ProductScraper
from src.keyword_research import KeywordResearcher
from src.blog_generator import BlogGenerator
from src.publisher import HashnodePublisher
from src.config import GEMINI_API_KEY, HASHNODE_ACCESS_TOKEN, HASHNODE_PUBLICATION_ID, TARGET_KEYWORDS_COUNT, BLOG_WORD_COUNT_MIN, BLOG_WORD_COUNT_MAX, PUBLISH_TO_HASHNODE

def main():
    print("\nSEO Blog Post Creation Tool\n")

    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY not set")
        return 1

    scraper = ProductScraper()
    researcher = KeywordResearcher()
    generator = BlogGenerator(api_key=GEMINI_API_KEY)
    publisher = HashnodePublisher(api_key=HASHNODE_ACCESS_TOKEN, publication_id=HASHNODE_PUBLICATION_ID)

    categories = {"1": "electronics", "2": "home-garden", "3": "sports", "4": "books"}
    print("Categories:")
    for k, v in categories.items():
        print(f"  {k}. {v}")
    choice = input("\nSelect (1-4) [1]: ").strip() or "1"
    category = categories.get(choice, "electronics")

    products = scraper.scrape_amazon_bestsellers(category=category, max_products=1)
    if not products:
        print("\nNo products found")
        return 1
    scraper.save_products()

    keywords_data = researcher.research_all_products(products, TARGET_KEYWORDS_COUNT)
    researcher.save_keywords(keywords_data)

    products_with_keywords = [{"product": products[i], "keywords": keywords_data[i]} for i in range(len(products))]
    blogs = []
    for item in products_with_keywords:
        product = item['product']
        keywords = item['keywords'].get('keywords', [])  # ensure it's a list
        blog = generator.create_blog_post(
            product,
            keywords,
            word_count_min=BLOG_WORD_COUNT_MIN,
            word_count_max=BLOG_WORD_COUNT_MAX
        )
        if blog:
            blogs.append(blog)
    if not blogs:
        print("\nGenerated 0 blogs")
        return 1
    generator.save_blogs(filepath="data/blogs.json")

    if PUBLISH_TO_HASHNODE and HASHNODE_ACCESS_TOKEN and HASHNODE_PUBLICATION_ID:
        publisher.publish_all(blogs)
        publisher.save_published_log()
        for p in publisher.published_posts:
            print(p.get("url", ""))

    print("\nDone")
    return 0

if __name__ == "__main__":
    sys.exit(main())
