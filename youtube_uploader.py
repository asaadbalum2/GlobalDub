#!/usr/bin/env python3
"""
YouTube Upload Module for GlobalDub
Automatically uploads dubbed videos to YouTube
"""

import os
import time
import json
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError


SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
CATEGORY_ENTERTAINMENT = '24'


def get_youtube_client():
    """Create authenticated YouTube client."""
    client_id = os.environ.get('YOUTUBE_CLIENT_ID')
    client_secret = os.environ.get('YOUTUBE_CLIENT_SECRET')
    refresh_token = os.environ.get('YOUTUBE_REFRESH_TOKEN')
    
    if not all([client_id, client_secret, refresh_token]):
        raise ValueError("Missing YouTube credentials")
    
    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES
    )
    
    credentials.refresh(Request())
    return build('youtube', 'v3', credentials=credentials)


LANG_NAMES = {
    'es': 'Spanish', 'pt': 'Portuguese', 'fr': 'French',
    'de': 'German', 'it': 'Italian', 'ja': 'Japanese',
    'ko': 'Korean', 'zh': 'Chinese', 'ar': 'Arabic',
    'hi': 'Hindi', 'ru': 'Russian'
}


def generate_title(original_title: str, lang: str) -> str:
    """Generate title for dubbed video."""
    lang_name = LANG_NAMES.get(lang, lang.upper())
    
    templates = [
        f"[{lang_name} Dub] {original_title}",
        f"{original_title} | {lang_name} Version",
        f"🌍 {original_title} ({lang_name})",
    ]
    
    import random
    title = random.choice(templates)
    return title[:100]


def generate_description(original_url: str, lang: str) -> str:
    """Generate description for dubbed video."""
    lang_name = LANG_NAMES.get(lang, lang.upper())
    
    return f"""🌍 This video has been dubbed into {lang_name}!

Original: {original_url}

Dubbed using AI voice technology.

#shorts #{lang} #dubbed #translated #{lang_name.lower()} #viral

---
🔔 Subscribe for more translated content!
🌐 Bringing content to global audiences
"""


def upload_dubbed_video(
    video_path: str,
    original_url: str,
    lang: str,
    original_title: str = "Viral Short",
    privacy: str = "public"
) -> dict:
    """Upload dubbed video to YouTube."""
    
    youtube = get_youtube_client()
    
    title = generate_title(original_title, lang)
    description = generate_description(original_url, lang)
    
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': ['shorts', 'dubbed', lang, 'translated', 'viral', LANG_NAMES.get(lang, lang)],
            'categoryId': CATEGORY_ENTERTAINMENT,
        },
        'status': {
            'privacyStatus': privacy,
            'selfDeclaredMadeForKids': False,
        }
    }
    
    media = MediaFileUpload(video_path, mimetype='video/mp4', resumable=True)
    
    print(f"📤 Uploading: {title}")
    
    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"   Progress: {int(status.progress() * 100)}%")
    
    video_id = response['id']
    video_url = f"https://youtube.com/shorts/{video_id}"
    
    print(f"✅ Uploaded: {video_url}")
    
    return {'id': video_id, 'url': video_url, 'title': title}


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python youtube_uploader.py <video_path> <original_url> <lang>")
        sys.exit(1)
    
    result = upload_dubbed_video(sys.argv[1], sys.argv[2], sys.argv[3])
    print(json.dumps(result, indent=2))


