import os
import sys
import random
import asyncio
import io
import requests

# ترقيع توافق moviepy مع مكتبة Pillow
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

# 1. إعدادات المفاتيح والقنوات
BUFFER_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN", "").strip()
DEFAULT_CHANNELS = [
    "6abacd06ea19ca0bde180ef9",
    "6abace11ea19ca0bde181821",
    "6abace7bea19ca0bde181dff"
]
env_channel_str = os.getenv("BUFFER_CHANNEL_IDS", "").strip()
CHANNELS_LIST = [ch.strip() for ch in env_channel_str.replace("\n", ",").split(",") if ch.strip()] if env_channel_str else DEFAULT_CHANNELS

# 2. بنك معلومات جغرافية وثائقية موسع (يتم اختيار 4 مشاهد عشوائية في كل فيديو + مشهد التفاعل)
FACTS_POOL = [
    {"country": "بريطانيا", "fact": "هل تعلم أن بريطانيا هي الدولة الوحيدة التي لم تُستعمر في التاريخ الحديث؟", "img": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=1080&h=1920&fit=crop"},
    {"country": "ألمانيا", "fact": "بينما تمتلك ألمانيا أقوى وأضخم اقتصاد صناعي متطور في قارة أوروبا.", "img": "https://images.unsplash.com/photo-1467269204594-9661b134dd2b?w=1080&h=1920&fit=crop"},
    {"country": "جنوب أفريقيا", "fact": "وجنوب أفريقيا هي الدولة الوحيدة في العالم التي تمتلك ثلاث عواصم رسمية.", "img": "https://images.unsplash.com/photo-1576485290814-1c72aa4bbb8e?w=1080&h=1920&fit=crop"},
    {"country": "اليابان", "fact": "أما اليابان فتمتلك أسرع وأدق شبكة قطارات فائقة السرعة على كوكب الأرض.", "img": "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?w=1080&h=1920&fit=crop"},
    {"country": "سنغافورة", "fact": "وتعتبر سنغافورة واحدة من أصغر دول العالم لكنها تمتلك أحد أكبر موانئ التجارة.", "img": "https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=1080&h=1920&fit=crop"},
    {"country": "كندا", "fact": "وتحتوي كندا على أكثر من ستين بالمئة من إجمالي بحيرات العالم الطبيعية العذبة.", "img": "https://images.unsplash.com/photo-1503614472-8c93d56e92ce?w=1080&h=1920&fit=crop"},
    {"country": "تركيا", "fact": "أما مدينة إسطنبول فهي المدينة الوحيدة الممتدة جغرافياً عبر قارتين في آن واحد.", "img": "https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?w=1080&h=1920&fit=crop"},
    {"country": "النرويج", "fact": "وفي شمال النرويج لا تغرب الشمس تماماً طوال فصل الصيف لشهور متتالية.", "img": "https://images.unsplash.com/photo-1507272931001-fc06c17e4f43?w=1080&h=1920&fit=crop"}
]

INTERACTION_FACTS = [
    {"country": "سؤال", "fact": "فما هي المعلومة الأبرز التي تميز دولتك؟ شاركنا رأيك في التعليقات!", "img": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1080&h=1920&fit=crop"},
    {"country": "سؤال", "fact": "أي من هذه الدول تود زيارتها مستقبلاً؟ بانتظار إجابتك في التعليقات!", "img": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1080&h=1920&fit=crop"}
]

# 3. معالجة النصوص العربية السليمة
def format_arabic_correctly(text):
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)

def create_arabic_caption(text, size=(1080, 1920)):
    """توليد صورة نصية عربية متراكبة بخط سليم ومقروء تماماً"""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
    except Exception:
        font = ImageFont.load_default()
        
    words = text.split()
    raw_lines = []
    current = []
    for w in words:
        current.append(w)
        if len(current) >= 4:
            raw_lines.append(" ".join(current))
            current = []
    if current:
        raw_lines.append(" ".join(current))
        
    formatted_lines = [format_arabic_correctly(line) for line in raw_lines]
    
    y_start = int(size[1] * 0.70)
    for line in formatted_lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (size[0] - text_w) // 2
        
        padding = 14
        draw.rectangle(
            [x - padding, y_start - padding, x + text_w + padding, y_start + text_h + padding],
            fill=(0, 0, 0, 190)
        )
        draw.text((x, y_start), line, font=font, fill=(255, 220, 0, 255))
        y_start += text_h + 24
        
    path = f"overlay_{random.randint(1000, 9999)}.png"
    img.save(path)
    return path

async def generate_voice(text, output_file, voice="ar-SA-HamedNeural"):
    """توليد فويس أوفر عربي فصيح عبر Edge-TTS"""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice, rate="+8%")
    await communicate.save(output_file)

def fetch_image(url, target_size, index):
    """جلب صورة المشهد بأبعاد رأسية 1080x1920"""
    path = f"scene_img_{index}.jpg"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code == 200 and len(r.content) > 3000:
            im = Image.open(io.BytesIO(r.content)).convert("RGB")
            im = im.resize(target_size, Image.Resampling.LANCZOS)
            im.save(path, "JPEG", quality=90)
            return path
    except Exception:
        pass
    
    im = Image.new("RGB", target_size, color=(15, 23, 42))
    im.save(path, "JPEG")
    return path

def build_shorts_video():
    """إنتاج فيديو شورتس رأسي احترافي مدته أقل من 60 ثانية"""
    size = (1080, 1920)
    # اختيار 4 معلومات عشوائية + خاتمة تفاعلية
    selected_scenes = random.sample(FACTS_POOL, 4) + [random.choice(INTERACTION_FACTS)]
    
    print(f"🎬 بدء إنتاج فيديو شورتس رأسي (9:16)...")
    scenes = []
    
    for idx, item in enumerate(selected_scenes):
        text = item["fact"]
        print(f"🎙️ معالجة المشهد ({idx + 1}/{len(selected_scenes)}): {item['country']}")
        
        # 1. الصوت
        audio_file = f"aud_{idx}.mp3"
        asyncio.run(generate_voice(text, audio_file))
        aud_clip = AudioFileClip(audio_file)
        duration = aud_clip.duration + 0.3
        
        # 2. الصورة مع حركة التكبير المستمرة
        img_path = fetch_image(item["img"], size, idx)
        img_clip = (ImageClip(img_path)
                    .set_duration(duration)
                    .resize(lambda t: 1 + 0.04 * t)
                    .crop(x_center=540, y_center=960, width=1080, height=1920))
        
        # 3. النص العربي المتراكب
        caption_file = create_arabic_caption(text, size=size)
        caption_clip = ImageClip(caption_file).set_duration(duration)
        
        scene = CompositeVideoClip([img_clip, caption_clip], size=size).set_audio(aud_clip)
        scenes.append(scene)
        
    final = concatenate_videoclips(scenes, method="compose")
    out_name = "final_shorts.mp4"
    final.write_videofile(
        out_name,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        bitrate="2500k",
        threads=4,
        preset="veryfast"
    )
    print("✨ تم اكتمال رندر الشورتس بنجاح!")
    return out_name

def upload_video_file(file_path):
    """رفع الفيديو والحصول على رابط مباشر يقبله Buffer"""
    print("☁️ جاري رفع الفيديو وتجهيز الرابط لـ Buffer...")

    # 1. خادم Uguu (سريع جداً ومباشر)
    try:
        print("🔄 محاولة الرفع عبر Uguu...")
        with open(file_path, "rb") as f:
            r = requests.post(
                "https://uguu.se/upload",
                files={"files[]": (os.path.basename(file_path), f, "video/mp4")},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=120
            )
            if r.status_code == 200:
                data = r.json()
                if data.get("success") and data.get("files"):
                    url = data["files"][0]["url"]
                    print(f"🔗 تم الرفع بنجاح عبر Uguu: {url}")
                    return url
    except Exception as e:
        print(f"⚠️ خطأ Uguu: {e}")

    # 2. خادم Pixeldrain (بديل ثانٍ)
    try:
        print("🔄 محاولة الرفع عبر Pixeldrain...")
        with open(file_path, "rb") as f:
            r = requests.post(
                "https://pixeldrain.com/api/file",
                files={"file": (os.path.basename(file_path), f, "video/mp4")},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=120
            )
            if r.status_code in [200, 201]:
                data = r.json()
                if data.get("id"):
                    url = f"https://pixeldrain.com/api/file/{data['id']}"
                    print(f"🔗 تم الرفع بنجاح عبر Pixeldrain: {url}")
                    return url
    except Exception as e:
        print(f"⚠️ خطأ Pixeldrain: {e}")

    raise Exception("فشلت جميع خوادم الرفع المباشر.")

def publish_to_buffer(channel_id, title, desc, video_url):
    """جدولة الشورتس على منصة Buffer عبر GraphQL API"""
    url = "https://api.buffer.com"
    headers = {"Authorization": f"Bearer {BUFFER_TOKEN}", "Content-Type": "application/json"}
    query = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess { post { id status } }
        ... on MutationError { message }
      }
    }
    """
    variables = {
        "input": {
            "channelId": channel_id,
            "text": desc,
            "schedulingType": "automatic",
            "mode": "addToQueue",
            "assets": [{"video": {"url": video_url}}],
            "metadata": {
                "youtube": {
                    "title": title[:95],
                    "categoryId": "27",
                    "madeForKids": False
                }
            }
        }
    }
    r = requests.post(url, headers=headers, json={"query": query, "variables": variables}, timeout=30)
    data = r.json()
    result = data.get("data", {}).get("createPost", {})
    if "post" in result and result["post"]:
        print(f"🚀 تم بنجاح جدولة الشورتس للقناة [{channel_id}] | ID: {result['post']['id']}")
    else:
        print(f"⚠️ استجابة Buffer للقناة [{channel_id}]: {data}")

def main():
    # 1. إنتاج الشورتس
    video_path = build_shorts_video()
    
    # 2. رفعه مباشرة
    video_url = upload_video_file(video_path)
    
    # 3. الجدولة لكل القنوات
    title = "حقائق ومعلومات مذهلة حول دول العالم 🌍⚡"
    desc = "شاهد أغرب الحقائق الجغرافية والمعلومات السريعة حول العالم 🎬⚡\n\n#حقائق #جغرافيا #هل_تعلم #Shorts #explore"
    
    for ch_id in CHANNELS_LIST:
        print(f"\n--- إرسال إلى Buffer للقناة: {ch_id} ---")
        publish_to_buffer(ch_id, title, desc, video_url)

if __name__ == "__main__":
    main()
