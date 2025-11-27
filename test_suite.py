"""Comprehensive test suite for the news aggregator"""

import unittest
from unittest.mock import patch, Mock
from scraper import (
    load_keywords,
    load_apt_keywords,
    parse_timestamp,
    match_keywords,
    scrape_rss_feed,
)
from app import extract_domain, highlight_keywords
from datetime import datetime


class TestKeywordLoading(unittest.TestCase):
    """Test keyword loading functionality"""

    def test_load_keywords(self):
        """Test that keywords are loaded correctly"""
        keywords = load_keywords()
        self.assertIsInstance(keywords, list)
        self.assertGreater(len(keywords), 0)
        # Check that comments are filtered out
        self.assertNotIn("#", "".join(keywords))

    def test_load_apt_keywords(self):
        """Test that APT keywords are loaded correctly"""
        apt_keywords = load_apt_keywords()
        self.assertIsInstance(apt_keywords, list)
        self.assertGreater(len(apt_keywords), 0)
        # Check for known APT groups
        self.assertTrue(
            any("apt" in k.lower() for k in apt_keywords)
            or any("lazarus" in k.lower() for k in apt_keywords)
        )


class TestTimestampParsing(unittest.TestCase):
    """Test timestamp parsing functionality"""

    def test_parse_rfc822_timestamp(self):
        """Test RFC 822 timestamp parsing"""
        timestamp = "Mon, 27 Nov 2025 10:30:00 GMT"
        result = parse_timestamp(timestamp)
        self.assertNotEqual(result, datetime.min)
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 11)

    def test_parse_iso_timestamp(self):
        """Test ISO 8601 timestamp parsing"""
        timestamp = "2025-11-27T10:30:00Z"
        result = parse_timestamp(timestamp)
        self.assertNotEqual(result, datetime.min)

    def test_parse_invalid_timestamp(self):
        """Test invalid timestamp returns datetime.min"""
        timestamp = "invalid timestamp"
        result = parse_timestamp(timestamp)
        self.assertEqual(result, datetime.min)


class TestKeywordMatching(unittest.TestCase):
    """Test keyword matching functionality"""

    def test_match_keywords_positive(self):
        """Test that matching keywords are detected"""
        text = "This is a ransomware attack"
        keywords = ["ransomware", "malware"]
        self.assertTrue(match_keywords(text, keywords))

    def test_match_keywords_negative(self):
        """Test that non-matching text returns False"""
        text = "This is a normal article"
        keywords = ["ransomware", "malware"]
        self.assertFalse(match_keywords(text, keywords))

    def test_match_keywords_case_insensitive(self):
        """Test that matching is case-insensitive"""
        text = "This is a RANSOMWARE attack"
        keywords = ["ransomware"]
        self.assertTrue(match_keywords(text, keywords))


class TestDomainExtraction(unittest.TestCase):
    """Test domain extraction functionality"""

    def test_extract_domain_basic(self):
        """Test basic domain extraction"""
        url = "https://www.example.com/path/to/page"
        result = extract_domain(url)
        self.assertEqual(result, "example.com")

    def test_extract_domain_no_www(self):
        """Test domain extraction without www"""
        url = "https://example.com/page"
        result = extract_domain(url)
        self.assertEqual(result, "example.com")

    def test_extract_domain_with_subdomain(self):
        """Test domain extraction with subdomain"""
        url = "https://news.example.com/article"
        result = extract_domain(url)
        self.assertEqual(result, "news.example.com")


class TestHighlighting(unittest.TestCase):
    """Test keyword highlighting functionality"""

    def test_highlight_single_keyword(self):
        """Test highlighting a single keyword"""
        text = "This article mentions ransomware"
        keywords = ["ransomware"]
        result = highlight_keywords(text, keywords)
        self.assertIn('<mark class="highlight">', str(result))
        self.assertIn("ransomware", str(result))

    def test_highlight_multiple_keywords(self):
        """Test highlighting multiple keywords"""
        text = "This article mentions ransomware and malware"
        keywords = ["ransomware", "malware"]
        result = highlight_keywords(text, keywords)
        self.assertEqual(str(result).count('<mark class="highlight">'), 2)

    def test_highlight_case_insensitive(self):
        """Test case-insensitive highlighting"""
        text = "This article mentions RANSOMWARE"
        keywords = ["ransomware"]
        result = highlight_keywords(text, keywords)
        self.assertIn('<mark class="highlight">', str(result))

    def test_highlight_word_boundaries(self):
        """Test that highlighting respects word boundaries"""
        text = "This is not a pengamaskin"
        keywords = ["mask"]
        result = highlight_keywords(text, keywords)
        # Should not highlight 'mask' inside 'maskin'
        self.assertNotIn('<mark class="highlight">mask</mark>in', str(result))

    def test_highlight_empty_text(self):
        """Test highlighting with empty text"""
        text = ""
        keywords = ["ransomware"]
        result = highlight_keywords(text, keywords)
        self.assertEqual(str(result), "")

    def test_highlight_no_nested_marks(self):
        """Test that highlighting doesn't create nested marks"""
        text = "data breach"
        keywords = ["data breach", "breach"]
        result = highlight_keywords(text, keywords)
        # Should not have nested <mark> tags
        self.assertNotIn("<mark><mark>", str(result))


class TestRSSFeed(unittest.TestCase):
    """Test RSS feed scraping"""

    @patch("scraper.requests.get")
    def test_scrape_rss_feed_success(self, mock_get):
        """Test successful RSS feed scraping"""
        # Mock RSS response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <item>
            <title>Test Article</title>
            <link>https://example.com/article</link>
            <description>Test description</description>
            <pubDate>Mon, 27 Nov 2025 10:30:00 GMT</pubDate>
        </item>
    </channel>
</rss>"""
        mock_get.return_value = mock_response

        site_config = {
            "name": "Test Site",
            "url": "https://example.com",
            "rss_url": "https://example.com/rss",
            "category": "international",
        }

        articles = scrape_rss_feed(site_config)
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["title"], "Test Article")
        self.assertEqual(articles[0]["link"], "https://example.com/article")


if __name__ == "__main__":
    unittest.main(verbosity=2)
