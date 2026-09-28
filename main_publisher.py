import os
import sys
import random
import asyncio
import io
import requests

# ترقيع توافق Pillow مع moviepy
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

# 1. المفاتيح والقنوات
BUFFER_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN", "").strip()
DEFAULT_CHANNELS = [
    "6abacd06ea19ca0bde180ef9",
    "6abace11ea19ca0bde181821",
    "6abace7bea19ca0bde181dff"
]
env_channel_str = os.getenv("BUFFER_CHANNEL_IDS", "").strip()
CHANNELS_LIST = [ch.strip() for ch in env_channel_str.replace("\n", ",").split(",") if ch.strip()] if env_channel_str else DEFAULT_CHANNELS

# 2. ضبط النصوص العربية بدون عكس الحروف أو تفرقتها
def format_arabic_correctly(text):
    """تشبيك الحروف العربية وضبط الترتيب من اليمين لليسار بدقة"""
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
        
    # تقسيم الكلمات إلى أسطر قبل تطبيق الـ Bidi لعدم قلب ترتيب الكلمات
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
        
    # تعريب وتشبيك كل سطر بشكل منفصل
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
    """توليد فويس أوفر وثائقي فصيح عبر Edge-TTS"""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice, rate="+5%")
    await communicate.save(output_file)

def fetch_image(url, target_size, index):
    """جلب صورة المشهد بالأبعاد المطلوبة سينمائياً"""
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
    
    # خلفية بديلة أنيقة في حال انقطاع السيرفر
    im = Image.new("RGB", target_size, color=(15, 23, 42))
    im.save(path, "JPEG")
    return path

# 3. بنك محتوى الشورتس (9:16 عمودي)
SHORTS_DATA = [
    {"fact": "هل تعلم أن بريطانيا هي الدولة الوحيدة التي لم تُستعمر في التاريخ الحديث؟", "img": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=1080&h=1920&fit=crop"},
    {"fact": "بينما تمتلك ألمانيا أقوى وأضخم اقتصاد صناعي متطور في قارة أوروبا.", "img": "https://images.unsplash.com/photo-1467269204594-9661b134dd2b?w=1080&h=1920&fit=crop"},
    {"fact": "وجنوب أفريقيا هي الدولة الوحيدة في العالم التي تمتلك ثلاث عواصم رسمية.", "img": "https://images.unsplash.com/photo-1576485290814-1c72aa4bbb8e?w=1080&h=1920&fit=crop"},
    {"fact": "أما اليابان فتمتلك أسرع وأدق شبكة قطارات فائقة السرعة على كوكب الأرض.", "img": "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?w=1080&h=1920&fit=crop"},
    {"fact": "فما هي المعلومة الأبرز التي تميز دولتك؟ شاركنا رأيك في التعليقات!", "img": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1080&h=1920&fit=crop"}
]

# 4. بنك محتوى الفيلم الوثائقي الطويل (16:9 أفقي بدقة 1920x1080 على نسق DW)
DOCUMENTARY_CHAPTERS = [
    {
        "title": "المقدمة: لغز نشأة الحضارات والجغرافيا",
        "narration": "منذ فجر التاريخ البشري، لم تكن الجغرافيا مجرد تضاريس وجبال وأنهار، بل كانت القوة الخفية التي صاغت مصائر الإمبراطوريات ورسمت حدود القوة والنفوذ في عالمنا المعاصر.",
        "img": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1920&h=1080&fit=crop"
    },
    {
        "title": "الفصل الأول: التحولات الهندسية والمشاريع الكبرى",
        "narration": "شهدت العقود الأخيرة سباقاً هندسياً غير مسبوق، حيث أعادت المشاريع العملاقة تشكيل مسارات التجارة العالمية، وربطت القارات بسلاسل إمداد تمثل الشرايين الحيوية للاقتصاد العالمي الحديث.",
        "img": "https://images.unsplash.com/photo-1541888946425-d0fbb186c5f7?w=1920&h=1080&fit=crop"
    },
    {
        "title": "الفصل الثاني: الممرات المائية وصراع النفوذ",
        "narration": "تتحكم المضائق والممرات البحرية في أكثر من ثمانين بالمئة من حركة التجارة الدولية، مما جعل السيطرة عليها محوراً استراتيجياً تدور حوله كبرى التحالفات والصراعات الجيوسياسية عبر التاريخ.",
        "img": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1920&h=1080&fit=crop"
    },
    {
        "title": "الخاتمة: آفاق المستقبل والتحديات القادمة",
        "narration": "مع تسارع التغيرات المناخية والتحول نحو مصادر الطاقة المتجددة، تقف البشرية اليوم أمام مفترق طرق حاسم يتطلب إعادة التفكير في علاقتنا مع كوكب الأرض وكيفية إدارة موارده للأجيال القادمة.",
        "img": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1920&h=1080&fit=crop"
    }
]

def build_video(mode="short"):
    """إنتاج الفيديو وفق النوع: شورتس رأسي (9:16) أو وثائقي أفقي (16:9)"""
    is_short = (mode == "short")
    size = (1080, 1920) if is_short else (1920, 1080)
    dataset = SHORTS_DATA if is_short else DOCUMENTARY_CHAPTERS
    
    print(f"🎬 بدء إنتاج فيديو: [{'شورتس رأسي' if is_short else 'وثائقي أفقي سينمائي 16:9'}]")
    scenes = []
    
    for idx, item in enumerate(dataset):
        text = item["fact"] if is_short else item["narration"]
        print(f"🎙️ معالجة الجزء ({idx + 1}/{len(dataset)})...")
        
        # 1. الصوت
        audio_file = f"aud_{idx}.mp3"
        asyncio.run(generate_voice(text, audio_file))
        aud_clip = AudioFileClip(audio_file)
        duration = aud_clip.duration + 0.5
        
        # 2. الصورة وتأثير التكبير السينمائي
        img_path = fetch_image(item["img"], size, idx)
        img_clip = (ImageClip(img_path)
                    .set_duration(duration)
                    .resize(lambda t: 1 + 0.03 * t)
                    .crop(x_center=size[0]//2, y_center=size[1]//2, width=size[0], height=size[1]))
        
        # 3. النصوص (فقط في الشورتس بطلب المشاهدين، الوثائقي شاشة سينمائية نقية)
        if is_short:
            caption_file = create_arabic_caption(text, size=size)
            caption_clip = ImageClip(caption_file).set_duration(duration)
            scene = CompositeVideoClip([img_clip, caption_clip], size=size).set_audio(aud_clip)
        else:
            scene = img_clip.set_audio(aud_clip)
            
        scenes.append(scene)
        
    final = concatenate_videoclips(scenes, method="compose")
    out_name = f"output_{mode}.mp4"
    final.write_videofile(
        out_name,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        preset="ultrafast"
    )
    print(f"✨ اكتمل تصدير الفيديو: {out_name}")
    return out_name

def upload_video_file(file_path):
    """رفع الفيديو عبر خوادم تدعم Buffer المباشر"""
    print("☁️ جاري رفع الفيديو وتجهيز الرابط لـ Buffer...")

    # 1. 0x0.st
    try:
        with open(file_path, "rb") as f:
            r = requests.post("https://0x0.st", files={"file": (os.path.basename(file_path), f, "video/mp4")}, timeout=120)
            if r.status_code == 200 and r.text.strip().startswith("http"):
                url = r.text.strip()
                print(f"🔗 رابط الرفع (0x0.st): {url}")
                return url
    except Exception as e:
        print(f"⚠️ تعذر 0x0: {e}")

    # 2. Pixeldrain
    try:
        with open(file_path, "rb") as f:
            r = requests.post(f"https://pixeldrain.com/api/file/{os.path.basename(file_path)}", files={"file": f}, timeout=120)
            if r.status_code in [200, 201]:
                fid = r.json().get("id")
                url = f"https://pixeldrain.com/api/file/{fid}"
                print(f"🔗 رابط الرفع (Pixeldrain): {url}")
                return url
    except Exception as e:
        print(f"⚠️ تعذر Pixeldrain: {e}")

    raise Exception("فشلت جميع خوادم الرفع.")

def publish_post(channel_id, title, desc, video_url):
    """إرسال المنشور إلى Buffer عبر GraphQL"""
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
        print(f"🚀 تم بنجاح النشر للقناة [{channel_id}] | ID: {result['post']['id']}")
    else:
        print(f"⚠️ استجابة Buffer: {data}")

def main():
    # قراءة نوع المهمة من سطر الأوامر (short أو long)
    job_type = sys.argv[1].lower() if len(sys.argv) > 1 else "short"
    
    # 1. إنتاج الفيديو بالمقاس الصحيح (رأسي للشورتس أو أفقي للوثائقي)
    video_path = build_video(job_type)
    
    # 2. الرفع للحصول على الرابط
    video_url = upload_video_file(video_path)
    
    # 3. إعداد البيانات والنشر
    if job_type == "short":
        title = "حقائق ومعلومات مذهلة حول دول العالم 🌍⚡"
        desc = "شاهد أغرب الحقائق الجغرافية والمعلومات السريعة حول العالم 🎬⚡\n\n#حقائق #جغرافيا #هل_تعلم #Shorts #explore"
    else:
        title = "وثائقي حصري: أسرار الجغرافيا وصراع النفوذ العالمي 🌍🎬"
        desc = "فيلم وثائقي شامل يستعرض خبايا الجغرافيا وتأثير المشاريع العملاقة على موازين القوى العالمية.\n\n#وثائقي #جغرافيا #مشاريع_عملاقة #اقتصاد #تحليل"
        
    for ch_id in CHANNELS_LIST:
        print(f"\n--- إرسال إلى Buffer للقناة: {ch_id} ---")
        publish_post(ch_id, title, desc, video_url)

if __name__ == "__main__":
    main()
