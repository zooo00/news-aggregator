from flask import Flask, render_template, jsonify
from markupsafe import Markup
from scraper import scrape_all_sites, parse_timestamp, load_keywords, load_apt_keywords
from datetime import datetime
import threading
import time
from urllib.parse import urlparse
import re

app = Flask(__name__)


def extract_domain(url):
    """Extract domain from URL (e.g., https://www.example.com/path -> example.com)"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        # Remove www. prefix if present
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except:
        return url


def highlight_keywords(text, keywords):
    """Highlight matching keywords in text with HTML"""
    if not text:
        return text

    # Sort keywords by length (longest first) to match longer phrases first
    sorted_keywords = sorted(keywords, key=len, reverse=True)

    # Use placeholders to prevent nested highlighting
    highlighted = text
    placeholder_counter = [0]  # Use list to allow modification in nested function
    replacements = {}

    for keyword in sorted_keywords:
        # Use word boundary at start to avoid matching inside words
        # But allow any suffix (e.g., cyberhot matches cyberhoten, cyberhotet, etc.)
        pattern = re.compile(r"\b(" + re.escape(keyword) + r"\w*)", re.IGNORECASE)

        def replace_with_placeholder(match):
            # Create unique placeholder that won't match any keyword
            placeholder = f"\x00HIGHLIGHT_{placeholder_counter[0]}\x00"
            replacements[placeholder] = (
                f'<mark class="highlight">{match.group(1)}</mark>'
            )
            placeholder_counter[0] += 1
            return placeholder

        highlighted = pattern.sub(replace_with_placeholder, highlighted)

    # Replace all placeholders with actual HTML
    for placeholder, html in replacements.items():
        highlighted = highlighted.replace(placeholder, html)

    return Markup(highlighted)


# Cache for articles
articles_cache = []
last_update = None
update_lock = threading.Lock()


def update_articles():
    """Background task to update articles periodically"""
    global articles_cache, last_update

    while True:
        try:
            print(f"Updating articles at {datetime.now()}")
            new_articles = scrape_all_sites()

            with update_lock:
                articles_cache = new_articles
                last_update = datetime.now()

            print(f"Found {len(new_articles)} articles")
        except Exception as e:
            print(f"Error updating articles: {e}")

        # Wait 30 minutes before next update
        time.sleep(30 * 60)


@app.route("/")
def index():
    """Render the main page"""
    with update_lock:
        articles = articles_cache.copy()
        updated = last_update

    # Load keywords for highlighting
    all_keywords = load_keywords()
    apt_keywords = load_apt_keywords()
    combined_keywords = list(set(all_keywords + apt_keywords))  # Remove duplicates

    # Format timestamps and extract domains for display
    for article in articles:
        if article.get("timestamp"):
            parsed = parse_timestamp(article["timestamp"])
            if parsed != datetime.min:
                article["formatted_timestamp"] = parsed.strftime("%Y-%m-%d %H:%M")
            else:
                article["formatted_timestamp"] = article["timestamp"]
        else:
            article["formatted_timestamp"] = None

        # Extract domain from origin_url
        if article.get("origin_url"):
            article["domain"] = extract_domain(article["origin_url"])

        # Highlight keywords in title and ingress
        article["title_highlighted"] = highlight_keywords(
            article.get("title", ""), combined_keywords
        )
        article["ingress_highlighted"] = highlight_keywords(
            article.get("ingress", ""), combined_keywords
        )
        article["summary_highlighted"] = highlight_keywords(
            article.get("summary", ""), combined_keywords
        )

    # Separate articles by category and APT
    # APT articles appear in both their original category AND the APT tab
    apt_articles = [a for a in articles if a.get("is_apt")]
    swedish_articles = [a for a in articles if a.get("category") == "swedish"]
    international_articles = [
        a for a in articles if a.get("category") == "international"
    ]

    return render_template(
        "index.html",
        swedish_articles=swedish_articles,
        international_articles=international_articles,
        apt_articles=apt_articles,
        last_update=updated,
        total_count=len(articles),
        swedish_count=len(swedish_articles),
        international_count=len(international_articles),
        apt_count=len(apt_articles),
    )


@app.route("/api/articles")
def api_articles():
    """API endpoint to get articles as JSON"""
    with update_lock:
        articles = articles_cache.copy()
        updated = last_update

    return jsonify(
        {
            "articles": articles,
            "last_update": updated.isoformat() if updated else None,
            "count": len(articles),
        }
    )


@app.route("/refresh")
def refresh():
    """Manually trigger a refresh"""
    global articles_cache, last_update

    try:
        new_articles = scrape_all_sites()
        with update_lock:
            articles_cache = new_articles
            last_update = datetime.now()
        return jsonify({"status": "success", "count": len(new_articles)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    # Initial load
    print("Loading initial articles...")
    articles_cache = scrape_all_sites()
    last_update = datetime.now()
    print(f"Loaded {len(articles_cache)} articles")

    # Start background update thread
    update_thread = threading.Thread(target=update_articles, daemon=True)
    update_thread.start()

    # Run Flask app
    app.run(debug=True, host="0.0.0.0", port=4711)
