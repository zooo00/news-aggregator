# Hot-Reload Keywords Feature

The news aggregator now automatically detects changes to `keywords.txt` and reloads them without requiring an app restart.

## How It Works

### File Monitoring
- Tracks the modification time (mtime) of `keywords.txt`
- Compares current mtime with cached mtime on each access
- Automatically reloads if file has been modified

### Caching
- Keywords are cached in memory for performance
- Cache invalidated when file mtime changes
- Separate cache for general keywords and APT keywords

### Performance
- **First access**: Reads from file, caches keywords + mtime
- **Subsequent access**: Returns cached version (no file I/O)
- **After file change**: Detects mtime change, reloads automatically
- **No polling**: Only checks on access, not continuously

## Usage Examples

### Example 1: Add New Keyword

```bash
# While app is running
$ vim keywords.txt

# Add new keyword
zero-click

# Save and exit
:wq

# Next time load_keywords() is called, it automatically reloads!
# This happens on:
# - Next scrape (background every 30 min)
# - Manual refresh (click "Refresh Now")
# - Next article filtering operation
```

### Example 2: Edit APT Groups

```bash
$ vim keywords.txt

# Add new APT group under "# APT Groups"
apt42
kimsuky

# Save
# Changes automatically detected and loaded
```

### Example 3: Bulk Update

```bash
$ cat >> keywords.txt << 'END'
# New section
supply chain attack
software supply chain
third-party breach
END

# Save and immediately available!
```

## Technical Details

### File: `scraper.py`

```python
# Global cache
_keywords_cache = {
    "keywords": None,      # Cached keywords list
    "apt_keywords": None,  # Cached APT keywords list
    "mtime": None          # File modification time
}

def _check_keywords_cache():
    """Check if cache is valid"""
    current_mtime = os.path.getmtime("keywords.txt")
    if _keywords_cache["mtime"] != current_mtime:
        return False  # Cache invalid, need reload
    return True       # Cache valid

def load_keywords():
    """Load keywords with hot-reload"""
    if _check_keywords_cache() and _keywords_cache["keywords"]:
        return _keywords_cache["keywords"]  # Return cached
    
    # Reload from file
    keywords = [...]
    _keywords_cache["keywords"] = keywords
    _keywords_cache["mtime"] = os.path.getmtime("keywords.txt")
    
    print(f"✓ Reloaded {len(keywords)} keywords")
    return keywords
```

### Console Output

When keywords reload, you'll see in the Flask console:

```
✓ Reloaded 200 keywords from keywords.txt
✓ Reloaded 93 APT keywords from keywords.txt
```

## Benefits

### For Development
- Test new keywords without restarting app
- Iterate quickly on keyword list
- No interruption to running scrapes

### For Production
- Update keywords on the fly
- Respond to new threats immediately
- No downtime required

### For Performance
- Cached keywords for fast repeated access
- Only checks mtime, not file contents
- Minimal overhead

## Testing

```python
from scraper import load_keywords
import os, time

# First load
keywords = load_keywords()
# Output: ✓ Reloaded 200 keywords from keywords.txt

# Second load (cached)
keywords = load_keywords()
# Output: (nothing - uses cache)

# Touch file
os.system('touch keywords.txt')
time.sleep(0.1)

# Third load (reloads)
keywords = load_keywords()
# Output: ✓ Reloaded 200 keywords from keywords.txt
```

## Limitations

### Not Real-Time
- Changes detected on next access, not immediately
- If app is idle, keywords won't reload until accessed
- For immediate effect, click "Refresh Now" in UI

### File System Dependent
- Relies on file system mtime accuracy
- Clock skew issues could cause problems
- Most systems handle this correctly

### Single File
- Only monitors `keywords.txt`
- Does not monitor `config.json` (would need restart)
- Does not monitor other configuration files

## Future Enhancements

Possible improvements:
- Watch config.json for source changes
- Web UI for keyword editing
- Reload notification in UI
- Manual reload API endpoint
- File watcher with inotify/FSEvents for instant detection

## Comparison

### Before
```
1. Edit keywords.txt
2. Restart Flask app
3. Wait for app to start
4. Or wait for 30-min refresh cycle
```

### After
```
1. Edit keywords.txt
2. Save
3. Done! (auto-reloads on next access)
```

## Related Files

- `scraper.py` - Hot-reload implementation
- `keywords.txt` - Keywords file being monitored
- `app.py` - Uses hot-reload through scraper functions

## See Also

- `SESSION_LOG.md` - Development history
- `CODE_QUALITY_REPORT.md` - Code analysis
- `README.md` - Main documentation
