# Persistency Feature Test Guide

## Features Implemented

1. **localStorage Tracking**: Tracks which articles you've seen across browser sessions
2. **Auto-refresh**: Checks every 5 minutes for new articles and reloads if found
3. **Visual Indicators**:
   - New articles have a green left border and "NEW" badge
   - Tab badges show count of new articles (e.g., "2 new")
   - Divider line between new and previously seen articles
4. **Mark All as Seen**: Button to manually mark all current articles as seen

## How to Test

1. **First Load**:
   - Open http://localhost:4711
   - All articles will be marked as NEW (green border, NEW badge)
   - Each tab will show "X new" count
   - Click "Mark All as Seen" to clear the new indicators

2. **Second Load**:
   - Refresh the page or come back later
   - Previously seen articles won't have NEW indicators
   - Only genuinely new articles will be highlighted

3. **Auto-refresh**:
   - Wait for the background scraper to find new articles (or use "Refresh Now")
   - The page will automatically reload every 5 minutes to check for new content
   - When new articles are detected, page auto-reloads

4. **Divider**:
   - When you have both new and old articles, a divider line appears
   - Says "Previously seen" between the sections

## Technical Details

- Uses browser localStorage (key: 'seenArticles')
- Stores article URLs to track what you've seen
- Checks /api/articles endpoint every 5 minutes
- Auto-reloads only when genuinely new articles are found
