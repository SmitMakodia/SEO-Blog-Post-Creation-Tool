import requests
from pytrends.request import TrendReq
import json
import time
from pathlib import Path
from difflib import SequenceMatcher
from .product_analyzer import ProductAnalyzer

class KeywordResearcher:
    def __init__(self):
        self.pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
        self.product_analyzer = ProductAnalyzer()
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    def research_all_products(self, products: list, target_count: int = 4) -> list:
        results = []
        for product in products:
            keywords = self._research_single_product(product, target_count)
            results.append(keywords)
            time.sleep(1)
        return results

    def _research_single_product(self, product: dict, target_count: int) -> dict:
        attrs = self.product_analyzer.analyze(product)
        seed_phrases = self.product_analyzer.generate_search_phrases(attrs)
        
        all_keywords = set(seed_phrases)
        
        # 1. Google Autocomplete
        for seed in seed_phrases[:4]:
            self._fetch_google_suggestions(seed, all_keywords)
        
        # 2. Amazon Autocomplete (Buyer Intent)
        base_term = f"{attrs.brand} {attrs.product_type}" if attrs.brand != "Generic" else attrs.product_type
        self._fetch_amazon_suggestions(base_term, all_keywords)

        # 3. Filter & Score
        scored_keywords = []
        for kw in all_keywords:
            relevance = self._calculate_relevance(kw, product, attrs)
            if relevance >= 0.35: # Min relevance threshold
                composite = self._calculate_composite_score(kw, relevance, attrs)
                scored_keywords.append(composite)
        
        # 4. Diversify & Select
        scored_keywords.sort(key=lambda x: x['composite_score'], reverse=True)
        final_keywords = self._diversify_keywords(scored_keywords, target_count, attrs)

        if not final_keywords:
            final_keywords = [{"keyword": product['title'][:50], "score": 1.0}]

        return {
            "product_id": product.get('asin', ''),
            "keywords": final_keywords
        }

    def _fetch_google_suggestions(self, seed, keywords_set):
        try:
            url = "http://suggestqueries.google.com/complete/search"
            params = {'client': 'firefox', 'q': seed}
            resp = requests.get(url, params=params, timeout=2)
            if resp.status_code == 200:
                keywords_set.update(resp.json()[1][:6])
        except: pass

    def _fetch_amazon_suggestions(self, seed, keywords_set):
        try:
            url = "https://completion.amazon.com/api/2017/suggestions"
            params = {'mid': 'ATVPDKIKX0DER', 'alias': 'aps', 'prefix': seed}
            resp = requests.get(url, params=params, headers=self.headers, timeout=2)
            data = resp.json()
            if 'suggestions' in data:
                for item in data['suggestions'][:8]:
                    if 'value' in item: keywords_set.add(item['value'])
        except: pass

    def _calculate_relevance(self, keyword: str, product: dict, attrs) -> float:
        kw_lower = keyword.lower()
        brand = getattr(attrs, 'brand', '') or ''
        ptype = getattr(attrs, 'product_type', '') or ''
        features = getattr(attrs, 'key_features', []) or []
        
        score = 0
        if brand.lower() in kw_lower: score += 0.25
        if ptype.lower() in kw_lower: score += 0.35
        
        # Feature match
        if any(f.lower() in kw_lower for f in features): score += 0.15
            
        # Word overlap
        kw_words = set(kw_lower.split())
        title_words = set(product['title'].lower().split())
        overlap = len(kw_words.intersection(title_words))
        score += (overlap / len(kw_words)) * 0.15 if kw_words else 0
        
        # Sequence match
        score += SequenceMatcher(None, kw_lower, product['title'].lower()).ratio() * 0.1
        return score

    def _calculate_composite_score(self, keyword, relevance, attrs):
        # Estimate volume based on intent since Trends API is slow/unreliable in batch
        intent = self._classify_intent(keyword, attrs)
        base_vol = 20
        if intent == 'transactional': base_vol = 50
        elif intent == 'commercial': base_vol = 40
        
        composite = (base_vol * 0.3) + (relevance * 100 * 0.4) + (20 if intent in ['transactional','commercial'] else 10)
        
        return {
            "keyword": keyword,
            "composite_score": round(composite, 1),
            "search_intent": intent
        }

    def _classify_intent(self, keyword, attrs):
        kw = keyword.lower()
        if any(x in kw for x in ['buy', 'price', 'deal', 'sale', 'cost']): return 'transactional'
        if any(x in kw for x in ['best', 'top', 'review', 'vs', 'compare']): return 'commercial'
        if any(x in kw for x in ['how', 'what', 'guide', 'tutorial']): return 'informational'
        brand = getattr(attrs, 'brand', '').lower()
        if brand and brand in kw: return 'navigational'
        return 'mixed'

    def _diversify_keywords(self, scored_kws, target_count, attrs):
        selected = []
        by_intent = {}
        for kw in scored_kws:
            i = kw['search_intent']
            if i not in by_intent: by_intent[i] = []
            by_intent[i].append(kw)
            
        priority = ['commercial', 'transactional', 'informational', 'navigational', 'mixed']
        
        while len(selected) < target_count and scored_kws:
            added_this_round = False
            for intent in priority:
                if intent in by_intent and by_intent[intent] and len(selected) < target_count:
                    selected.append(by_intent[intent].pop(0))
                    added_this_round = True
            if not added_this_round: # Fill rest with whatever is highest score
                remaining = [k for k in scored_kws if k not in selected]
                if remaining: selected.append(remaining[0])
                else: break
                
        return selected[:target_count]

    def save_keywords(self, keywords_data: list, filepath="data/keywords.json"):
        Path(filepath).parent.mkdir(exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(keywords_data, f, indent=2, ensure_ascii=False)
        return filepath
