import json
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import re
from datetime import datetime
from dateutil import parser as date_parser
import xml.etree.ElementTree as ET
import os

# Cache for keywords with file modification time
_keywords_cache = {"keywords": None, "apt_keywords": None, "mtime": None}
_keywords_file = "keywords.txt"


def load_config():
    """Load site configuration from config.json"""
    with open("config.json", "r") as f:
        return json.load(f)


def _check_keywords_cache():
    """Check if keywords cache is valid or needs reload"""
    try:
        current_mtime = os.path.getmtime(_keywords_file)
        if (
            _keywords_cache["mtime"] is None
            or current_mtime != _keywords_cache["mtime"]
        ):
            # File changed, need to reload
            return False
        return True
    except Exception:
        return False


def load_keywords():
    """Load keywords from keywords.txt (with hot-reload on file change)"""
    if _check_keywords_cache() and _keywords_cache["keywords"] is not None:
        return _keywords_cache["keywords"]

    # Reload keywords
    with open(_keywords_file, "r") as f:
        keywords = [
            line.strip().lower()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        ]

    # Update cache
    _keywords_cache["keywords"] = keywords
    _keywords_cache["mtime"] = os.path.getmtime(_keywords_file)

    print(f"✓ Reloaded {len(keywords)} keywords from {_keywords_file}")
    return keywords


def load_apt_keywords():
    """Load APT-specific keywords from keywords.txt (with hot-reload on file change)"""
    if _check_keywords_cache() and _keywords_cache["apt_keywords"] is not None:
        return _keywords_cache["apt_keywords"]

    # Reload APT keywords
    with open(_keywords_file, "r") as f:
        lines = f.readlines()
        apt_section = False
        apt_keywords = []
        for line in lines:
            line = line.strip()
            if line.startswith("# APT Groups"):
                apt_section = True
                continue
            if apt_section:
                if line.startswith("#") and "APT" not in line:
                    break
                if line and not line.startswith("#"):
                    apt_keywords.append(line.lower())

    # Update cache
    _keywords_cache["apt_keywords"] = apt_keywords
    _keywords_cache["mtime"] = os.path.getmtime(_keywords_file)

    print(f"✓ Reloaded {len(apt_keywords)} APT keywords from {_keywords_file}")
    return apt_keywords


def match_keywords(text: str, keywords: List[str]) -> bool:
    """Check if text contains any of the keywords (with word boundary at start, allows suffixes)"""
    text_lower = text.lower()
    for keyword in keywords:
        # Use word boundary at start to avoid matching inside words
        # But allow any suffix (e.g., cyberhot matches cyberhoten, cyberhoten, etc.)
        pattern = r"\b" + re.escape(keyword.lower())
        if re.search(pattern, text_lower):
            return True
    return False


def detect_swedish_reference(text: str) -> bool:
    """Detect if article mentions Swedish references (companies, cities, country)"""
    text_lower = text.lower()

    # Swedish indicators
    swedish_keywords = [
        # Country names
        "sweden", "sverige", "swedish",
        # Major cities
        "stockholm", "göteborg", "gothenburg", "malmö", "malmo", "uppsala", "västerås", "vasteras",
        "örebro", "orebro", "linköping", "linkoping", "helsingborg", "jönköping", "jonkoping",
        "norrköping", "norrkoping", "lund", "umeå", "umea", "gävle", "gavle", "borås", "boras",
        # Swedish domains
        ".se",
        # Common Swedish companies/organizations
        "volvo", "ericsson", "ikea", "h&m", "spotify", "klarna", "skanska", "sca", "astrazeneca",
        "nordea", "seb bank", "swedbank", "handelsbanken", "telia", "telenor", "scania",
        # Government/Organizations
        "swedish government", "regeringen", "försvarsmakten", "forsvaret", "polisen",
        "msb", "cert-se", "säpo", "sapo", "försäkringskassan", "forsakringskassan",
        "skatteverket", "arbetsförmedlingen", "arbetsformedlingen",
    ]

    for keyword in swedish_keywords:
        pattern = r"\b" + re.escape(keyword.lower())
        if re.search(pattern, text_lower):
            return True

    return False


def generate_summary(text: str, max_length: int = 150) -> str:
    """Generate a short summary from text"""
    text = text.strip()
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(" ", 1)[0] + "..."


def fetch_article_ingress(url: str, ingress_selector: str) -> str:
    """Fetch the ingress/lead paragraph from an article page"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        ingress_elem = soup.select_one(ingress_selector)

        if ingress_elem:
            ingress_text = ingress_elem.get_text(strip=True)
            # Clean up the text
            ingress_text = re.sub(r"\s+", " ", ingress_text)
            return ingress_text
        return ""
    except Exception as e:
        print(f"Error fetching ingress from {url}: {e}")
        return ""


def scrape_rss_feed(site_config: Dict) -> List[Dict]:
    """Scrape a single news site via RSS feed"""
    articles = []

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(site_config["rss_url"], headers=headers, timeout=10)
        response.raise_for_status()

        # Parse RSS feed
        root = ET.fromstring(response.content)

        # Handle both RSS and Atom feeds
        # RSS uses <item> elements, Atom uses <entry>
        items = list(
            root.findall(".//item")
            or root.findall(".//{http://www.w3.org/2005/Atom}entry")
        )

        for item in items[:50]:  # Limit to 50 articles per site
            try:
                # Extract title - use direct iteration to avoid XML namespace issues
                title = None
                for child in item:
                    if (
                        child.tag == "title"
                        or child.tag == "{http://www.w3.org/2005/Atom}title"
                    ):
                        title = "".join(child.itertext()).strip()
                        break

                # Extract link
                link = None
                for child in item:
                    if (
                        child.tag == "link"
                        or child.tag == "{http://www.w3.org/2005/Atom}link"
                    ):
                        if child.text:
                            link = child.text.strip()
                        else:
                            link = child.get("href", "").strip()
                        break

                # Extract description/summary for ingress
                description = None
                for child in item:
                    if child.tag in [
                        "description",
                        "{http://purl.org/rss/1.0/modules/content/}encoded",
                        "{http://www.w3.org/2005/Atom}summary",
                        "{http://www.w3.org/2005/Atom}content",
                    ]:
                        desc_text = "".join(child.itertext())
                        if desc_text and desc_text.strip():
                            # Strip HTML tags from description
                            # Only parse if it contains HTML-like content
                            if "<" in desc_text and ">" in desc_text:
                                description = BeautifulSoup(
                                    desc_text, "html.parser"
                                ).get_text(strip=True)
                            else:
                                description = desc_text.strip()
                            # Limit length
                            if len(description) > 300:
                                description = (
                                    description[:300].rsplit(" ", 1)[0] + "..."
                                )
                        break

                # Extract timestamp - use direct iteration like title/link
                timestamp = None
                for child in item:
                    if child.tag in [
                        "pubDate",
                        "{http://purl.org/dc/elements/1.1/}date",
                        "{http://www.w3.org/2005/Atom}published",
                        "{http://www.w3.org/2005/Atom}updated",
                    ]:
                        timestamp = "".join(child.itertext()).strip()
                        break

                if title and link:
                    articles.append(
                        {
                            "title": title,
                            "link": link,
                            "origin": site_config["name"],
                            "origin_url": site_config["url"],
                            "timestamp": timestamp,
                            "category": site_config.get("category", "international"),
                            "ingress": description or "",
                            "ingress_selector": "",  # Not needed for RSS
                        }
                    )
            except Exception as e:
                print(f"Error parsing RSS item from {site_config['name']}: {e}")
                continue

    except Exception as e:
        print(f"Error scraping RSS feed {site_config['name']}: {e}")

    return articles


def scrape_site(site_config: Dict) -> List[Dict]:
    """Scrape a single news site based on configuration"""
    # If RSS feed URL is provided, use RSS scraping instead
    if "rss_url" in site_config and site_config["rss_url"]:
        return scrape_rss_feed(site_config)

    # Otherwise fall back to HTML scraping
    articles = []

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(site_config["url"], headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        selectors = site_config["selectors"]

        article_elements = soup.select(selectors["articles"])

        for article_elem in article_elements[:50]:  # Limit to 50 articles per site
            try:
                title_elem = article_elem.select_one(selectors["title"])
                link_elem = article_elem.select_one(selectors["link"])

                if title_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    link = link_elem.get("href", "")

                    # Make relative URLs absolute
                    if link and not link.startswith("http"):
                        from urllib.parse import urljoin

                        link = urljoin(site_config["url"], link)

                    # Extract timestamp if available
                    timestamp = None
                    if "timestamp" in selectors:
                        timestamp_elem = article_elem.select_one(selectors["timestamp"])
                        if timestamp_elem:
                            # Try to get datetime attribute first, then text
                            timestamp = timestamp_elem.get(
                                "datetime"
                            ) or timestamp_elem.get_text(strip=True)

                    # Store ingress selector for later use
                    ingress_selector = selectors.get("ingress", "")

                    articles.append(
                        {
                            "title": title,
                            "link": link,
                            "origin": site_config["name"],
                            "origin_url": site_config["url"],
                            "timestamp": timestamp,
                            "category": site_config.get("category", "international"),
                            "ingress_selector": ingress_selector,
                        }
                    )
            except Exception as e:
                continue

    except Exception as e:
        print(f"Error scraping {site_config['name']}: {e}")

    return articles


def parse_timestamp(timestamp_str: str) -> datetime:
    """Try to parse a timestamp string into a datetime object"""
    if not timestamp_str:
        return datetime.min

    try:
        # Try parsing ISO format or common date formats
        parsed = date_parser.parse(timestamp_str)
        # Remove timezone info to make all datetimes naive for comparison
        if parsed.tzinfo is not None:
            parsed = parsed.replace(tzinfo=None)
        return parsed
    except:
        # If parsing fails, return minimum date so it goes to the end
        return datetime.min


def scrape_all_sites() -> List[Dict]:
    """Scrape all configured sites and filter by keywords"""
    config = load_config()
    keywords = load_keywords()
    apt_keywords = load_apt_keywords()
    all_articles = []

    for site in config["sites"]:
        articles = scrape_site(site)
        all_articles.extend(articles)

    # Filter by keywords
    filtered_articles = []
    for article in all_articles:
        # Check both title and ingress for keyword matches
        article_text = article["title"] + " " + article.get("ingress", "")

        if match_keywords(article_text, keywords):
            # If ingress not already set (from RSS), fetch from article page
            if not article.get("ingress"):
                if article.get("ingress_selector") and article.get("link"):
                    article["ingress"] = fetch_article_ingress(
                        article["link"], article["ingress_selector"]
                    )
                else:
                    article["ingress"] = ""

            # Set summary fallback
            article["summary"] = (
                article["ingress"]
                if article["ingress"]
                else generate_summary(article["title"])
            )

            # Check if article is APT-related
            article_text = (article["title"] + " " + article.get("ingress", "")).lower()
            if match_keywords(article_text, apt_keywords):
                article["is_apt"] = True

            # Check for Swedish references (for ransomware.live and similar APT sources)
            if detect_swedish_reference(article["title"] + " " + article.get("ingress", "")):
                article["is_swedish_reference"] = True

            filtered_articles.append(article)

    # Sort by timestamp, newest first
    filtered_articles.sort(
        key=lambda x: parse_timestamp(x.get("timestamp", "")), reverse=True
    )

    return filtered_articles
