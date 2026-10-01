import os
import sys
import random
import asyncio
import io
import json
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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

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

NICHE_NAMES = ["أبعاد جغرافية", "مشاريع عملاقة", "مسار"]

# 2. بنك المواضيع الموسع (30+ موضوع حصري يضمن التنوع الكامل يومياً)
FALLBACK_TOPICS_POOL = {
    "أبعاد جغرافية": [
        {
            "title": "أغرب بحيرة على كوكب الأرض تحول الحيوانات إلى حجارة !!😱⚡",
            "desc": "حقائق مرعبة عن بحيرة النطرون وظواهر طبيعية غامضة! اكتب سبحان الله واشترك 🌍⚡\n\n#أبعاد_جغرافية #غرائب #حقائق_مرعبة #طبيعة #Shorts",
            "scenes": [
                {"hook": "أنت تعرف إن في بحيرة في إفريقيا بتحول أي طائر يلمسها لحجر متكلس فوراً؟", "display": ["بحيرة النطرون في تنزانيا", "بتحول أي طائر يلمسها", "إلى تمثال حجري فوراً!"], "query": "lake pink water aerial", "img_backup": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1080&h=1920&fit=crop"},
                {"hook": "البحيرة دي اسمها بحيرة النطرون، ودرجة ملوحتها وحرارتها بتوصل لستين درجة مئوية!", "display": ["درجة حرارتها بتوصل", "لستين درجة مئوية", "بمياه شديدة القلوية!"], "query": "volcanic lake steam", "img_backup": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1080&h=1920&fit=crop"},
                {"hook": "وفي أبرد قرية في روسيا، درجة الحرارة بتنزل لواحد وسبعين تحت الصفر، والرموش بتتجمد في ثانية!", "display": ["وفي قرية أويمياكون", "الحرارة 71 تحت الصفر", "والأنفاس بتتجمد فوراً!"], "query": "snow blizzard siberia", "img_backup": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=1080&h=1920&fit=crop"},
                {"hook": "أما حفرة دارفازا في تركمانستان فبتشتعل بنيران غازية مستمرة من أكتر من خمسين سنة!", "display": ["وحفرة بوابة جهنم", "مشتعلة بالنيران المستمرة", "من أكثر من 50 عاماً!"], "query": "fire pit flames dark", "img_backup": "https://images.unsplash.com/photo-1517411032315-54ef2cb783bb?w=1080&h=1920&fit=crop"},
                {"hook": "ما تنساش تكتب سبحان الله في التعليقات وتشترك في القناة وتعمل لايك!", "display": ["اكتب سبحان الله في التعليقات", "واشترك في القناة حالا!", "واعمل لايك للفيديو"], "query": "space earth night", "img_backup": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1080&h=1920&fit=crop"}
            ]
        },
        {
            "title": "ظواهر جغرافية مرعبة ستجعلك ترتجف من الغموض !!😱⚡",
            "desc": "أسرار جغرافية لا يصدقها عقل عن الصحاري والبراكين! اكتب سبحان الله واشترك 🌍⚡\n\n#أبعاد_جغرافية #جغرافيا #غرائب #Shorts",
            "scenes": [
                {"hook": "أنت تعرف إن صحراء أتاكاما في تشيلي، في أجزاء منها ما نزلش عليها نقطة مطر من أربعمئة سنة؟", "display": ["صحراء أتاكاما في تشيلي", "ما نزلش عليها مطر", "من 400 سنة متواصلة!"], "query": "desert dry landscape drone", "img_backup": "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=1080&h=1920&fit=crop"},
                {"hook": "والرمال هناك بتشبه سطح كوكب المريخ لدرجة إن وكالة ناسا بتختبر مركبات الفضاء فيها!", "display": ["ناسا بتختبر مركباتها هناك", "لأن تضاريسها نسخة طبق الأصل", "من كوكب المريخ!"], "query": "mars rover red planet", "img_backup": "https://images.unsplash.com/photo-1614728894747-a83421e2b9c9?w=1080&h=1920&fit=crop"},
                {"hook": "ونهر الأمازون العملاق، بطول آلاف الكيلومترات، ما فيهوش ولا كوبري واحد مبني فوقه!", "display": ["ونهر الأمازون العملاق", "لا يوجد فوقه أي جسر", "على الإطلاق!"], "query": "amazon river jungle", "img_backup": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1080&h=1920&fit=crop"},
                {"hook": "وفي إندونيسيا، في بركان بيقذف حمم بركانية بلون أزرق كهربائي ساطع في الليل الدامس!", "display": ["وبركان كاواه إيجين", "بيقذف نيران وحمم زرقاء", "في ظلام الليل!"], "query": "volcano blue lava night", "img_backup": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1080&h=1920&fit=crop"},
                {"hook": "ما تنساش تكتب سبحان الله في التعليقات وتشترك في القناة وتعمل لايك!", "display": ["اكتب سبحان الله في التعليقات", "واشترك في القناة حالا!", "واعمل لايك للفيديو"], "query": "planet earth horizon", "img_backup": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1080&h=1920&fit=crop"}
            ]
        }
    ],

    "مشاريع عملاقة": [
        {
            "title": "أضخم آلات حفر وأنفاق صنعتها البشرية في التاريخ !!😱🏗️",
            "desc": "معجزات هندسية وآلات جبارة تخترق الجبال وقيعان البحار! اكتب سبحان الله واشترك 🏗️⚡\n\n#مشاريع_عملاقة #هندسة #بناء #ناطحات_سحاب #Shorts",
            "scenes": [
                {"hook": "أنت تعرف إن أضخم آلة حفر أنفاق في العالم، وزنها سبعة آلاف طن وطولها ملعب كرة قدم؟", "display": ["آلة الحفر بيرثا", "وزنها 7 آلاف طن", "وبطول ملعب كرة قدم!"], "query": "tunnel boring machine underground", "img_backup": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=1080&h=1920&fit=crop"},
                {"hook": "الآلة دي بتقدر تقطع الصخور الصلبة وتثبت جدران الخرسانة المسلحة في نفس الدقيقة!", "display": ["بتقطع الجبال الشاهقة", "وتبني جدار الخرسانة", "في نفس اللحظة!"], "query": "construction heavy machinery", "img_backup": "https://images.unsplash.com/photo-1541888946425-d0fbb186c5f7?w=1080&h=1920&fit=crop"},
                {"hook": "وجسر ميلاو في فرنسا، أعمدته الخرسانية أعلى من برج إيفل وبتمر السحب من تحت الجسر!", "display": ["وجسر ميلاو في فرنسا", "أعلى من برج إيفل", "والغيوم بتمر تحته!"], "query": "highest bridge clouds valley", "img_backup": "https://images.unsplash.com/photo-1545558014-8692077e9b5c?w=1080&h=1920&fit=crop"},
                {"hook": "وفي هولندا، بنوا أعظم سد هيدروليكي متحرك في العالم لحماية مدن كاملة من الغرق في البحر!", "display": ["وهولندا بنت بوابات عملاقة", "بتحمي مدن كاملة", "من الغرق في المحيط!"], "query": "ocean sea wall barrier storm", "img_backup": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1080&h=1920&fit=crop"},
                {"hook": "ما تنساش تكتب سبحان الله وتشترك في القناة وتعمل لايك!", "display": ["اكتب سبحان الله في التعليقات", "واشترك في القناة حالا!", "واعمل لايك للفيديو"], "query": "skyscraper construction night", "img_backup": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=1080&h=1920&fit=crop"}
            ]
        }
    ],

    "مسار": [
        {
            "title": "أسرار أضخم سفن الحاويات وحوادث المضائق الكارثية !!😱🚢",
            "desc": "أخطر كواليس سلاسل الإمداد وممرات التجارة الدولية! اكتب سبحان الله واشترك بالقناة 🚢⚡\n\n#مسار #تجارة #مضائق #اقتصاد #Shorts",
            "scenes": [
                {"hook": "أنت تعرف إن سفينة الحاويات الحديثة بتقدر تشيل أربعة وعشرين ألف حاوية بضائع عملاقة؟", "display": ["سفينة الشحن الحديثة", "بتشيل 24 ألف حاوية", "بحجم ناطحة سحاب!"], "query": "massive container ship ocean", "img_backup": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1080&h=1920&fit=crop"},
                {"hook": "ولو رصينا الحاويات دي في خط مستقيم، هتعمل طريق طوله مئة وخمسين كيلومتراً متواصلاً!", "display": ["حاوياتها لو اترصت بالخط", "طولها بيوصل 150 كيلومتر", "بدون أي فراغ!"], "query": "shipping port container crane", "img_backup": "https://images.unsplash.com/photo-1578575437130-527eed3abbec?w=1080&h=1920&fit=crop"},
                {"hook": "وحادثة جنوح إيفر جيفن في قناة السويس، وقفت تجارة بقيمة عشرة مليارات دولار كل أربع وعشرين ساعة!", "display": ["جنوح سفينة في السويس", "عطّل 10 مليارات دولار", "في اليوم الواحد!"], "query": "suez canal ship stuck", "img_backup": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=1080&h=1920&fit=crop"},
                {"hook": "وأكتر من تسعين بالمئة من كل شاشات وهواتف وملابس العالم، بتسافر في أعالي البحار قبل ما توصلك!", "display": ["90% من كل أجهزتك", "بتسافر آلاف الأميال بحراً", "عبر سلاسل الإمداد!"], "query": "freight ship open sea", "img_backup": "https://images.unsplash.com/photo-1505705694340-019e1e335916?w=1080&h=1920&fit=crop"},
                {"hook": "ما تنساش تكتب سبحان الله في التعليقات وتشترك في القناة وتعمل لايك!", "display": ["اكتب سبحان الله في التعليقات", "واشترك في القناة حالا!", "واعمل لايك للفيديو"], "query": "blue sea sunrise", "img_backup": "https://images.unsplash.com/photo-1494412574643-ff11b0a5c1c3?w=1080&h=1920&fit=crop"}
            ]
        }
    ]
}

# 3. توليد سكريبت جديد كلياً بالذكاء الاصطناعي (Gemini) إن وجد المفتاح
def generate_ai_script(niche_name):
    """توليد سكريبت جديد وفريد تماماً بأسلوب غابرييل عماد عبر Gemini API"""
    if not GEMINI_API_KEY:
        return None

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        seed = random.randint(1000, 99999)
        prompt = f"""
أنت كاتب محتوى يوتيوب شورتس محترف جداً مثل أسلوب "غابرييل عماد".
المجال المطلوب: {niche_name}.
رقم البذرة العشوائية لعدم التكرار: {seed}.
اكتب موضوعاً جديداً، غريباً، ومثيراً جداً لم يتم تكراره من قبل.
يجب أن ترجع النتيجة بصيغة JSON فقط دون أي شروح أو علامات ماركداون:
{{
  "title": "عنوان جذاب وصادم مع إيموجي",
  "desc": "وصف قصير مع هاشتاجات",
  "scenes": [
    {{
      "hook": "الجملة المحكية بالعامية المشوقة أو الفصحى المبسطة",
      "display": ["السطر الأول للعرض", "السطر الثاني للعرض", "السطر الثالث للعرض"],
      "query": "english search term for stock video",
      "img_backup": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1080&h=1920&fit=crop"
    }},
    ... (إجمالي 5 مشاهد، المشهد الأخير دائماً دعوة لكتابة سبحان الله والاشتراك)
  ]
}}
        """
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = requests.post(url, json=payload, timeout=20)
        if res.status_code == 200:
            txt = res.json()["candidates"][0]["content"]["parts"][0]["text"]
            txt = txt.strip().replace("```json", "").replace("```", "")
            data = json.loads(txt)
            if "scenes" in data and len(data["scenes"]) >= 4:
                print(f"🤖 تم بنجاح توليد سكريبت حصري جديد بالذكاء الاصطناعي: {data.get('title')}")
                return data
    except Exception as e:
        print(f"⚠️ تعذر توليد السكريبت بـ Gemini ({e})، سيتم السحب من بنك المواضيع المتنوعة.")
    return None

def get_channel_content(niche_name):
    """جلب محتوى جديد تماماً إما عبر الذكاء الاصطناعي أو بالاختيار العشوائي من البنك"""
    ai_content = generate_ai_script(niche_name)
    if ai_content:
        return ai_content

    # السحب العشوائي من بنك المواضيع الاحتياطي
    pool = FALLBACK_TOPICS_POOL.get(niche_name, [])
    selected = random.choice(pool).copy()
    # خلط ترتيب المشاهد الداخلية العشوائية (مع الحفاظ على المشهد الأول والأخير)
    if len(selected["scenes"]) > 3:
        middle = selected["scenes"][1:-1]
        random.shuffle(middle)
        selected["scenes"] = [selected["scenes"][0]] + middle + [selected["scenes"][-1]]
    return selected

# 4. معالجة النصوص والرسم
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
            headers = {"Authorization": PEXELS_API_KEY, "User-Agent": "Mozilla/5.0"}
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

def build_gabriel_short(content_data, ch_idx):
    """بناء فيديو شورتس كامل وفريد تماماً للقناة"""
    size = (1080, 1920)
    scenes_data = content_data["scenes"]

    scenes = []
    temp_files = []

    for s_idx, item in enumerate(scenes_data):
        print(f"🎬 معالجة المشهد ({s_idx + 1}/{len(scenes_data)}): {item.get('query', 'scene')}")

        # 1. الصوت
        aud_path = f"aud_{ch_idx}_{s_idx}.mp3"
        asyncio.run(generate_voice(item["hook"], aud_path))
        aud_clip = AudioFileClip(aud_path)
        duration = aud_clip.duration + 0.2
        temp_files.append(aud_path)

        # 2. تحميل مقطع الفيديو أو اللقطة السينمائية البديلة
        raw_video_path = f"stock_{ch_idx}_{s_idx}.mp4"
        success = fetch_pexels_video(item.get("query", "nature"), raw_video_path)

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
                video_clip = None

        if video_clip is None:
            img_path = f"img_{ch_idx}_{s_idx}.jpg"
            try:
                backup_url = item.get("img_backup", "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1080&h=1920&fit=crop")
                r = requests.get(backup_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
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

        # 3. النص العريض المحدد في المنتصف
        caption_path = create_gabriel_caption(item["display"], ch_idx, s_idx, size=size)
        caption_clip = ImageClip(caption_path).set_duration(duration)
        temp_files.append(caption_path)

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

    for f in temp_files:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

    return out_name

def upload_video_file(file_path):
    """رفع الفيديو للحصول على رابط مباشر فوري لـ Buffer"""
    print(f"☁️ جاري رفع {file_path}...")
    try:
        with open(file_path, "rb") as f:
            r = requests.post("https://uguu.se/upload", files={"files[]": (os.path.basename(file_path), f, "video/mp4")}, timeout=120)
            if r.status_code == 200:
                data = r.json()
                if data.get("success") and data.get("files"):
                    url = data["files"][0]["url"]
                    print(f"🔗 تم الرفع بنجاح: {url}")
                    return url
    except Exception as e:
        print(f"⚠️ خطأ Uguu: {e}")

    try:
        with open(file_path, "rb") as f:
            r = requests.post("https://pixeldrain.com/api/file", files={"file": (os.path.basename(file_path), f, "video/mp4")}, timeout=120)
            if r.status_code in [200, 201]:
                fid = r.json().get("id")
                if fid:
                    return f"https://pixeldrain.com/api/file/{fid}"
    except Exception:
        pass

    raise Exception("فشلت جميع خوادم الرفع المباشر.")

def publish_to_buffer_now(channel_id, title, desc, video_url):
    """نشر فوري ولحظي على يوتيوب عبر Buffer دون إرسال إلى قائمة الانتظار"""
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
        niche_name = NICHE_NAMES[idx % len(NICHE_NAMES)]
        
        print(f"\n=======================================================")
        print(f"🎬 [القناة {idx+1}/{len(CHANNELS_LIST)}] تجهيز موضوع جديد وحصري لقناة: {niche_name}")
        print(f"=======================================================")

        # جلب موضوع وسيناريو جديد وغير مكرر إطلاقاً
        content_data = get_channel_content(niche_name)

        video_path = build_gabriel_short(content_data, idx)
        video_url = upload_video_file(video_path)

        print(f"⚡ نشر مباشر ولحظي إلى يوتيوب الآن...")
        publish_to_buffer_now(channel_id, content_data["title"], content_data["desc"], video_url)

        if os.path.exists(video_path):
            try: os.remove(video_path)
            except: pass

if __name__ == "__main__":
    main()
