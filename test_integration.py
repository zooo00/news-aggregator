"""Integration test for highlighting in the full flow"""
from scraper import scrape_all_sites
from app import highlight_keywords, load_keywords, load_apt_keywords

print("Testing full integration...")
print("=" * 80)

# Load keywords
all_keywords = load_keywords()
apt_keywords = load_apt_keywords()
combined = list(set(all_keywords + apt_keywords))

print(f"Loaded {len(all_keywords)} general keywords")
print(f"Loaded {len(apt_keywords)} APT keywords")
print(f"Combined: {len(combined)} unique keywords\n")

# Scrape articles
articles = scrape_all_sites()
print(f"✓ Scraped {len(articles)} articles\n")

# Test highlighting on a few articles
if articles:
    print("Sample highlighted articles:")
    print("=" * 80)

    for i, article in enumerate(articles[:3], 1):
        title_highlighted = highlight_keywords(article.get('title', ''), combined)

        print(f"\n{i}. Original title:")
        print(f"   {article.get('title', '')}")

        print(f"   Highlighted title:")
        print(f"   {title_highlighted}")

        if '<mark class="highlight">' in str(title_highlighted):
            print(f"   ✓ Keywords highlighted!")
        else:
            print(f"   ℹ No keywords found in this title")

print("\n" + "=" * 80)
print("✓ Integration test completed successfully!")
