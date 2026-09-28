import os
import sys
import random
import asyncio
import re
import requests
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

# 2. بنك المعلومات والخرائط ثلاثية الأبعاد (3D Maps Assets)
FACTS_DATABASE = [
    {
        "country": "بريطانيا",
        "fact": "هل تعلم أن بريطانيا هي الدولة الوحيدة التي لم تُستعمر في التاريخ الحديث؟",
        "image_url": "https://images.pexels.com/photos/460672/pexels-photo-460672.jpeg"
    },
    {
        "country": "ألمانيا",
        "fact": "بينما تمتلك ألمانيا أقوى وأضخم اقتصاد صناعي في قارة أوروبا بأكملها.",
        "image_url": "https://images.pexels.com/photos/109629/pexels-photo-109629.jpeg"
    },
    {
        "country": "جنوب أفريقيا",
        "fact": "وجنوب أفريقيا هي الدولة الوحيدة في العالم التي تمتلك ثلاث عواصم رسمية.",
        "image_url": "https://images.pexels.com/photos/259280/pexels-photo-259280.jpeg"
    },
    {
        "country": "اليابان",
        "fact": "أما اليابان فتمتلك أسرع وأدق شبكة قطارات فائقة السرعة على كوكب الأرض.",
        "image_url": "https://images.pexels.com/photos/161401/fuji-mountain-kawaguchiko-japan-161401.jpeg"
    },
    {
        "country": "سؤال التفاعل",
        "fact": "فما هي المعلومة الأبرز التي تميز دولتك؟ شاركنا في التعليقات!",
        "image_url": "https://images.pexels.com/photos/87651/earth-blue-planet-globe-planet-87651.jpeg"
    }
]

def format_arabic_text(text):
    """ضبط اتجاه وتشبيك النصوص العربية"""
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)

def create_caption_image(text, size=(1080, 1920)):
    """توليد صورة نصية شفافة مخصصة لتظهر بوضوح واحترافية فوق الفيديو"""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 46)
    except:
        font = ImageFont.load_default()
        
    formatted = format_arabic_text(text)
    
    # تقسيم النص إلى أسطر قصيرة تناسب شاشات الشورتس
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
        
        # خلفية مظللة للنص لضمان سهولة القراءة
        padding = 12
        draw.rectangle([x - padding, y_start - padding, x + text_w + padding, y_start + (bbox[3] - bbox[1]) + padding], fill=(0, 0, 0, 180))
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

def build_scene(scene_data, index):
    """بناء مشهد شورتس بدقة 1080x1920 مع صوت وحركة زوم مستمرة"""
    print(f"🎬 جاري معالجة المشهد ({index + 1}): {scene_data['country']}")
    
    # 1. الصوت
    audio_path = f"audio_{index}.mp3"
    asyncio.run(generate_speech(scene_data["fact"], audio_path))
    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration + 0.3
    
    # 2. الصورة وتجهيزها
    img_resp = requests.get(scene_data["image_url"], timeout=20)
    raw_img_path = f"img_{index}.jpg"
    with open(raw_img_path, "wb") as f:
        f.write(img_resp.content)
        
    # ضبط مقاس الصورة على أبعاد الهواتف 9:16
    im = Image.open(raw_img_path)
    im = im.resize((1080, 1920), Image.Resampling.LANCZOS)
    im.save(raw_img_path)
    
    # 3. تطبيق حركة التكبير التدريجي (Dynamic Zoom)
    img_clip = (ImageClip(raw_img_path)
                .set_duration(duration)
                .resize(lambda t: 1 + 0.05 * t)
                .crop(x_center=540, y_center=960, width=1080, height=1920))
    
    # 4. النص العربي فوق المشهد
    caption_path = create_caption_image(scene_data["fact"])
    caption_clip = ImageClip(caption_path).set_duration(duration)
    
    video = CompositeVideoClip([img_clip, caption_clip], size=(1080, 1920)).set_audio(audio_clip)
    return video

def create_complete_video():
    """تجميع المشاهد في فيديو شورتس كامل وتصديره"""
    scenes = []
    selected_facts = FACTS_DATABASE.copy()
    
    for i, item in enumerate(selected_facts):
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
    """رفع الفيديو مؤقتاً للحصول على رابط مباشر تقبله منصة Buffer فوراً"""
    print("☁️ جاري رفع الفيديو لتجهيز رابط النشر لـ Buffer...")
    url = "https://litterbox.catbox.moe/resources/internals/api.php"
    with open(file_path, "rb") as f:
        files = {
            "reqtype": (None, "fileupload"),
            "time": (None, "12h"),
            "fileToUpload": (file_path, f, "video/mp4")
        }
        res = requests.post(url, files=files, timeout=60)
        if res.status_code == 200 and res.text.startswith("http"):
            direct_url = res.text.strip()
            print(f"🔗 رابط الفيديو المباشر: {direct_url}")
            return direct_url
    raise Exception("فشل رفع ملف الفيديو إلى الخادم المؤقت.")

def publish_to_buffer(channel_id, title, video_url):
    """جدولة الفيديو على منصة Buffer"""
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
        print(f"⚠️ استجابة Buffer: {data}")

def main():
    # 1. إنشاء الفيديو بالكامل
    video_file = create_complete_video()
    
    # 2. رفعه والحصول على رابط MP4 مباشر
    public_url = upload_to_temp_host(video_file)
    
    # 3. جدولته على قنواتك الثلاث
    title = "حقائق ومعلومات مذهلة حول دول العالم 🌍⚡"
    for channel_id in CHANNELS_LIST:
        print(f"\n--- إرسال إلى Buffer للقناة: {channel_id} ---")
        publish_to_buffer(channel_id, title, public_url)

if __name__ == "__main__":
    main()
