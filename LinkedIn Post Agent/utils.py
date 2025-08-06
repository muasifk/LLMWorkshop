

import os
import feedparser
import time

def fetch_latest_news(feeds, max_articles=10):
    """Fetch and aggregate latest headlines with error handling"""
    all_entries = []
    successful_feeds = 0
    
    for feed_url in feeds:
        try:
            print(f"Fetching from: {feed_url}")
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                print(f"Warning: Feed parsing issues for {feed_url}")
            
            # Filter out entries without required fields
            valid_entries = [
                entry for entry in feed.entries 
                if hasattr(entry, 'title') and hasattr(entry, 'summary') and hasattr(entry, 'link')
            ]
            
            all_entries.extend(valid_entries)
            successful_feeds += 1
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            print(f"Error fetching {feed_url}: {str(e)}")
            continue
    
    if successful_feeds == 0:
        raise Exception("Failed to fetch from any RSS feeds")
    
    print(f"Successfully fetched from {successful_feeds}/{len(feeds)} sources")
    
    # Sort by published date, handle missing dates
    def get_published_time(entry):
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            return entry.published_parsed
        return (1970, 1, 1, 0, 0, 0, 0, 0, 0)  # Default to epoch
    
    sorted_entries = sorted(all_entries, key=get_published_time, reverse=True)
    return sorted_entries[:max_articles]
