#!/usr/bin/env python3
"""
GlobalDub - Automated Translation & Dubbing Pipeline for YouTube Shorts
Zero-Cost Stack: yt-dlp + whisper + deep-translator + edge-tts + moviepy

Transforms English YouTube Shorts into Spanish (or other languages) with voiceover dubbing.
"""

import argparse
import asyncio
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import edge_tts
from deep_translator import GoogleTranslator
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
from pydub import AudioSegment

# Try to import whisper (will be installed separately)
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("⚠️ Warning: openai-whisper not installed. Install with: pip install openai-whisper")


# ============ CONFIGURATION ============
OUTPUT_DIR = Path("./output")
TEMP_DIR = Path("./temp")

# Whisper settings
WHISPER_MODEL = "base"  # Options: tiny, base, small, medium, large (base is good for CPU)

# Translation settings
SOURCE_LANG = "en"
TARGET_LANG = "es"  # Spanish (Mexico)

# TTS Voice mapping by language
VOICE_MAP = {
    "es": "es-MX-DaliaNeural",      # Spanish (Mexico) - Female
    "es-f": "es-MX-DaliaNeural",    # Spanish Female
    "es-m": "es-MX-JorgeNeural",    # Spanish Male
    "pt": "pt-BR-FranciscaNeural",  # Portuguese (Brazil)
    "fr": "fr-FR-DeniseNeural",     # French
    "de": "de-DE-KatjaNeural",      # German
    "it": "it-IT-ElsaNeural",       # Italian
    "ja": "ja-JP-NanamiNeural",     # Japanese
    "ko": "ko-KR-SunHiNeural",      # Korean
    "zh": "zh-CN-XiaoxiaoNeural",   # Chinese (Mandarin)
    "ar": "ar-SA-ZariyahNeural",    # Arabic
    "hi": "hi-IN-SwaraNeural",      # Hindi
    "ru": "ru-RU-SvetlanaNeural",   # Russian
}

# Audio settings
ORIGINAL_AUDIO_VOLUME = 0.1  # 10% - keeps background music/sfx faint
MAX_SPEED_FACTOR = 1.25      # Maximum speedup for translated audio


def ensure_directories():
    """Create necessary directories."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    TEMP_DIR.mkdir(exist_ok=True)


def check_dependencies():
    """Check if required external tools are installed."""
    required = ["ffmpeg", "yt-dlp"]
    missing = []
    
    for tool in required:
        if shutil.which(tool) is None:
            missing.append(tool)
    
    if missing:
        print("❌ Missing required tools:")
        for tool in missing:
            print(f"   - {tool}")
        print("\n📦 Installation:")
        print("   FFmpeg: sudo apt install ffmpeg (Linux) | winget install ffmpeg (Windows)")
        print("   yt-dlp: pip install yt-dlp")
        sys.exit(1)
    
    if not WHISPER_AVAILABLE:
        print("❌ Missing openai-whisper. Install with:")
        print("   pip install openai-whisper")
        sys.exit(1)
    
    print("✅ All dependencies found!")


def download_video(url: str) -> Tuple[str, str]:
    """
    Download video from YouTube using yt-dlp.
    Returns tuple of (video_path, audio_path).
    """
    print(f"\n📥 Downloading video from: {url}")
    
    video_path = str(TEMP_DIR / "source_video.mp4")
    audio_path = str(TEMP_DIR / "source_audio.wav")
    
    # Download video
    video_cmd = [
        "yt-dlp",
        "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", video_path,
        "--no-playlist",
        "--socket-timeout", "30",
        "--retries", "3",
        url
    ]
    
    try:
        subprocess.run(video_cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error downloading video: {e.stderr}")
        raise
    
    print("✅ Video downloaded!")
    
    # Extract audio as WAV for Whisper
    print("🎵 Extracting audio...")
    audio_cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",  # No video
        "-acodec", "pcm_s16le",
        "-ar", "16000",  # 16kHz for Whisper
        "-ac", "1",  # Mono
        audio_path
    ]
    
    subprocess.run(audio_cmd, check=True, capture_output=True)
    print("✅ Audio extracted!")
    
    return video_path, audio_path


def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe audio using Whisper.
    Uses the 'base' model for CPU efficiency.
    """
    print(f"\n📝 Transcribing audio with Whisper ({WHISPER_MODEL} model)...")
    print("   (This may take a moment on CPU)")
    
    # Load model
    model = whisper.load_model(WHISPER_MODEL)
    
    # Transcribe
    result = model.transcribe(
        audio_path,
        language="en",
        task="transcribe",
        fp16=False  # Use fp32 for CPU
    )
    
    text = result["text"].strip()
    
    print(f"✅ Transcription complete!")
    print(f"   Length: {len(text)} characters")
    print(f"   Preview: {text[:100]}..." if len(text) > 100 else f"   Text: {text}")
    
    return text


def translate_text(text: str, target_lang: str = TARGET_LANG) -> str:
    """
    Translate text using Google Translate (via deep-translator).
    Chunks text to handle length limits.
    """
    print(f"\n🌍 Translating to {target_lang}...")
    
    translator = GoogleTranslator(source='auto', target=target_lang)
    
    # Google Translate has a 5000 char limit per request
    max_chunk_size = 4500
    
    if len(text) <= max_chunk_size:
        translated = translator.translate(text)
    else:
        # Split into sentences and chunk
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < max_chunk_size:
                current_chunk += " " + sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Translate each chunk
        translated_chunks = []
        for i, chunk in enumerate(chunks):
            print(f"   Translating chunk {i+1}/{len(chunks)}...")
            try:
                translated_chunk = translator.translate(chunk)
                translated_chunks.append(translated_chunk)
            except Exception as e:
                print(f"   ⚠️ Error translating chunk: {e}")
                translated_chunks.append(chunk)  # Keep original if translation fails
        
        translated = " ".join(translated_chunks)
    
    print(f"✅ Translation complete!")
    print(f"   Preview: {translated[:100]}..." if len(translated) > 100 else f"   Text: {translated}")
    
    return translated


async def generate_tts(text: str, output_path: str, lang: str = TARGET_LANG) -> float:
    """
    Generate speech using Edge-TTS.
    Returns the duration of the generated audio.
    """
    print(f"\n🎤 Generating speech ({lang})...")
    
    # Get voice for language
    voice = VOICE_MAP.get(lang, VOICE_MAP.get(lang[:2], "es-MX-DaliaNeural"))
    
    print(f"   Using voice: {voice}")
    
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
    
    # Get duration
    audio = AudioSegment.from_mp3(output_path)
    duration = len(audio) / 1000.0  # Convert ms to seconds
    
    print(f"✅ Speech generated! Duration: {duration:.1f}s")
    
    return duration


def adjust_audio_speed(audio_path: str, speed_factor: float, output_path: str):
    """
    Adjust audio speed using ffmpeg.
    """
    if speed_factor == 1.0:
        shutil.copy(audio_path, output_path)
        return
    
    print(f"   ⏩ Adjusting speed by {speed_factor:.2f}x...")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", audio_path,
        "-filter:a", f"atempo={speed_factor}",
        "-vn",
        output_path
    ]
    
    subprocess.run(cmd, check=True, capture_output=True)


def mix_audio(
    original_video_path: str,
    dubbed_audio_path: str,
    output_path: str,
    original_volume: float = ORIGINAL_AUDIO_VOLUME,
    video_duration: Optional[float] = None
) -> str:
    """
    Mix dubbed audio with original video.
    Ducks original audio to specified volume.
    """
    print("\n🎛️ Mixing audio tracks...")
    
    # Load video to get duration
    video = VideoFileClip(original_video_path)
    if video_duration is None:
        video_duration = video.duration
    
    # Load original audio and reduce volume
    original_audio = video.audio
    if original_audio is not None:
        original_audio = original_audio.volumex(original_volume)
    
    # Load dubbed audio
    dubbed_audio = AudioFileClip(dubbed_audio_path)
    
    # Check if dubbed audio is longer than video
    dubbed_duration = dubbed_audio.duration
    
    if dubbed_duration > video_duration:
        # Speed up dubbed audio to fit (within limits)
        speed_needed = dubbed_duration / video_duration
        
        if speed_needed <= MAX_SPEED_FACTOR:
            print(f"   ⏩ Dubbed audio is {speed_needed:.2f}x longer. Speeding up...")
            
            temp_adjusted = str(TEMP_DIR / "adjusted_dub.mp3")
            adjust_audio_speed(dubbed_audio_path, speed_needed, temp_adjusted)
            
            dubbed_audio.close()
            dubbed_audio = AudioFileClip(temp_adjusted)
        else:
            print(f"   ⚠️ Dubbed audio is too long ({speed_needed:.2f}x). Trimming to fit.")
            dubbed_audio = dubbed_audio.subclip(0, video_duration)
    
    # Create composite audio
    if original_audio is not None:
        final_audio = CompositeAudioClip([original_audio, dubbed_audio])
    else:
        final_audio = dubbed_audio
    
    # Set audio on video
    final_video = video.set_audio(final_audio)
    
    # Render
    print("🎬 Rendering final video...")
    final_video.write_videofile(
        output_path,
        codec='libx264',
        audio_codec='aac',
        preset='ultrafast',
        threads=4,
        logger=None
    )
    
    # Cleanup
    video.close()
    dubbed_audio.close()
    
    print(f"✅ Final video saved: {output_path}")
    
    return output_path


def cleanup_temp():
    """Remove temporary files."""
    if TEMP_DIR.exists():
        for file in TEMP_DIR.iterdir():
            try:
                file.unlink()
            except Exception:
                pass


async def process_video(
    url: str,
    target_lang: str = TARGET_LANG,
    output_name: Optional[str] = None,
    keep_temp: bool = False
) -> str:
    """
    Full pipeline: Download → Transcribe → Translate → Dub → Mix
    """
    print("\n" + "="*60)
    print("🌍 GlobalDub - Video Translation Pipeline")
    print("="*60)
    
    ensure_directories()
    
    try:
        # Step 1: Download
        video_path, audio_path = download_video(url)
        
        # Step 2: Transcribe
        transcript = transcribe_audio(audio_path)
        
        # Step 3: Translate
        translated = translate_text(transcript, target_lang)
        
        # Step 4: Generate TTS
        tts_path = str(TEMP_DIR / "dubbed_audio.mp3")
        await generate_tts(translated, tts_path, target_lang)
        
        # Step 5: Mix and render
        if output_name is None:
            # Generate name from URL
            video_id = url.split("/")[-1].split("?")[0]
            if "v=" in url:
                video_id = url.split("v=")[1].split("&")[0]
            output_name = f"dubbed_{video_id}_{target_lang}.mp4"
        
        output_path = str(OUTPUT_DIR / output_name)
        mix_audio(video_path, tts_path, output_path)
        
        print("\n" + "="*60)
        print("✅ DUBBING COMPLETE!")
        print(f"📁 Output: {output_path}")
        print("="*60 + "\n")
        
        return output_path
        
    finally:
        if not keep_temp:
            cleanup_temp()


async def batch_process(urls_file: str, target_lang: str = TARGET_LANG):
    """
    Process multiple videos from a file (one URL per line).
    """
    with open(urls_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    print(f"\n📋 Found {len(urls)} videos to process")
    
    results = []
    for i, url in enumerate(urls, 1):
        print(f"\n{'='*60}")
        print(f"📹 Processing video {i}/{len(urls)}")
        print(f"{'='*60}")
        
        try:
            output = await process_video(url, target_lang)
            results.append({"url": url, "output": output, "status": "success"})
        except Exception as e:
            print(f"❌ Error processing {url}: {e}")
            results.append({"url": url, "error": str(e), "status": "failed"})
    
    # Summary
    print("\n" + "="*60)
    print("📊 BATCH PROCESSING COMPLETE")
    print("="*60)
    
    success = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "failed")
    
    print(f"   ✅ Successful: {success}")
    print(f"   ❌ Failed: {failed}")
    
    return results


def main():
    """Main entry point with CLI."""
    parser = argparse.ArgumentParser(
        description="GlobalDub - Automated Video Translation & Dubbing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dub a single video to Spanish
  python dub.py https://youtube.com/shorts/VIDEO_ID
  
  # Dub to Portuguese
  python dub.py https://youtube.com/shorts/VIDEO_ID --lang pt
  
  # Process multiple videos from file
  python dub.py --batch urls.txt --lang es
  
  # List available languages
  python dub.py --list-langs

Available Languages:
  es - Spanish (Mexico)      pt - Portuguese (Brazil)
  fr - French                de - German
  it - Italian               ja - Japanese
  ko - Korean                zh - Chinese (Mandarin)
  ar - Arabic                hi - Hindi
  ru - Russian
        """
    )
    
    parser.add_argument("url", nargs="?", help="YouTube video URL to dub")
    parser.add_argument("--lang", "-l", default="es", help="Target language (default: es)")
    parser.add_argument("--batch", "-b", metavar="FILE", help="Process URLs from file")
    parser.add_argument("--output", "-o", help="Output filename")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary files")
    parser.add_argument("--list-langs", action="store_true", help="List available languages")
    parser.add_argument("--check", action="store_true", help="Check dependencies only")
    
    args = parser.parse_args()
    
    if args.list_langs:
        print("\n🌍 Available Languages and Voices:\n")
        for code, voice in VOICE_MAP.items():
            print(f"   {code:6} → {voice}")
        return
    
    if args.check:
        check_dependencies()
        return
    
    # Check dependencies
    check_dependencies()
    
    if args.batch:
        asyncio.run(batch_process(args.batch, args.lang))
    elif args.url:
        asyncio.run(process_video(args.url, args.lang, args.output, args.keep_temp))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

