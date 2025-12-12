# 🌍 GlobalDub

**Automated Translation & Dubbing Pipeline for YouTube Shorts**

Transform English YouTube Shorts into Spanish, Portuguese, French, and 10+ other languages—completely free!

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Cost](https://img.shields.io/badge/Cost-$0-brightgreen?style=flat-square)

## 🚀 Features

- **Zero-Cost**: Uses Whisper (free) + Google Translate + Edge-TTS (free Microsoft voices)
- **Voiceover Style**: Documentary-style dubbing (not lip-sync)
- **Audio Ducking**: Keeps original background music/sfx at 10% volume
- **Smart Speed Matching**: Automatically adjusts dubbed audio to fit video length
- **12+ Languages**: Spanish, Portuguese, French, German, Japanese, Korean, and more
- **Batch Processing**: Dub multiple videos from a URL list

## 🎬 How It Works

1. **Download** video using yt-dlp
2. **Transcribe** audio using Whisper (base model, CPU-friendly)
3. **Translate** text using Google Translate
4. **Generate** dubbed audio using Edge-TTS
5. **Mix** dubbed audio over ducked original audio
6. **Export** final video

## 📁 Project Structure

```
GlobalDub/
├── dub.py              # Main dubbing script
├── requirements.txt    # Python dependencies
├── urls.txt            # (Optional) List of URLs for batch processing
├── output/             # Dubbed videos go here
└── temp/               # Temporary files (auto-cleaned)
```

## 🛠️ Installation

### Prerequisites

1. **Python 3.10+**
2. **FFmpeg** (required for audio/video processing)
   - Windows: `winget install ffmpeg`
   - Linux: `sudo apt install ffmpeg`
   - Mac: `brew install ffmpeg`

### Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/GlobalDub.git
cd GlobalDub

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

> ⚠️ **Note**: First run will download the Whisper model (~150MB for 'base').

## 📝 Usage

### Dub a Single Video

```bash
# Dub to Spanish (default)
python dub.py https://youtube.com/shorts/VIDEO_ID

# Dub to Portuguese
python dub.py https://youtube.com/shorts/VIDEO_ID --lang pt

# Dub to Japanese
python dub.py https://youtube.com/shorts/VIDEO_ID --lang ja

# Custom output name
python dub.py https://youtube.com/shorts/VIDEO_ID --output my_video.mp4
```

### Batch Process Multiple Videos

Create a `urls.txt` file:
```
# My videos to dub
https://youtube.com/shorts/abc123
https://youtube.com/shorts/def456
https://youtube.com/shorts/ghi789
```

Then run:
```bash
python dub.py --batch urls.txt --lang es
```

### List Available Languages

```bash
python dub.py --list-langs
```

### Check Dependencies

```bash
python dub.py --check
```

## 🌍 Supported Languages

| Code | Language | Voice |
|------|----------|-------|
| `es` | Spanish (Mexico) | DaliaNeural |
| `pt` | Portuguese (Brazil) | FranciscaNeural |
| `fr` | French | DeniseNeural |
| `de` | German | KatjaNeural |
| `it` | Italian | ElsaNeural |
| `ja` | Japanese | NanamiNeural |
| `ko` | Korean | SunHiNeural |
| `zh` | Chinese (Mandarin) | XiaoxiaoNeural |
| `ar` | Arabic | ZariyahNeural |
| `hi` | Hindi | SwaraNeural |
| `ru` | Russian | SvetlanaNeural |

## ⚙️ Configuration

Edit the constants in `dub.py`:

```python
# Whisper model (tiny/base/small/medium/large)
WHISPER_MODEL = "base"  # 'tiny' for faster, 'small' for better quality

# Original audio volume during dubbing
ORIGINAL_AUDIO_VOLUME = 0.1  # 10% - adjust to taste

# Maximum speed-up for dubbed audio
MAX_SPEED_FACTOR = 1.25  # Won't speed up more than 25%
```

## 🚀 Deployment (Oracle Cloud Free Tier)

1. Create an Oracle Cloud account (Always Free tier)
2. Launch an ARM instance (VM.Standard.A1.Flex)
3. SSH in and setup:

```bash
# Install dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip ffmpeg git -y

# Clone and setup
git clone https://github.com/YOUR_USERNAME/GlobalDub.git
cd GlobalDub
pip3 install -r requirements.txt

# Test with a video
python3 dub.py https://youtube.com/shorts/VIDEO_ID --lang es
```

### Performance Notes

- **Whisper 'base' model**: ~1-2 minutes per 60s video on CPU
- **Whisper 'tiny' model**: Faster but less accurate
- Oracle ARM instances handle this well

## 💡 Monetization Strategy

1. **Niche Translation**: Focus on specific content (cooking, fitness, educational)
2. **Multi-Channel**: Create channels in different languages
3. **Popular Content**: Dub trending shorts quickly
4. **Quality Control**: Review translations before uploading (optional)

## ⚠️ Legal Considerations

- **Fair Use**: Check if your use qualifies as transformative
- **Attribution**: Credit original creators when required
- **Monetization**: Some content may have restrictions
- **Terms of Service**: Respect platform guidelines

## 🤝 Contributing

Pull requests welcome! For major changes, open an issue first.

## 📄 License

MIT License - use responsibly!

---

**Made with ❤️ for the global hustle**

