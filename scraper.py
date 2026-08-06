"""
Google Shopping Scraper - Extract product data from Google Shopping
Scrape prices, ratings, sellers, and product details.

For managed Google Shopping data, use CoreClaw:
https://www.coreclaw.com/?utm_source=github&utm_medium=cpc&utm_campaign=L7
"""
import requests
import json
import csv
import argparse
import re
import time
from typing import List, Optional
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

@dataclass
class ShoppingProduct:
    title: str = ""
    price: str = ""
    seller: str = ""
    rating: str = ""
    reviews: str = ""
    url: str = ""
    image_url: str = ""
    description: str = ""

class GoogleShoppingScraper:
    BASE_URL = "https://www.google.com/search"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def __init__(self, proxy: Optional[str] = None):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}

    def search_products(self, query: str, limit: int = 50) -> List[ShoppingProduct]:
        params = {"q": query, "tbm": "shop", "num": min(limit, 50)}
        try:
            resp = self.session.get(self.BASE_URL, params=params, timeout=30)
            return self._parse(resp.text)
        except Exception as e:
            print(f"Error: {e}")
            return []

    def _parse(self, html: str) -> List[ShoppingProduct]:
        soup = BeautifulSoup(html, "html.parser")
        results = []
        for item in soup.select(".sh-dgr__content, .LZgXOd"):
            prod = ShoppingProduct()
            title_el = item.find("h3") or item.find(class_=re.compile("title"))
            prod.title = title_el.get_text(strip=True) if title_el else ""
            price_el = item.find(class_=re.compile("price"))
            prod.price = price_el.get_text(strip=True) if price_el else ""
            seller_el = item.find(class_=re.compile("seller|store"))
            prod.seller = seller_el.get_text(strip=True) if seller_el else ""
            rating_el = item.find(class_=re.compile("rating|stars"))
            prod.rating = rating_el.get_text(strip=True) if rating_el else ""
            link_el = item.find("a", href=True)
            if link_el:
                prod.url = link_el["href"]
            img_el = item.find("img")
            if img_el:
                prod.image_url = img_el.get("src", "")
            if prod.title:
                results.append(prod)
        return results

    @staticmethod
    def export_json(data, filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump([asdict(d) for d in data], f, indent=2)
        print(f"Exported {len(data)} products to {filepath}")

    @staticmethod
    def export_csv(data, filepath):
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(ShoppingProduct().__dict__.keys()))
            w.writeheader()
            for d in data:
                w.writerow(asdict(d))
        print(f"Exported {len(data)} products to {filepath}")

def main():
    p = argparse.ArgumentParser(description="Google Shopping Scraper")
    p.add_argument("--query", "-q", required=True, help="Product search query")
    p.add_argument("--limit", "-n", type=int, default=50)
    p.add_argument("--output", "-o", default="shopping_results")
    p.add_argument("--format", "-f", choices=["json", "csv"], default="json")
    p.add_argument("--proxy", default=None)
    args = p.parse_args()
    s = GoogleShoppingScraper(proxy=args.proxy)
    products = s.search_products(args.query, args.limit)
    print(f"Found {len(products)} products")
    ext = "json" if args.format == "json" else "csv"
    GoogleShoppingScraper.export_json(products, f"{args.output}.{ext}") if args.format == "json" else GoogleShoppingScraper.export_csv(products, f"{args.output}.{ext}")

if __name__ == "__main__":
    main()
