import json
import time
from typing import List
import requests
from urllib.parse import urlencode
from parsel import Selector
from loguru import logger as log
import pandas as pd
from pandas import DataFrame
from constants import *

def create_search_url(query: str, page=1, sort="price_low") -> str:
    """create url for a single walmart search page"""
    return "https://www.walmart.com/search?" + urlencode(
        {
            "q": query,
            "sort": sort,
            "page": page,
            "affinityOverride": "default",
        }
    )

def parse_search(html_text: str):
    """extract search results from search HTML response"""
    sel = Selector(text=html_text)
    data = sel.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
    data = json.loads(data)

    total_results = data["props"]["pageProps"]["initialData"]["searchResult"]["itemStacks"][0]["count"]
    results = data["props"]["pageProps"]["initialData"]["searchResult"]["itemStacks"][0]['items']
    return results, total_results

def parse_product(html_text: str):
    """parse walmart product from product page response"""
    sel = Selector(text=html_text)
    data = sel.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
    if data != None: # This verification is because we might get an html with no content
        data = json.loads(data)
        _product_raw = data["props"]["pageProps"]["initialData"]["data"]["product"]
        wanted_product_keys = [
            "availabilityStatus",
            "averageRating",
            "brand",
            "id",
            "imageInfo",
            "manufacturerName",
            "name",
            "model",
            "category.path"
            "orderLimit",
            "orderMinLimit",
            "priceInfo",
            "shortDescription",
            "type",
        ]
        product = {k: v for k, v in _product_raw.items() if k in wanted_product_keys}
        reviews_raw = data["props"]["pageProps"]["initialData"]["data"]["reviews"]
        product['reviews'] = reviews_raw
        return product

def scrape_products_by_url(urls: List[str], df: DataFrame) -> DataFrame:
    """scrape walmart products by urls"""
    log.info(f"scraping {len(urls)} product urls (in chunks of 50)")
    for url in urls:
        html = requests.get(url, headers=headers_product_detail) #headers are important because they might hid the fact that this is an actual bot
        product = parse_product(html.text)
        time.sleep(10) # fake being a real user
        if product != None:
            df = df.append(pd.json_normalize(product), ignore_index=True)
        
        http_status = 'Successfully' if html.status_code == 200 else 'Unsuccessfully'
        log.info(f'Scraped {url} {http_status} waiting...')
    
    return df
