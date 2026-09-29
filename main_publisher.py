import os
import sys
import random
import asyncio
import io
import requests

# ترقيع توافق moviepy مع مكتبة Pillow
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    setattr(PIL.Image, 'ANTIALIAS', PIL.Image.Resampling.LANCZOS)

from PIL import Image, ImageDraw, ImageFont, features
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    ImageClip,
    ColorClip,
    CompositeVideoClip,
    concatenate_videoclips,
    vfx
)

# 1. المفاتيح والقنوات
BUFFER_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN", "").strip()
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "").strip()

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

# 2. بنك المشاهد بأسلوب غابرييل عماد
CHANNELS_CONTENT = {
    # 🌍 القناة الأولى: أبعاد جغرافية
    "أبعاد جغرافية": {
        "title": "معلومات جغرافية صادمة ومخيفة عن كوكب الأرض !!😱⚡",
        "desc": "أغرب الحقائق الجغرافية التي لم تسمع بها من قبل عن كوكب الأرض! اكتب سبحان الله واشترك للمزيد 🌍⚡\n\n#أبعاد_جغرافية #حقائق_مرعبة #غرائب #هل_تعلم #Shorts #explore",
        "scenes": [
            {
                "hook": "أنت تعرف إن في روسيا فرق التوقيت بيوصل لإحدى عشرة ساعة بين طرفي البلد؟",
                "display": ["أنت تعرف إن روسيا فيها", "11 منطقة زمنية مختلفة", "في نفس اللحظة؟!"],
                "query": "snow forest drone",
                "img_backup": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=1080&h=1920&fit=crop"
            },
            {
                "hook": "وجبل إفرست الأعلى في العالم، بينمو أربعة مليمترات زيادة كل سنة بسبب حركة الأرض!",
                "display": ["وجبل إفرست كل سنة", "بينمو 4 مليمترات زيادة", "بفعل حركة الصفائح!"],
                "query": "mountain clouds aerial",
                "img_backup": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1080&h=1920&fit=crop"
            },
            {
                "hook": "وفي القارة القطبية الجنوبية، ما سقطش عليها نقطة مطر واحدة من أكتر من مليوني سنة!",
                "display": ["والقارة القطبية الجنوبية", "ما نزلش عليها مطر", "من مليوني سنة!"],
                "query": "ice glacier arctic",
                "img_backup": "https://images.unsplash.com/photo-1517411032315-54ef2cb783bb?w=1080&h=1920&fit=crop"
            },
            {
                "hook": "وفي شمال النرويج، الشمس بتفضل ساطعة وما بتغربش نهائياً طوال فصل الصيف!",
                "display": ["وفي شمال النرويج", "الشمس ما بتغربش أبداً", "طوال الصيف!"],
                "query": "sunset landscape northern",
                "img_backup": "https://images.unsplash.com/photo-1507272931001-fc06c17e4f43?w=1080&h=1920&fit=crop"
            },
            {
                "hook": "ما تنساش تكتب سبحان الله في التعليقات وتشترك في القناة وتعمل لايك!",
                "display": ["اكتب سبحان الله في التعليقات", "واشترك في القناة حالا!", "واعمل لايك للفيديو"],
                "query": "planet earth space",
                "img_backup": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1080&h=1920&fit=crop"
            }
        ]
    },

    # 🏗️ القناة الثانية: مشاريع عملاقة
    "مشاريع عملاقة": {
        "title": "أضخم مشاريع في تاريخ البشرية غيرت دوران الأرض !!😱🏗️",
        "desc": "إنجازات هندسية خارقة ومعلومات مرعبة عن سدود وناطحات العالم! اكتب سبحان الله واشترك 🏗️⚡\n\n#مشاريع_عملاقة #هندسة #بناء #ناطحات_سحاب #غرائب #Shorts",
        "scenes": [
            {
                "hook": "أنت تعرف إن سد الممرات الثلاثة في الصين، من ضخامته، أبطأ حركة دوران كوكب الأرض؟",
                "display": ["سد الممرات في الصين", "أبطأ دوران الأرض بالكامل", "بسبب ضخامة وزنه!"],
                "query": "water dam reservoir",
                "img_backup": "https://images.unsplash.com/photo-1541888946425-d0fbb186c5f7?w=1080&h=1920&fit=crop"
            },
            {
                "hook": "وبرج خليفة في دبي، وزنه بيعادل مئة ألف فيل ضخم ومصنوع من خرسانة جبارة!",
                "display": ["وبرج خليفة في دبي", "وزنه بيعادل وزن", "100 ألف فيل!"],
                "query": "dubai skyline skyscraper",
                "img_backup": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=1080&h=1920&fit=crop"
            },
            {
                "hook": "ونفق المانش بيسمح للقطارات تمر تحت قاع البحر بين بريطانيا وفرنسا في ظلام دامس!",
                "display": ["ونفق المانش بيمر", "تحت قاع المحيط تماماً", "بين فرنسا وبريطانيا!"],
                "query": "train speed tunnel",
                "img_backup": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1080&h=1920&fit=crop"
            },
            {
                "hook": "وأطول جسر على وجه الأرض بيمتد لأكتر من مئة وأربعة وستين كيلومتراً بدون توقف!",
                "display": ["وأطول جسر في العالم", "طوله 164 كيلومتر", "في قلب الصين!"],
                "query": "highway bridge drone",
                "img_backup": "https://images.unsplash.com/photo-1545558014-8692077e9b5c?w=1080&h=1920&fit=crop"
            },
            {
                "hook": "ما تنساش تكتب سبحان الله وتشترك في القناة وتعمل لايك!",
                "display": ["اكتب سبحان الله في التعليقات", "واشترك في القناة حالا!", "واعمل لايك للفيديو"],
                "query": "construction building site",
                "img_backup": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1080&h=1920&fit=crop"
            }
        ]
    },

    # 🚢 القناة الثالثة: مسار
    "مسار": {
        "title": "أسرار مرعبة عن المضائق وطرق التجارة العالمية !!😱🚢",
        "desc": "أخطر وأهم الممرات المائية التي تقود العالم! لا تنسَ كتابة سبحان الله والاشتراك بالقناة 🚢⚡\n\n#مسار #اقتصاد #تجارة #مضائق #قناة_السويس #Shorts",
        "scenes": [
            {
                "hook": "أنت تعرف إن لو مضيق هرمز اتقفل يوم واحد، أسعار البنزين والنفط في العالم هتنفجر فوراً؟",
                "display": ["لو مضيق هرمز اتقفل", "خُمس نفط كوكب الأرض", "هيتوقف في لحظة!"],
                "query": "oil tanker ship sea",
                "img_backup": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=1080&h=1920&fit=crop"
            },
            {
                "hook": "وقناة السويس بيمر عبرها تريليونات الدولارات سنوياً، وهي نبض التجارة بين الشرق والغرب!",
                "display": ["وقناة السويس بيمر منها", "أكتر من 12 بالمئة", "من تجارة العالم كله!"],
                "query": "container vessel canal",
                "img_backup": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1080&h=1920&fit=crop"
            },
            {
                "hook": "وقناة بنما بترفع السفن العملاقة فوق الجبل لارتفاع ستة وعشرين متراً بنظام مائي عبقري!",
                "display": ["وقناة بنما بترفع السفن", "26 متر فوق الجبال", "عبر أهوسة مائية مذهلة!"],
                "query": "ship lock panama",
                "img_backup": "https://images.unsplash.com/photo-1505705694340-019e1e335916?w=1080&h=1920&fit=crop"
            },
            {
                "hook": "ومضيق ملقا بتمر منه مئة ألف سفينة سنوياً وسط حراسة مشددة ضد القرصنة البحرية!",
                "display": ["ومضيق ملقا بتمر منه", "100 ألف سفينة سنوياً", "في ممر بحري ضيق!"],
                "query": "cargo vessel ocean",
                "img_backup": "https://images.unsplash.com/photo-1578575437130-527eed3abbec?w=1080&h=1920&fit=crop"
            },
            {
                "hook": "ما تنساش تكتب سبحان الله في التعليقات وتشترك في القناة وتعمل لايك!",
                "display": ["اكتب سبحان الله في التعليقات", "واشترك في القناة حالا!", "واعمل لايك للفيديو"],
                "query": "blue sea aerial",
                "img_backup": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1080&h=1920&fit=crop"
            }
        ]
    }
}

NICHE_KEYS = list(CHANNELS_CONTENT.keys())

# 3. إعداد خط Noto Sans Arabic Bold
def get_best_arabic_font(size=54):
    for p in [
        "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoKufiArabic-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

def create_gabriel_caption(text_lines, ch_idx, scene_idx, size=(1080, 1920)):
    """توليد نصوص عربية سليمة 100% بنمط غابرييل عماد (خط أبيض ساطع بإطار أسود عريض)"""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = get_best_arabic_font(size=54)

    line_height = 85
    total_height = len(text_lines) * line_height
    y_start = 960 - (total_height // 2)

    has_raqm = features.check("raqm")

    for i, line in enumerate(text_lines):
        y = y_start + (i * line_height)
        if has_raqm:
            draw.text(
                (540, y),
                line,
                font=font,
                fill=(255, 255, 255, 255),
                stroke_width=6,
                stroke_fill=(0, 0, 0, 255),
                anchor="mm",
                direction="rtl"
            )
        else:
            import arabic_reshaper
            from bidi.algorithm import get_display
            bidi_text = get_display(arabic_reshaper.reshape(line))
            draw.text(
                (540, y),
                bidi_text,
                font=font,
                fill=(255, 255, 255, 255),
                stroke_width=6,
                stroke_fill=(0, 0, 0, 255),
                anchor="mm"
            )

    path = f"caption_{ch_idx}_{scene_idx}.png"
    img.save(path)
    return path

async def generate_voice(text, output_file):
    """توليد صوت عربي فصيح حماسي وسريع (+16%)"""
    import edge_tts
    communicate = edge_tts.Communicate(text, "ar-SA-HamedNeural", rate="+16%")
    await communicate.save(output_file)

def fetch_pexels_video(query, target_filename):
    """سحب مقطع فيديو حقيقي MP4 من Pexels API مع التحقق من سلامة الملف وحجمه"""
    if PEXELS_API_KEY:
        try:
            url = f"https://api.pexels.com/videos/search?query={query}&per_page=5&orientation=portrait"
            headers = {
                "Authorization": PEXELS_API_KEY,
                "User-Agent": "Mozilla/5.0"
            }
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200:
                data = res.json()
                videos = data.get("videos", [])
                if videos:
                    video_files = videos[0].get("video_files", [])
                    selected_file = None
                    for vf in video_files:
                        if vf.get("file_type") == "video/mp4":
                            if vf.get("width") == 1080 or vf.get("height") == 1920:
                                selected_file = vf["link"]
                                break
                    if not selected_file and video_files:
                        selected_file = video_files[0]["link"]

                    if selected_file:
                        v_resp = requests.get(selected_file, headers={"User-Agent": "Mozilla/5.0"}, stream=True, timeout=30)
                        if v_resp.status_code == 200:
                            with open(target_filename, "wb") as f:
                                for chunk in v_resp.iter_content(chunk_size=1024*1024):
                                    if chunk:
                                        f.write(chunk)
                            if os.path.exists(target_filename) and os.path.getsize(target_filename) > 100000:
                                print(f"🎥 تم بنجاح تحميل فيديو Pexels لموضوع: {query}")
                                return True
        except Exception as e:
            print(f"⚠️ تنبيه Pexels ({e})، سيتم الانتقال للبديل التلقائي.")
    return False

def build_gabriel_short(channel_name, ch_idx):
    """بناء فيديو شورتس كامل بلقطات فيديو حقيقية أو لقطات سينمائية متحركة بديلة"""
    size = (1080, 1920)
    data = CHANNELS_CONTENT[channel_name]
    scenes_data = data["scenes"]

    scenes = []
    temp_files = []

    for s_idx, item in enumerate(scenes_data):
        print(f"🎬 معالجة المشهد ({s_idx + 1}/{len(scenes_data)}): {item['query']}")

        # 1. الصوت
        aud_path = f"aud_{ch_idx}_{s_idx}.mp3"
        asyncio.run(generate_voice(item["hook"], aud_path))
        aud_clip = AudioFileClip(aud_path)
        duration = aud_clip.duration + 0.2
        temp_files.append(aud_path)

        # 2. تحميل مقطع الفيديو أو اللقطة السينمائية البديلة
        raw_video_path = f"stock_{ch_idx}_{s_idx}.mp4"
        success = fetch_pexels_video(item["query"], raw_video_path)

        video_clip = None
        if success:
            try:
                clip = VideoFileClip(raw_video_path).without_audio()
                if clip.duration < duration:
                    clip = clip.fx(vfx.loop, duration=duration)
                else:
                    clip = clip.subclip(0, duration)

                clip = clip.resize(height=1920)
                if clip.w < 1080:
                    clip = clip.resize(width=1080)
                video_clip = clip.crop(x_center=clip.w // 2, y_center=clip.h // 2, width=1080, height=1920)
                temp_files.append(raw_video_path)
            except Exception as e:
                print(f"⚠️ تعذر تشغيل المقطع ({e})، سيتم تشغيل اللقطة السينمائية البديلة.")
                video_clip = None

        # البديل السلس والمضمون 100% في حال عدم توفر الفيديو
        if video_clip is None:
            img_path = f"img_{ch_idx}_{s_idx}.jpg"
            try:
                r = requests.get(item["img_backup"], headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
                im = Image.open(io.BytesIO(r.content)).convert("RGB")
                im = im.resize(size, Image.Resampling.LANCZOS)
                im.save(img_path, "JPEG")
            except Exception:
                im = Image.new("RGB", size, color=(15, 23, 42))
                im.save(img_path, "JPEG")
            temp_files.append(img_path)

            video_clip = (ImageClip(img_path)
                          .set_duration(duration)
                          .resize(lambda t: 1 + 0.04 * t)
                          .crop(x_center=540, y_center=960, width=1080, height=1920))

        # 3. النص العريض المحدد في المنتصف (ستايل غابرييل عماد)
        caption_path = create_gabriel_caption(item["display"], ch_idx, s_idx, size=size)
        caption_clip = ImageClip(caption_path).set_duration(duration)
        temp_files.append(caption_path)

        # دمج المشهد
        scene = CompositeVideoClip([video_clip, caption_clip], size=size).set_audio(aud_clip)
        scenes.append(scene)

    final = concatenate_videoclips(scenes, method="compose")
    out_name = f"short_{ch_idx}.mp4"
    final.write_videofile(
        out_name,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        bitrate="2400k",
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
    """رفع الفيديو إلى Uguu للحصول على رابط مباشر فوري لـ Buffer"""
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
        print(f"⚠️ خطأ Uguu: {e}")

    # 2. Pixeldrain كخادم بديل
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
        print(f"⚠️ خطأ Pixeldrain: {e}")

    raise Exception("فشلت جميع خوادم الرفع المباشر.")

def publish_to_buffer_now(channel_id, title, desc, video_url):
    """نشر فوري ولحظي على القناة دون إرسال إلى قائمة الانتظار"""
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
    print(f"📋 إجمالي عدد القنوات المستهدفة: {len(CHANNELS_LIST)}")

    for idx, channel_id in enumerate(CHANNELS_LIST):
        niche_name = NICHE_KEYS[idx % len(NICHE_KEYS)]
        data = CHANNELS_CONTENT[niche_name]

        print(f"\n=======================================================")
        print(f"🎬 [القناة {idx+1}/{len(CHANNELS_LIST)}] إنتاج شورتس (Stock Videos & Gabriel Style): {niche_name}")
        print(f"=======================================================")

        video_path = build_gabriel_short(niche_name, idx)
        video_url = upload_video_file(video_path)

        print(f"⚡ نشر مباشر ولحظي إلى يوتيوب الآن...")
        publish_to_buffer_now(channel_id, data["title"], data["desc"], video_url)

        if os.path.exists(video_path):
            try: os.remove(video_path)
            except: pass

if __name__ == "__main__":
    main()
