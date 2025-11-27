# News Feed Aggregator

A cybersecurity news aggregator that monitors Swedish and international sources for security-related articles. Built with Flask and featuring intelligent keyword filtering, RSS feed parsing, and a modern dark mode interface.

## Features

- **Multi-Source Aggregation**: Monitors 12 news sources (8 Swedish, 4 International)
- **Intelligent Filtering**: 292 keywords including 93 APT group names
- **Swedish Language Support**: Handles Swedish grammar with suffix matching (cyberhot → cyberhoten, cyberhotet)
- **Smart Highlighting**: Subtle keyword highlighting in articles
- **APT Detection**: Automatic categorization of APT-related articles
- **Article Persistence**: Tracks read/unread articles with localStorage
- **Auto-Refresh**: Background updates every 30 minutes, checks for new content every 5 minutes
- **Dark Mode**: Persistent theme preference across sessions
- **Clean UI**: Modern, emoji-free interface with tab navigation

## Sources

### Swedish
- CERT-SE (35% match rate)
- Computer Sweden (10% match rate)
- Ny Teknik (2% match rate)
- MSB (Myndigheten för samhällsskydd och beredskap)
- Dagens Industri
- Dagens Nyheter
- SVT Nyheter
- TV4 Nyheter

### International
- Krebs on Security
- Bleeping Computer
- The Register
- IDG (Computer Sweden)

## Requirements

- Python 3.8+
- Flask 3.0+
- See `requirements.txt` for full dependencies

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/news-aggregator.git
cd news-aggregator

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The application will be available at `http://localhost:4711`

## Configuration

### Adding New Sources

Edit `config.json` to add new RSS feeds:

```json
{
  "name": "Source Name",
  "url": "https://example.com/",
  "category": "swedish",
  "rss_url": "https://example.com/rss",
  "selectors": {
    "articles": "article",
    "title": "h2",
    "link": "a",
    "timestamp": "time",
    "ingress": "p.lead"
  }
}
```

### Customizing Keywords

Edit `keywords.txt` to add or modify keywords:

```
# Swedish Keywords
cybersäkerhet
dataintrång
säkerhetshål

# International Keywords
ransomware
data breach
zero-day
```

## API Endpoints

- `GET /` - Main web interface
- `GET /api/articles` - JSON API returning all filtered articles
- `GET /refresh` - Manually trigger article refresh

## Architecture

```
scraper/
├── app.py              # Flask application and routes
├── scraper.py          # RSS scraping and filtering logic
├── config.json         # News source configuration
├── keywords.txt        # Keyword list for filtering
├── templates/
│   └── index.html      # Web interface template
├── test_suite.py       # Unit tests
└── requirements.txt    # Python dependencies
```

## Key Features Explained

### Swedish Suffix Matching

The keyword matcher supports Swedish grammar:
- `cyberhot` matches: cyberhot, cyberhoten, cyberhotet, cyberhots
- `ransomware` matches: ransomware, ransomwareattack, ransomwareattacker
- Still prevents false positives: `mask` won't match inside `pengamaskin`

### Article Persistence

Articles are tracked in browser localStorage:
- New articles show "NEW" badge with green border
- Tab badges display new article count
- "Mark All as Seen" button to clear indicators
- Visual divider between new and seen articles

### Smart Filtering

Articles are filtered based on keywords in both:
- Article titles
- Article ingress/summary text

This catches ~34% more relevant articles than title-only filtering.

## Testing

```bash
# Run unit tests
python -m pytest test_suite.py -v

# Run code formatting
python -m black app.py scraper.py

# Run security scan
python -m bandit -r app.py scraper.py
```

All 18 tests pass with 100% success rate.

## Development

### Code Quality

- **Formatted**: Black (PEP 8 compliant)
- **Tested**: 18 unit tests, 100% passing
- **Documented**: Comprehensive docstrings and comments

### Security Notes

⚠️ **Before Production:**
1. Disable debug mode: `app.run(debug=False)`
2. Change host binding: `host="127.0.0.1"`
3. Install defusedxml: `pip install defusedxml`
4. Update XML parsing in scraper.py

See `CODE_QUALITY_REPORT.md` for detailed security analysis.

## Performance

- Initial load: ~5-10 seconds (scraping 12 sites)
- Articles per scrape: ~47 average
- Background refresh: Every 30 minutes
- Frontend auto-check: Every 5 minutes
- Test suite execution: 0.15 seconds

## Statistics

- **Total Keywords**: 292 (199 general + 93 APT)
- **Average Articles**: 47 per scrape
- **Match Rate**: 8-12% overall
- **Best Sources**: CERT-SE (35%), Computer Sweden (10%)

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Follow Black formatting
4. Add tests for new features
5. Submit a pull request

## License

MIT License

## Session Logs

See `SESSION_LOG.md` for detailed development history and all changes made during development sessions.

## Code Quality

See `CODE_QUALITY_REPORT.md` for comprehensive code analysis, security findings, and recommendations.

## Author

Created with Claude Code

## Acknowledgments

- RSS feeds provided by respective news organizations
- Built with Flask web framework
- Testing with pytest
- Code formatting with Black
