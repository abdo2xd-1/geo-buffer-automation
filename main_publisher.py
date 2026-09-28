import os
import sys
import random
import asyncio
import io
import requests

# ترقيع توافق moviepy مع Pillow
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
    concatenate_videoclips
)

# 1. إعدادات المفاتيح
BUFFER_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN", "").strip()
DEFAULT_CHANNELS = [
    "6abacd06ea19ca0bde180ef9",
    "6abace11ea19ca0bde181821",
    "6abace7bea19ca0bde181dff"
]
env_channel_str = os.getenv("BUFFER_CHANNEL_IDS", "").strip()
CHANNELS_LIST = [ch.strip() for ch in env_channel_str.replace("\n", ",").split(",") if ch.strip()] if env_channel_str else DEFAULT_CHANNELS

# 2. بنك المعلومات والمشاهد بدقة 1080x1920
FACTS_DATABASE = [
    {
        "country": "بريطانيا",
        "fact": "هل تعلم أن بريطانيا هي الدولة الوحيدة التي لم تُستعمر في التاريخ الحديث؟",
        "image_url": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=1080&h=1920&fit=crop"
    },
    {
        "country": "ألمانيا",
        "fact": "بينما تمتلك ألمانيا أقوى وأضخم اقتصاد صناعي في قارة أوروبا بأكملها.",
        "image_url": "https://images.unsplash.com/photo-1467269204594-9661b134dd2b?w=1080&h=1920&fit=crop"
    },
    {
        "country": "جنوب أفريقيا",
        "fact": "وجنوب أفريقيا هي الدولة الوحيدة في العالم التي تمتلك ثلاث عواصم رسمية.",
        "image_url": "https://images.unsplash.com/photo-1576485290814-1c72aa4bbb8e?w=1080&h=1920&fit=crop"
    },
    {
        "country": "اليابان",
        "fact": "أما اليابان فتمتلك أسرع وأدق شبكة قطارات فائقة السرعة على كوكب الأرض.",
        "image_url": "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?w=1080&h=1920&fit=crop"
    },
    {
        "country": "سؤال التفاعل",
        "fact": "فما هي المعلومة الأبرز التي تميز دولتك؟ شاركنا في التعليقات!",
        "image_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1080&h=1920&fit=crop"
    }
]

def format_arabic_text(text):
    """ضبط اتجاه وتشبيك النصوص العربية"""
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)

def create_caption_image(text, size=(1080, 1920)):
    """توليد صورة نصية شفافة مخصصة لتظهر بوضوح فوق الفيديو"""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 46)
    except Exception:
        font = ImageFont.load_default()
        
    formatted = format_arabic_text(text)
    
    words = formatted.split()
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        if len(current_line) >= 4:
            lines.append(" ".join(current_line))
            current_line = []
    if current_line:
        lines.append(" ".join(current_line))
        
    y_start = int(size[1] * 0.70)
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = (size[0] - text_w) // 2
        
        padding = 14
        draw.rectangle(
            [x - padding, y_start - padding, x + text_w + padding, y_start + (bbox[3] - bbox[1]) + padding],
            fill=(0, 0, 0, 185)
        )
        draw.text((x, y_start), line, font=font, fill=(255, 220, 0, 255))
        y_start += (bbox[3] - bbox[1]) + 24
        
    overlay_path = f"overlay_{random.randint(100, 999)}.png"
    img.save(overlay_path)
    return overlay_path

async def generate_speech(text, output_file):
    """توليد الصوت العربي الفصيح عبر Edge-TTS"""
    import edge_tts
    voice = "ar-SA-HamedNeural"
    communicate = edge_tts.Communicate(text, voice, rate="+10%")
    await communicate.save(output_file)

def get_scene_image(image_url, country_name, index):
    """تحميل الصورة بأمان تام مع نظام استرجاع تلقائي"""
    raw_path = f"img_{index}.jpg"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        resp = requests.get(image_url, headers=headers, timeout=20)
        if resp.status_code == 200 and len(resp.content) > 3000:
            test_img = Image.open(io.BytesIO(resp.content))
            test_img.verify()
            
            im = Image.open(io.BytesIO(resp.content)).convert("RGB")
            im = im.resize((1080, 1920), Image.Resampling.LANCZOS)
            im.save(raw_path, "JPEG", quality=90)
            return raw_path
    except Exception as e:
        print(f"⚠️ تنبيه: تعذر جلب صورة {country_name} ({e})، سيتم توليد خلفية بديلة.")

    fallback_img = Image.new("RGB", (1080, 1920), color=(15, 23, 42))
    draw = ImageDraw.Draw(fallback_img)
    draw.rectangle([40, 40, 1040, 1880], outline=(56, 189, 248), width=8)
    fallback_img.save(raw_path, "JPEG")
    return raw_path

def build_scene(scene_data, index):
    """بناء مشهد الشورتس مع الصوت وحركة التكبير والنصوص"""
    print(f"🎬 جاري معالجة المشهد ({index + 1}): {scene_data['country']}")
    
    audio_path = f"audio_{index}.mp3"
    asyncio.run(generate_speech(scene_data["fact"], audio_path))
    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration + 0.3
    
    img_path = get_scene_image(scene_data["image_url"], scene_data["country"], index)
    
    img_clip = (ImageClip(img_path)
                .set_duration(duration)
                .resize(lambda t: 1 + 0.04 * t)
                .crop(x_center=540, y_center=960, width=1080, height=1920))
    
    caption_path = create_caption_image(scene_data["fact"])
    caption_clip = ImageClip(caption_path).set_duration(duration)
    
    video = CompositeVideoClip([img_clip, caption_clip], size=(1080, 1920)).set_audio(audio_clip)
    return video

def create_complete_video():
    """تجميع المشاهد ورندرة الفيديو النهائي"""
    scenes = []
    for i, item in enumerate(FACTS_DATABASE):
        scene = build_scene(item, i)
        scenes.append(scene)
        
    final = concatenate_videoclips(scenes, method="compose")
    output_filename = "final_output.mp4"
    final.write_videofile(
        output_filename,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        preset="ultrafast"
    )
    print("✨ تم اكتمال رندر الفيديو بنجاح!")
    return output_filename

def upload_to_temp_host(file_path):
    """رفع الفيديو عبر خوادم موثوقة ومفتوحة تقبل GitHub Actions وسيرفرات Buffer"""
    print("☁️ جاري رفع الفيديو وتجهيز الرابط المباشر لـ Buffer...")

    # 1. الخادم الأول: 0x0.st (خفيف جداً ومباشر بدون Cloudflare)
    try:
        print("🔄 محاولة الرفع عبر 0x0.st...")
        with open(file_path, "rb") as f:
            resp = requests.post(
                "https://0x0.st",
                files={"file": (os.path.basename(file_path), f, "video/mp4")},
                headers={"User-Agent": "curl/8.0.0"},
                timeout=90
            )
            if resp.status_code == 200 and resp.text.strip().startswith("http"):
                url = resp.text.strip()
                print(f"🔗 تم الرفع بنجاح عبر 0x0.st: {url}")
                return url
            print(f"⚠️ استجابة 0x0.st: {resp.status_code} - {resp.text[:100]}")
    except Exception as e:
        print(f"⚠️ تعذر 0x0.st: {e}")

    # 2. الخادم الثاني: uguu.se (سريع ومخصص للوسائط المؤقتة المباشرة)
    try:
        print("🔄 محاولة الرفع عبر uguu.se...")
        with open(file_path, "rb") as f:
            resp = requests.post(
                "https://uguu.se/upload",
                files={"files[]": (os.path.basename(file_path), f, "video/mp4")},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=90
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success") and data.get("files"):
                    url = data["files"][0]["url"]
                    print(f"🔗 تم الرفع بنجاح عبر Uguu: {url}")
                    return url
            print(f"⚠️ استجابة uguu: {resp.status_code}")
    except Exception as e:
        print(f"⚠️ تعذر uguu: {e}")

    # 3. الخادم الثالث: pixeldrain.com (خادم عالمي سريع ويدعم التنزيل المباشر)
    try:
        print("🔄 محاولة الرفع عبر pixeldrain.com...")
        with open(file_path, "rb") as f:
            resp = requests.post(
                f"https://pixeldrain.com/api/file/{os.path.basename(file_path)}",
                files={"file": f},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=90
            )
            if resp.status_code in [200, 201]:
                file_id = resp.json().get("id")
                if file_id:
                    url = f"https://pixeldrain.com/api/file/{file_id}"
                    print(f"🔗 تم الرفع بنجاح عبر Pixeldrain: {url}")
                    return url
            print(f"⚠️ استجابة pixeldrain: {resp.status_code}")
    except Exception as e:
        print(f"⚠️ تعذر pixeldrain: {e}")

    raise Exception("فشلت جميع خوادم الرفع المباشر.")

def publish_to_buffer(channel_id, title, video_url):
    """جدولة الفيديو على منصة Buffer عبر GraphQL API"""
    url = "https://api.buffer.com"
    headers = {
        "Authorization": f"Bearer {BUFFER_TOKEN}",
        "Content-Type": "application/json"
    }

    query = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess {
          post {
            id
            status
          }
        }
        ... on MutationError {
          message
        }
      }
    }
    """

    variables = {
        "input": {
            "channelId": channel_id,
            "text": f"{title}\n\n#حقائق #جغرافيا #هل_تعلم #Shorts #explore",
            "schedulingType": "automatic",
            "mode": "addToQueue",
            "assets": [
                {
                    "video": {
                        "url": video_url
                    }
                }
            ],
            "metadata": {
                "youtube": {
                    "title": title[:95],
                    "categoryId": "27",
                    "madeForKids": False
                }
            }
        }
    }

    res = requests.post(url, headers=headers, json={"query": query, "variables": variables}, timeout=30)
    data = res.json()
    result = data.get("data", {}).get("createPost", {})
    if "post" in result and result["post"]:
        print(f"🚀 تم جدولته بنجاح للقناة [{channel_id}] | ID: {result['post']['id']}")
    else:
        print(f"⚠️ استجابة Buffer للقناة [{channel_id}]: {data}")

def main():
    video_file = create_complete_video()
    public_url = upload_to_temp_host(video_file)
    
    title = "حقائق ومعلومات مذهلة حول دول العالم 🌍⚡"
    for channel_id in CHANNELS_LIST:
        print(f"\n--- إرسال إلى Buffer للقناة: {channel_id} ---")
        publish_to_buffer(channel_id, title, public_url)

if __name__ == "__main__":
    main()
