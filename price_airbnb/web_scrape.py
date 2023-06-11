import re

import numpy as np
import requests
from bs4 import BeautifulSoup

def scrape_page(page_url):
    """Extracts HTML from a webpage"""

    answer = requests.get(page_url)
    content = answer.content
    soup = BeautifulSoup(content, features='html.parser')

    return soup

def extract_listing(page_url, class_name="pquyp1l"):
    """Extracts listings from an Airbnb search page"""

    page_soup = scrape_page(page_url)
    listings = page_soup.findAll("div", {"class": class_name})

    return listings

def extract_prices(page_url):
    """Extracts prices from an Airbnb search page"""

    page_soup = scrape_page(page_url)
    regex_price_per_night = re.compile("[0-9]+ € par nuit")
    divs = list(page_soup.findAll("div"))
    prices_per_night = [re.search(regex_price_per_night, str(d)) for d in divs]
    regex_price_int = re.compile("[0-9]+")
    prices_per_night = np.array([int(re.search(regex_price_int, p.group(0)).group(0)) for p in prices_per_night if p is not None])
    return prices_per_night