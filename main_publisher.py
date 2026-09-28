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

# 1. المفاتيح والقنوات (مع منع التكرار تماماً)
BUFFER_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN", "").strip()

DEFAULT_CHANNELS = [
    "6abacd06ea19ca0bde180ef9", # أبعاد جغرافية
    "6abace11ea19ca0bde181821", # مشاريع عملاقة
    "6abace7bea19ca0bde181dff"  # مسار
]

env_channel_str = os.getenv("BUFFER_CHANNEL_IDS", "").strip()
if env_channel_str:
    raw_channels = [ch.strip() for ch in env_channel_str.replace("\n", ",").split(",") if ch.strip()]
    CHANNELS_LIST = list(dict.fromkeys(raw_channels))
else:
    CHANNELS_LIST = DEFAULT_CHANNELS

# 2. بنك المحتوى المخصص: فيديو مختلف تماماً لكل قناة
NICHE_DATABASES = {
    "أبعاد جغرافية": {
        "title": "حقائق جغرافية مذهلة حول كوكب الأرض 🌍⚡",
        "hashtags": "#أبعاد_جغرافية #جغرافيا #غرائب #طبيعة #Shorts #explore",
        "facts": [
            {"fact": "هل تعلم أن روسيا تمتلك إحدى عشرة منطقة زمنية مختلفة في نفس اللحظة؟", "img": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=1080&h=1920&fit=crop"},
            {"fact": "وجبل إفرست ينمو بمعدل أربعة مليمترات إضافية سنوياً بفعل حركة الصفائح.", "img": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1080&h=1920&fit=crop"},
            {"fact": "وتحتوي كندا على أكثر من ستين بالمئة من إجمالي بحيرات العالم الطبيعية.", "img": "https://images.unsplash.com/photo-1503614472-8c93d56e92ce?w=1080&h=1920&fit=crop"},
            {"fact": "أما القارة القطبية الجنوبية فتعد أكبر صحراء جافة على وجه الأرض.", "img": "https://images.unsplash.com/photo-1517411032315-54ef2cb783bb?w=1080&h=1920&fit=crop"},
            {"fact": "وفي شمال النرويج لا تغرب الشمس تماماً طوال فصل الصيف لشهور متتالية.", "img": "https://images.unsplash.com/photo-1507272931001-fc06c17e4f43?w=1080&h=1920&fit=crop"}
        ],
        "questions": [
            {"fact": "ما هي أكثر معلومة جغرافية أدهشتك؟ شاركنا رأيك في التعليقات!", "img": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1080&h=1920&fit=crop"}
        ]
    },
    "مشاريع عملاقة": {
        "title": "أضخم المعجزات الهندسية في تاريخ البشرية 🏗️⚡",
        "hashtags": "#مشاريع_عملاقة #هندسة #بناء #ناطحات_سحاب #جسور #Shorts",
        "facts": [
            {"fact": "هل تعلم أن سد الممرات الثلاثة في الصين أبطأ دوران الأرض بجزء من الثانية؟", "img": "https://images.unsplash.com/photo-1541888946425-d0fbb186c5f7?w=1080&h=1920&fit=crop"},
            {"fact": "بينما استهلك برج خليفة في دبي ثلاثمئة وثلاثين ألف متر مكعب من الخرسانة.", "img": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=1080&h=1920&fit=crop"},
            {"fact": "ويمتد جسر دانيانغ كونشان لأكثر من مئة وأربعة وستين كيلومتراً كأطول جسر في العالم.", "img": "https://images.unsplash.com/photo-1545558014-8692077e9b5c?w=1080&h=1920&fit=crop"},
            {"fact": "أما نفق المانش فيربط بريطانيا بفرنسا تحت قاع البحر بعمق خمسة وسبعين متراً.", "img": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1080&h=1920&fit=crop"},
            {"fact": "وتعمل آلات حفر الأنفاق العملاقة بقوة جبارة توازي وزن مئات الطائرات النفاثة.", "img": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=1080&h=1920&fit=crop"}
        ],
        "questions": [
            {"fact": "أي من هذه المشاريع تعتبره الأكثر إبهاراً؟ اكتب لنا رأيك في التعليقات!", "img": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1080&h=1920&fit=crop"}
        ]
    },
    "مسار": {
        "title": "أسرار الممرات المائية وطرق التجارة العالمية 🚢⚡",
        "hashtags": "#مسار #اقتصاد #تجارة #مضائق #قناة_السويس #Shorts",
        "facts": [
            {"fact": "هل تعلم أن قناة السويس يمر عبرها أكثر من اثني عشر بالمئة من إجمالي التجارة العالمية؟", "img": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1080&h=1920&fit=crop"},
            {"fact": "بينما يعبر مضيق هرمز خُمس استهلاك العالم اليومي من النفط الخام والمشتقات البترولية.", "img": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=1080&h=1920&fit=crop"},
            {"fact": "وترفع قناة بنما السفن العملاقة ستة وعشرين متراً فوق سطح البحر عبر أهوسة مائية معقدة.", "img": "https://images.unsplash.com/photo-1505705694340-019e1e335916?w=1080&h=1920&fit=crop"},
            {"fact": "أما مضيق ملقا فيربط بين قارة آسيا والشرق الأوسط ويعبره مئة ألف سفينة سنوياً.", "img": "https://images.unsplash.com/photo-1578575437130-527eed3abbec?w=1080&h=1920&fit=crop"},
            {"fact": "وتشكل خطوط الشحن البحري الشريان الحقيقي الذي يغذي العالم بكل احتياجاته اليومية.", "img": "https://images.unsplash.com/photo-1494412574643-ff11b0a5c1c3?w=1080&h=1920&fit=crop"}
        ],
        "questions": [
            {"fact": "ما هو الممر المائي الأكثر أهمية وتأثيراً في نظرك؟ شاركنا رأيك في التعليقات!", "img": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1080&h=1920&fit=crop"}
        ]
    }
}

NICHE_NAMES = list(NICHE_DATABASES.keys())

# 3. إعداد خط Cairo الاحترافي للشورتس
CAIRO_FONT_PATH = "Cairo-Bold.ttf"

def get_arabic_font(size=46):
    """تنزيل خط Cairo تلقائياً إذا لم يكن متوفراً لضمان أعلى جودة كتابة"""
    if not os.path.exists(CAIRO_FONT_PATH):
        try:
            url = "https://github.com/google/fonts/raw/main/ofl/cairo/static/Cairo-Bold.ttf"
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                with open(CAIRO_FONT_PATH, "wb") as f:
                    f.write(r.content)
        except Exception:
            pass

    if os.path.exists(CAIRO_FONT_PATH):
        try:
            return ImageFont.truetype(CAIRO_FONT_PATH, size)
        except Exception:
            pass

    for sys_font in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf"
    ]:
        if os.path.exists(sys_font):
            try:
                return ImageFont.truetype(sys_font, size)
            except Exception:
                pass

    return ImageFont.load_default()

def create_arabic_caption(text, channel_idx, scene_idx, size=(1080, 1920)):
    """توليد صورة نصية عربية مشبوكة وسليمة 100% بنمط الشورتس"""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = get_arabic_font(size=46)

    # 1. تقسيم الكلمات أولاً لضمان عدم تداخل الأسطر
    words = text.strip().split()
    raw_lines = []
    current = []
    for w in words:
        current.append(w)
        if len(current) >= 4:
            raw_lines.append(" ".join(current))
            current = []
    if current:
        raw_lines.append(" ".join(current))

    # 2. تشبيك وعكس اتجاه كل سطر بشكل مستقل
    formatted_lines = []
    for line in raw_lines:
        reshaped = arabic_reshaper.reshape(line)
        bidi_line = get_display(reshaped)
        formatted_lines.append(bidi_line)

    # 3. رسم النص في أسفل الشاشة بخط واضح وخلفية مظللة
    y_start = int(size[1] * 0.68)
    for line in formatted_lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (size[0] - text_w) // 2

        pad_x, pad_y = 18, 10
        draw.rectangle(
            [x - pad_x, y_start - pad_y, x + text_w + pad_x, y_start + text_h + pad_y],
            fill=(0, 0, 0, 195)
        )
        draw.text(
            (x, y_start),
            line,
            font=font,
            fill=(255, 225, 0, 255),
            stroke_width=2,
            stroke_fill=(0, 0, 0, 255)
        )
        y_start += text_h + 26

    path = f"overlay_{channel_idx}_{scene_idx}.png"
    img.save(path)
    return path

async def generate_voice(text, output_file):
    """توليد تعليق صوتي عربي فصيح عبر Edge-TTS"""
    import edge_tts
    communicate = edge_tts.Communicate(text, "ar-SA-HamedNeural", rate="+8%")
    await communicate.save(output_file)

def fetch_image(url, target_size, filename):
    """جلب صورة المشهد بأبعاد الشورتس 1080x1920"""
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code == 200 and len(r.content) > 3000:
            im = Image.open(io.BytesIO(r.content)).convert("RGB")
            im = im.resize(target_size, Image.Resampling.LANCZOS)
            im.save(filename, "JPEG", quality=90)
            return filename
    except Exception:
        pass

    im = Image.new("RGB", target_size, color=(15, 23, 42))
    im.save(filename, "JPEG")
    return filename

def build_unique_short(niche_data, channel_idx):
    """إنتاج فيديو شورتس مخصص ومستقل تماماً لهذه القناة"""
    size = (1080, 1920)

    facts_pool = niche_data["facts"].copy()
    random.shuffle(facts_pool)
    selected_scenes = facts_pool[:4] + [random.choice(niche_data["questions"])]

    scenes = []
    temp_files = []

    for s_idx, item in enumerate(selected_scenes):
        text = item["fact"]

        # 1. الصوت
        audio_file = f"aud_{channel_idx}_{s_idx}.mp3"
        asyncio.run(generate_voice(text, audio_file))
        aud_clip = AudioFileClip(audio_file)
        duration = aud_clip.duration + 0.3
        temp_files.append(audio_file)

        # 2. الصورة وتأثير التكبير
        img_file = f"img_{channel_idx}_{s_idx}.jpg"
        fetch_image(item["img"], size, img_file)
        temp_files.append(img_file)

        img_clip = (ImageClip(img_file)
                    .set_duration(duration)
                    .resize(lambda t: 1 + 0.04 * t)
                    .crop(x_center=540, y_center=960, width=1080, height=1920))

        # 3. النص العربي المتراكب بالخط السليم
        caption_file = create_arabic_caption(text, channel_idx, s_idx, size=size)
        caption_clip = ImageClip(caption_file).set_duration(duration)
        temp_files.append(caption_file)

        scene = CompositeVideoClip([img_clip, caption_clip], size=size).set_audio(aud_clip)
        scenes.append(scene)

    final = concatenate_videoclips(scenes, method="compose")
    out_name = f"short_channel_{channel_idx}.mp4"
    final.write_videofile(
        out_name,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        bitrate="2200k",
        threads=4,
        preset="ultrafast"
    )

    # تنظيف الملفات المؤقتة
    for f in temp_files:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

    return out_name

def upload_video_file(file_path):
    """رفع الفيديو والحصول على رابط مباشر يقبله Buffer"""
    print(f"☁️ جاري رفع {file_path} للحصول على رابط مباشر...")

    # 1. Uguu
    try:
        with open(file_path, "rb") as f:
            r = requests.post("https://uguu.se/upload", files={"files[]": (os.path.basename(file_path), f, "video/mp4")}, timeout=120)
            if r.status_code == 200:
                data = r.json()
                if data.get("success") and data.get("files"):
                    url = data["files"][0]["url"]
                    print(f"🔗 تم الرفع عبر Uguu: {url}")
                    return url
    except Exception as e:
        print(f"⚠️ تعذر Uguu: {e}")

    # 2. Pixeldrain
    try:
        with open(file_path, "rb") as f:
            r = requests.post("https://pixeldrain.com/api/file", files={"file": (os.path.basename(file_path), f, "video/mp4")}, timeout=120)
            if r.status_code in [200, 201]:
                fid = r.json().get("id")
                if fid:
                    url = f"https://pixeldrain.com/api/file/{fid}"
                    print(f"🔗 تم الرفع عبر Pixeldrain: {url}")
                    return url
    except Exception as e:
        print(f"⚠️ تعذر Pixeldrain: {e}")

    raise Exception("فشلت جميع خوادم الرفع.")

def publish_to_buffer_now(channel_id, title, desc, video_url):
    """نشر الشورتس فوراً ولحظياً على يوتيوب عبر Buffer دون إرساله للجدولة"""
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
    # لاحظ: استخدام mode: shareNow للنشر الفوري المباشر
    variables = {
        "input": {
            "channelId": channel_id,
            "text": desc,
            "schedulingType": "automatic",
            "mode": "shareNow",
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
        print(f"⚡ تم النشر الفوري بنجاح للقناة [{channel_id}] | ID: {result['post']['id']}")
    else:
        print(f"⚠️ استجابة Buffer للقناة [{channel_id}]: {data}")

def main():
    print(f"📋 عدد القنوات الفعلية المستهدفة (بدون أي تكرار): {len(CHANNELS_LIST)}")

    for idx, channel_id in enumerate(CHANNELS_LIST):
        niche_name = NICHE_NAMES[idx % len(NICHE_NAMES)]
        niche_data = NICHE_DATABASES[niche_name]

        print(f"\n=======================================================")
        print(f"🎬 [القناة {idx+1}/{len(CHANNELS_LIST)}] جاري إنتاج فيديو مخصص لقناة: {niche_name} ({channel_id})")
        print(f"=======================================================")

        video_path = build_unique_short(niche_data, idx)
        video_url = upload_video_file(video_path)

        title = niche_data["title"]
        desc = f"شاهد تفاصيل مذهلة وحقائق حصرية حول {niche_name} ⚡🎬\n\n{niche_data['hashtags']}"

        print(f"⚡ جاري النشر الفوري والمباشر الآن إلى يوتيوب...")
        publish_to_buffer_now(channel_id, title, desc, video_url)

        if os.path.exists(video_path):
            try: os.remove(video_path)
            except: pass

if __name__ == "__main__":
    main()
