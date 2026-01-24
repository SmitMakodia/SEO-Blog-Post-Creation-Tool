import re
from typing import Dict, List, Set
from dataclasses import dataclass

@dataclass
class ProductAttributes:
    brand: str
    product_type: str
    category: str
    subcategory: str
    key_features: List[str]
    model_number: str
    specifications: Dict[str, str]

class ProductAnalyzer:
    def __init__(self):
        self.brands = {
            'snow joe', 'owala', 'dreo', 'sony', 'samsung', 'apple', 'amazon',
            'bose', 'jbl', 'anker', 'instant pot', 'ninja', 'dyson', 'keurig',
            'philips', 'lg', 'whirlpool', 'cuisinart', 'vitamix', 'kitchenaid'
        }
        
        self.product_types = {
            'heating': ['heater', 'space heater', 'room heater', 'electric heater', 'ceramic heater'],
            'cooling': ['fan', 'air conditioner', 'cooler', 'dehumidifier'],
            'kitchen': ['blender', 'mixer', 'cooker', 'pot', 'kettle', 'toaster'],
            'storage': ['bottle', 'container', 'jar', 'tumbler', 'flask', 'thermos'],
            'cleaning': ['vacuum', 'mop', 'cleaner', 'steamer'],
            'outdoor': ['ice melt', 'deicer', 'salt', 'snow removal', 'lawn mower'],
            'lighting': ['lamp', 'light', 'bulb', 'fixture'],
            'furniture': ['chair', 'table', 'desk', 'shelf', 'rack']
        }
        
        self.feature_patterns = {
            'capacity': r'(\d+)\s*(oz|ml|l|lb|kg|gallon)',
            'power': r'(\d+)\s*(w|watt|watts|kw)',
            'voltage': r'(\d+)\s*v\b',
            'size': r'(\d+)\s*(inch|in|ft|cm)',
            'weight': r'(\d+)\s*(lb|kg|g|oz)',
            'temperature': r'(\d+)\s*(f|fahrenheit|c|celsius)',
            'speed': r'(\d+)\s*speed',
            'mode': r'(\d+)\s*mode'
        }
    
    def analyze(self, product: Dict) -> ProductAttributes:
        title = product['title']
        category = product.get('category', 'general')
        
        brand = self._extract_brand(title)
        product_type, subcategory = self._extract_product_type(title, category)
        features = self._extract_features(title)
        model = self._extract_model_number(title)
        specs = self._extract_specifications(title)
        
        return ProductAttributes(
            brand=brand,
            product_type=product_type,
            category=category,
            subcategory=subcategory,
            key_features=features,
            model_number=model,
            specifications=specs
        )
    
    def _extract_brand(self, title: str) -> str:
        title_lower = title.lower()
        
        for brand in self.brands:
            if brand in title_lower:
                return brand.title()
        
        first_word = title.split()[0]
        if first_word[0].isupper():
            return first_word
        
        return "Generic"
    
    def _extract_product_type(self, title: str, category: str) -> tuple:
        title_lower = title.lower()
        
        for subcategory, types in self.product_types.items():
            for ptype in types:
                if ptype in title_lower:
                    return (ptype, subcategory)
        
        return (category.replace('-', ' '), category)
    
    def _extract_features(self, title: str) -> List[str]:
        features = []
        title_lower = title.lower()
        
        feature_keywords = {
            'insulated', 'portable', 'wireless', 'bluetooth', 'stainless steel',
            'bpa-free', 'leak proof', 'cordless', 'rechargeable', 'digital',
            'smart', 'eco-friendly', 'remote control', 'timer', 'automatic',
            'adjustable', 'foldable', 'dishwasher safe', 'microwave safe',
            'thermal', 'waterproof', 'durable', 'premium', 'professional'
        }
        
        for keyword in feature_keywords:
            if keyword in title_lower:
                features.append(keyword.title())
        
        for feature_name, pattern in self.feature_patterns.items():
            match = re.search(pattern, title_lower)
            if match:
                features.append(f"{match.group(0)}")
        
        return features[:5]
    
    def _extract_model_number(self, title: str) -> str:
        model_pattern = r'\b[A-Z]{2,}[-\d]+[A-Z]*\b'
        match = re.search(model_pattern, title)
        
        if match:
            return match.group(0)
        
        return ""
    
    def _extract_specifications(self, title: str) -> Dict[str, str]:
        specs = {}
        
        for spec_name, pattern in self.feature_patterns.items():
            match = re.search(pattern, title.lower())
            if match:
                specs[spec_name] = match.group(0)
        
        return specs
    
    def generate_search_phrases(self, attrs: ProductAttributes) -> List[str]:
        phrases = []
        
        if attrs.brand != "Generic" and attrs.product_type:
            phrases.append(f"{attrs.brand} {attrs.product_type}")
            phrases.append(f"{attrs.brand} {attrs.product_type} review")
        
        if attrs.product_type:
            phrases.append(f"best {attrs.product_type}")
            phrases.append(f"best {attrs.product_type} 2026")
            phrases.append(f"top rated {attrs.product_type}")
        
        if attrs.product_type and attrs.key_features:
            for feature in attrs.key_features[:2]:
                phrases.append(f"{attrs.product_type} {feature.lower()}")
        
        if attrs.subcategory != attrs.category:
            phrases.append(f"{attrs.subcategory} {attrs.product_type}")
        
        problem_templates = {
            'heater': ['stay warm winter', 'heat small room', 'energy efficient heating'],
            'bottle': ['keep drinks cold', 'water bottle leak proof', 'best hydration'],
            'ice melt': ['safe ice melter', 'pet friendly deicer', 'melt ice quickly'],
            'blender': ['smooth blending', 'crush ice', 'make smoothies'],
            'vacuum': ['remove pet hair', 'clean carpet', 'powerful suction']
        }
        
        for key, templates in problem_templates.items():
            if key in attrs.product_type.lower():
                phrases.extend(templates[:2])
        
        for spec_name, spec_value in attrs.specifications.items():
            if spec_name in ['capacity', 'power']:
                phrases.append(f"{attrs.product_type} {spec_value}")
        
        return list(set(phrases))