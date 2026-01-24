import json
import time
from pathlib import Path
import requests

class HashnodePublisher:
    def __init__(self, api_key=None, publication_id=None):
        self.api_key = api_key
        self.publication_id = publication_id
        self.published_posts = []

    def publish_all(self, blogs, tags_limit=5):
        for blog in blogs:
            r = self.publish_to_hashnode(blog, tags_limit=tags_limit)
            if r:
                self.published_posts.append(r)
            time.sleep(2)

    def publish_to_hashnode(self, blog, tags_limit=5):
        if not self.api_key or not self.publication_id:
            return None

        url = "https://gql.hashnode.com"
        headers = {"Authorization": self.api_key, "Content-Type": "application/json"}

        tags = []
        for t in (blog.get("tags") or [])[:tags_limit]:
            name = str(t).strip()
            if not name:
                continue
            tags.append({"slug": name.lower().replace(" ", "-"), "name": name})

        content = self._md(blog)

        query = """
mutation PublishPost($input: PublishPostInput!) {
  publishPost(input: $input) {
    post { id url title }
  }
}
""".strip()

        variables = {
            "input": {
                "title": blog["blog_title"],
                "contentMarkdown": content,
                "publicationId": self.publication_id,
                "tags": tags
            }
        }

        try:
            resp = requests.post(url, headers=headers, json={"query": query, "variables": variables}, timeout=30)
            if resp.status_code != 200:
                return None
            data = resp.json()
            post = (((data.get("data") or {}).get("publishPost") or {}).get("post") or None)
            if not post:
                return None
            return {
                "platform": "Hashnode",
                "post_id": post.get("id", ""),
                "url": post.get("url", ""),
                "title": post.get("title", ""),
                "published_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception:
            return None

    def _md(self, blog):
        cta = f"\n\n---\n\nCheck out this product: [{blog.get('product_title','')}]({blog.get('product_url','#')})\n"
        return (blog.get("blog_content") or "").strip() + cta

    def save_published_log(self, filepath="data/published.json"):
        Path(filepath).parent.mkdir(exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.published_posts, f, indent=2, ensure_ascii=False)
        return filepath
