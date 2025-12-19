#!/usr/bin/env python3
"""
Trending Video Fetcher for GlobalDub
Automatically finds popular YouTube Shorts to dub
"""

import os
import json
import random
import requests
from datetime import datetime
from typing import List, Optional


# Categories to search for trending shorts
TRENDING_SEARCHES = [
    "viral shorts today",
    "trending shorts 2024",
    "funny shorts viral",
    "satisfying shorts",
    "life hacks shorts",
    "facts you didn't know shorts",
    "amazing shorts",
    "motivational shorts",
    "cooking shorts viral",
    "pet shorts funny",
]


def get_trending_shorts_from_rss() -> List[str]:
    """
    Get trending shorts from YouTube RSS feeds.
    This is a free method that doesn't require API quota.
    """
    urls = []
    
    # Popular channels that post shorts
    channel_feeds = [
        # Add RSS feeds of channels with viral shorts
        # Format: https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID
    ]
    
    # For now, return curated list of viral short patterns
    # In production, this would scrape or use API
    return urls


def get_shorts_from_search(query: str, max_results: int = 5) -> List[dict]:
    """
    Search for shorts using a free method.
    Uses yt-dlp's search functionality.
    """
    import subprocess
    
    try:
        # Use yt-dlp to search (free, no API needed)
        cmd = [
            "yt-dlp",
            f"ytsearch{max_results}:{query}",
            "--get-id",
            "--get-title",
            "--no-download",
            "--flat-playlist",
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            shorts = []
            
            # Parse pairs of title + id
            for i in range(0, len(lines) - 1, 2):
                if i + 1 < len(lines):
                    title = lines[i]
                    video_id = lines[i + 1]
                    
                    # Only include if it looks like a short (title patterns)
                    if len(video_id) == 11:  # Valid YouTube ID length
                        shorts.append({
                            'id': video_id,
                            'title': title,
                            'url': f"https://youtube.com/shorts/{video_id}"
                        })
            
            return shorts
            
    except Exception as e:
        print(f"Search failed: {e}")
    
    return []


def fetch_trending_to_dub(count: int = 5) -> List[str]:
    """
    Fetch trending shorts URLs to dub.
    Returns list of YouTube URLs.
    """
    print("🔍 Fetching trending shorts to dub...")
    
    all_shorts = []
    
    # Search multiple queries
    queries = random.sample(TRENDING_SEARCHES, min(3, len(TRENDING_SEARCHES)))
    
    for query in queries:
        print(f"   Searching: {query}")
        shorts = get_shorts_from_search(query, max_results=5)
        all_shorts.extend(shorts)
    
    # Remove duplicates
    seen = set()
    unique_shorts = []
    for short in all_shorts:
        if short['id'] not in seen:
            seen.add(short['id'])
            unique_shorts.append(short)
    
    # Shuffle and take requested count
    random.shuffle(unique_shorts)
    selected = unique_shorts[:count]
    
    print(f"\n✅ Found {len(selected)} shorts to dub:")
    for s in selected:
        print(f"   • {s['title'][:50]}...")
    
    return [s['url'] for s in selected]


def save_urls_for_processing(urls: List[str], output_file: str = "urls_to_dub.txt"):
    """Save URLs to a file for batch processing."""
    with open(output_file, 'w') as f:
        f.write(f"# Auto-fetched trending shorts - {datetime.now().isoformat()}\n")
        for url in urls:
            f.write(f"{url}\n")
    
    print(f"📁 Saved {len(urls)} URLs to {output_file}")
    return output_file


if __name__ == "__main__":
    import sys
    
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    
    urls = fetch_trending_to_dub(count)
    
    if urls:
        save_urls_for_processing(urls)
        print("\n🚀 Ready to dub! Run:")
        print(f"   python dub.py --batch urls_to_dub.txt --lang es")



