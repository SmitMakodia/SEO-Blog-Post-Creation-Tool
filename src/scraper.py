import requests
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from src.utils import setup_logger

logger = setup_logger("scraper")

class ProductScraper:
    def __init__(self, headless=True):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        self.headless = headless
        self.products = []
        self.driver = None

    def _get_selenium_driver(self):
        if self.driver:
            return self.driver
            
        logger.info("Initializing Selenium WebDriver...")
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(f"user-agent={self.headers['User-Agent']}")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            return self.driver
        except Exception as e:
            logger.error(f"Failed to initialize Selenium: {e}")
            return None

    def _get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        try:
            time.sleep(random.uniform(2, 5))
            
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                return BeautifulSoup(response.content, 'lxml')
            elif response.status_code == 429:
                logger.warning(f"Requests blocked (429). Switching to Selenium...")
            else:
                logger.warning(f"Request failed with status {response.status_code}. Trying Selenium...")
                
        except Exception as e:
            logger.warning(f"Request failed: {e}. Switching to Selenium...")

        driver = self._get_selenium_driver()
        if not driver:
            return None
            
        try:
            driver.get(url)
            time.sleep(5) 
            
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
            time.sleep(2)
            
            return BeautifulSoup(driver.page_source, 'lxml')
        except Exception as e:
            logger.error(f"Selenium navigation failed: {e}")
            return None

    def cleanup(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

    def scrape_amazon_bestsellers(self, category="electronics", max_products=10):
        logger.info(f"Scraping Amazon Best Sellers ({category})...")
        
        category_urls = {
            "electronics": "https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics",
            "home-garden": "https://www.amazon.com/Best-Sellers-Home-Garden/zgbs/home-garden",
            "sports": "https://www.amazon.com/Best-Sellers-Sports-Outdoors/zgbs/sporting-goods",
            "books": "https://www.amazon.com/Best-Sellers-Books/zgbs/books",
            "toys": "https://www.amazon.com/Best-Sellers-Toys-Games/zgbs/toys-and-games",
            "fashion": "https://www.amazon.com/Best-Sellers-Fashion/zgbs/fashion"
        }
        
        url = category_urls.get(category, category_urls["electronics"])
        
        soup = self._get_page_content(url)
        if not soup:
            logger.error("Failed to retrieve Amazon page content.")
            return []

        products_found = []
        product_divs = soup.find_all('div', {'class': 'zg-grid-general-faceout'})[:max_products]
        
        if not product_divs:
            product_divs = soup.select('div[id^="gridItemRoot"]')[:max_products]
            
        if not product_divs:
            logger.warning("No product elements found on Amazon page.")

        for idx, div in enumerate(product_divs, 1):
            try:
                title_tag = div.find('div', {'class': '_cDEzb_p13n-sc-css-line-clamp-3_g3dy1'})
                if not title_tag:
                    title_tag = div.find('a', {'class': 'a-link-normal'})
                    if title_tag:
                        span = title_tag.find('span')
                        if span: title_tag = span
                
                title = title_tag.get_text(strip=True) if title_tag else "Unknown Product"
                
                link_tag = div.find('a', href=True)
                product_url = "https://www.amazon.com" + link_tag['href'] if link_tag else ""
                
                price = "N/A"
                price_tag = div.find('span', {'class': '_cDEzb_p13n-sc-price_3mJ9Z'})
                if not price_tag:
                    price_tag = div.find('span', {'class': 'p13n-sc-price'})
                if not price_tag:
                    price_tag = div.find('span', {'class': 'a-price-whole'})
                    if price_tag:
                        fraction = div.find('span', {'class': 'a-price-fraction'})
                        if fraction:
                            price = f"${price_tag.get_text(strip=True)}.{fraction.get_text(strip=True)}"
                        else:
                            price = price_tag.get_text(strip=True)
                
                if price == "N/A" and price_tag:
                     price = price_tag.get_text(strip=True)

                rating_tag = div.find('span', {'class': 'a-icon-alt'})
                rating = rating_tag.get_text(strip=True) if rating_tag else "N/A"
                
                asin = product_url.split('/dp/')[-1].split('/')[0] if '/dp/' in product_url else None
                
                product = {
                    "rank": idx,
                    "title": title,
                    "price": price,
                    "rating": rating,
                    "url": product_url,
                    "asin": asin,
                    "category": category,
                    "platform": "Amazon",
                    "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                products_found.append(product)
                logger.info(f"Scraped Amazon: {title[:60]}... ({price})")
                
            except Exception as e:
                logger.error(f"Error parsing product {idx}: {e}")
                continue
        
        self.products.extend(products_found)
        logger.info(f"Total Amazon products: {len(products_found)}")
        return products_found
    
    def save_products(self, filepath="data/products.json"):
        Path(filepath).parent.mkdir(exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.products, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(self.products)} products to {filepath}")
        return filepath
    
    def __del__(self):
        self.cleanup()