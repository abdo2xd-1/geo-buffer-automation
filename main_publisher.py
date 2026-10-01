import os
import sys
import random
import asyncio
import io
import re
import json
import requests
import numpy as np

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
    CompositeAudioClip,
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

# تخصيص الهويات الصوتية باللهجة المصرية والعربية المناسبة
NICHE_PROFILES = {
    "أبعاد جغرافية": {
        "voice": "ar-EG-ShakirNeural",
        "rate": "+18%",
        "badge": "أبعاد جغرافية | أسرار الكوكب"
    },
    "مشاريع عملاقة": {
        "voice": "ar-EG-ShakirNeural",
        "rate": "+16%",
        "badge": "مشاريع عملاقة | معجزات هندسية"
    },
    "مسار": {
        "voice": "ar-EG-ShakirNeural",
        "rate": "+16%",
        "badge": "مسار | أسرار التجارة العالمية"
    }
}

NICHE_NAMES = list(NICHE_PROFILES.keys())

# 2. ملفات المؤثرات والموسيقى
BGM_TRACKS = [
    "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3?filename=dark-mystery-trailer-111586.mp3",
    "https://cdn.pixabay.com/download/audio/2022/03/15/audio_c8bbf72242.mp3?filename=suspense-cinematic-ambient-109012.mp3"
]
SFX_WHOOSH_URL = "https://cdn.pixabay.com/download/audio/2022/03/10/audio_c3527e30ec.mp3?filename=whoosh-6316.mp3"
SFX_IMPACT_URL = "https://cdn.pixabay.com/download/audio/2021/08/04/audio_12b0c7443c.mp3?filename=cinematic-boom-impact-114457.mp3"
SFX_POP_URL = "https://cdn.pixabay.com/download/audio/2022/03/24/audio_c29f6004b9.mp3?filename=pop-39222.mp3"

def ensure_audio_assets():
    assets = {
        "sfx_whoosh.mp3": SFX_WHOOSH_URL,
        "sfx_impact.mp3": SFX_IMPACT_URL,
        "sfx_pop.mp3": SFX_POP_URL,
        "bgm_track.mp3": random.choice(BGM_TRACKS)
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    for filename, url in assets.items():
        if not os.path.exists(filename):
            try:
                r = requests.get(url, headers=headers, timeout=20)
                if r.status_code == 200:
                    with open(filename, "wb") as f:
                        f.write(r.content)
            except Exception as e:
                print(f"⚠️ تعذر تنزيل {filename}: {e}")

# 3. بنك السيناريوهات بالعامية المصرية وأسلوب غابرييل عماد
FALLBACK_TOPICS_POOL = {
    "أبعاد جغرافية": [
        {
            "title": "[صدمة] بحيرة سرية في إفريقيا بتحول الطيور لحجارة فوراً !! 😱⚡",
            "desc": "تخيل إن في مكان حقيقي على كوكب الأرض بيحول الكائنات لتماثيل حجرية! لو اتعرض عليك مليون دولار لتعيش هناك أسبوع توافق؟ شاركنا رأيك في التعليقات 🌍⚡\n\n#أبعاد_جغرافية #غرائب #حقائق_مرعبة #هل_تعلم #Shorts",
            "scenes": [
                {"hook": "تخيل إن في بحيرة سرية في إفريقيا، أي طائر يلمس ميتها بيتحول لتمثال حجر فوراً!", "part1": "بحيرة النطرون", "part2": "بتحول الكائنات لحجر!", "coords": "02°25'S 36°00'E", "query": "red lake volcanic thermal", "img_backup": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1080&h=1920&fit=crop"},
                {"hook": "الموضوع مش سحر نهائي، درجة حرارة المية بتوصل لستين درجة، ومليانة أملاح كاوية بتحجر الأجسام!", "part1": "حرارة 60 درجة", "part2": "مياه كاوية قاتلة!", "coords": "02°25'S 36°00'E", "query": "boiling water volcanic thermal", "img_backup": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1080&h=1920&fit=crop"},
                {"hook": "وفي أبرد قرية في روسيا، الحرارة بتنزل لواحد وسبعين تحت الصفر، والرموش بتتجمد في ثانية واحدة!", "part1": "برودة -71 مئوية", "part2": "رموشك تتجمد بثانية!", "coords": "63°27'N 142°47'E", "query": "frozen siberia blizzard snow", "img_backup": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=1080&h=1920&fit=crop"},
                {"hook": "وحفرة بوابة جهنم في آسيا، مشتعلة بنيران غازية مستمرة وما انطفتش من أكتر من خمسين سنة!", "part1": "بوابة جهنم", "part2": "مشتعلة من 50 سنة!", "coords": "40°15'N 58°26'E", "query": "fire pit flames desert dark", "img_backup": "https://images.unsplash.com/photo-1517411032315-54ef2cb783bb?w=1080&h=1920&fit=crop"},
                {"hook": "لو اتعرض عليك مليون دولار لتعيش في الأماكن دي أسبوع.. توافق؟ اكتب في التعليقات لأن كل ده بدأ مع...", "part1": "مليون $ للمغامرة؟", "part2": "اكتب رأيك الآن!", "coords": "GLOBAL RADAR", "query": "space earth cinematic night", "img_backup": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1080&h=1920&fit=crop"}
            ]
        }
    ],
    "مشاريع عملاقة": [
        {
            "title": "[وحش ميكانيكي] أضخم آلة صنعتها البشرية حفرت تحت قاع البحر !! 🏗️😱",
            "desc": "آلة حفر وزنها 7000 طن غيرت ملامح الكوكب بالكامل! هل تعتقد أن التطور الهندسي هينقذ البشرية ولا هيدمرها؟ اكتب رأيك بالتعليقات 🏗️⚡\n\n#مشاريع_عملاقة #هندسة #بناء #ناطحات_سحاب #Shorts",
            "scenes": [
                {"hook": "أنت متخيل إن أضخم وحش ميكانيكي صنعته البشرية وزنه بيعادل سبعة آلاف طن كاملة؟", "part1": "وحش ميكانيكي مرعب", "part2": "وزنه 7000 طن!", "coords": "47°36'N 122°19'W", "query": "tunnel boring machine industrial", "img_backup": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=1080&h=1920&fit=crop"},
                {"hook": "الآلة دي بتفتت صخور الجبال وبتثبت جدران الخرسانة المسلحة تحت قاع الأرض في نفس الدقيقة!", "part1": "تفتت جبال الصخر", "part2": "وتبني جدار خرسانة!", "coords": "47°36'N 122°19'W", "query": "underground cave excavation drill", "img_backup": "https://images.unsplash.com/photo-1541888946425-d0fbb186c5f7?w=1080&h=1920&fit=crop"},
                {"hook": "وجسر ميلاو في فرنسا، أعمدته أعلى من برج إيفل ذات نفسه، والغيوم بتمر من تحت العربيات!", "part1": "أعلى من برج إيفل", "part2": "الغيوم تعبر تحته!", "coords": "44°05'N 03°01'E", "query": "huge bridge clouds aerial height", "img_backup": "https://images.unsplash.com/photo-1545558014-8692077e9b5c?w=1080&h=1920&fit=crop"},
                {"hook": "وهولندا بنت بوابات حديدية جبارة في قلب البحر بتحمي مدن كاملة من الغرق المحتوم!", "part1": "بوابات محيط عملاقة", "part2": "تحمي مدن كاملة!", "coords": "51°39'N 03°43'E", "query": "ocean storm sea wall barrier", "img_backup": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1080&h=1920&fit=crop"},
                {"hook": "تفتكر المشاريع دي هتقدر تحمي البشرية للأبد؟ اكتب في التعليقات لأن الفكرة دي كلها بدأت مع أول تصميم لـ...", "part1": "هل تحمينا للأبد؟", "part2": "شاركنا رأيك بالتعليقات!", "coords": "GLOBAL RADAR", "query": "modern skyscraper construction drone", "img_backup": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=1080&h=1920&fit=crop"}
            ]
        }
    ],
    "مسار": [
        {
            "title": "[كارثة عالمية] لو الممر ده اتقفل 24 ساعة، كوكب الأرض هيقف تماماً !! 🚢🚨",
            "desc": "أسرار خطوط الملاحة وسلاسل الإمداد العالمية التي تحرك تريليونات الدولارات! ما هو الممر الأكثر خطورة برأيك؟ شاركنا بالتعليقات 🚢⚡\n\n#مسار #تجارة #مضائق #اقتصاد #قناة_السويس #Shorts",
            "scenes": [
                {"hook": "أنت عارف إن لو مضيق هرمز اتقفل يوم واحد، خُمس نفط كوكب الأرض هيتوقف وأسعار الطاقة هتولع؟", "part1": "لو اتقفل يوم واحد", "part2": "خمس نفط العالم يقف!", "coords": "26°34'N 56°15'E", "query": "huge cargo ship ocean storm", "img_backup": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1080&h=1920&fit=crop"},
                {"hook": "وسفينة الحاويات الحديثة بتشيل أربعة وعشرين ألف حاوية ضخمة، بحجم ناطحة سحاب عائمة في البحر!", "part1": "24 ألف حاوية", "part2": "ناطحة سحاب عائمة!", "coords": "30°42'N 32°20'E", "query": "container terminal port aerial", "img_backup": "https://images.unsplash.com/photo-1578575437130-527eed3abbec?w=1080&h=1920&fit=crop"},
                {"hook": "وجنوح سفينة إيفر جيفن في قناة السويس، وقف تجارة عالمية بقيمة عشرة مليارات دولار كل أربع وعشرين ساعة!", "part1": "كارثة السويس", "part2": "10 مليارات $ باليوم!", "coords": "30°01'N 32°34'E", "query": "canal ship navigation traffic", "img_backup": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=1080&h=1920&fit=crop"},
                {"hook": "وتسعين بالمئة من كل شاشات وهدوم وموبايلات العالم، بتسافر في المحيطات قبل ما توصل لإيدك!", "part1": "90% من أجهزتك", "part2": "سافرت عبر المحيطات!", "coords": "01°16'N 103°50'E", "query": "freight vessel open sea waves", "img_backup": "https://images.unsplash.com/photo-1505705694340-019e1e335916?w=1080&h=1920&fit=crop"},
                {"hook": "تفتكر إيه هو أخطر شريان بحري في العالم كله؟ اكتب في التعليقات لأن الكارثة الحقيقية هتبدأ لو اتعطل...", "part1": "ما هو الممر الأخطر؟", "part2": "اكتب رأيك الآن!", "coords": "GLOBAL RADAR", "query": "ocean blue waves aerial drone", "img_backup": "https://images.unsplash.com/photo-1494412574643-ff11b0a5c1c3?w=1080&h=1920&fit=crop"}
            ]
        }
    ]
}

# 4. توليد المحتوى بالـ AI بأسلوب غابرييل عماد
def generate_ai_script(niche_name):
    if not GEMINI_API_KEY:
        return None
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        prompt = f"""
أنت كاتب سيناريو شورتس احترافي تصنع فيديوهات حماسية جداً بالعامية المصرية المتقنة على طريقة "غابرييل عماد".
المجال: {niche_name}. البذرة: {random.randint(1000, 99999)}.
الشروط:
1. العنوان يبدأ بصدمة داخل أقواس مثل [كارثة حقيقية] أو [صدمة مرعبة].
2. الأسلوب بالعامية المصرية المشوقة ("تخيل إن...", "أنت عارف إن...", "الحوار ده مش صدفة نهائي!").
3. المشهد 5 يطرح سؤالاً يثير الجدل والتعليقات (Comment-Bait)، وينتهي بعبارة رابطة مفتوحة تكملها الجملة الأولى تماماً (Seamless Loop).
4. توفير إحداثيات GPS تقديرية لكل مشهد (coords مثل "27°12'N 31°15'E").
5. الإخراج بصيغة JSON حصراً بدون ماركداون:
{{
  "title": "[صدمة] عنوان فجوة الفضول المصري",
  "desc": "وصف يوتيوب SEO مع هاشتاجات قوية",
  "scenes": [
    {{
      "hook": "الجملة المنطوقة بالعامية المصرية المشوقة",
      "part1": "كلمتين تمهيد",
      "part2": "كلمتين وصدمة أو رقم",
      "coords": "27°12'N 31°15'E",
      "query": "cinematic stock video query english",
      "img_backup": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1080&h=1920&fit=crop"
    }}
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
                return data
    except Exception:
        pass
    return None

def get_channel_content(niche_name):
    ai_content = generate_ai_script(niche_name)
    if ai_content:
        return ai_content
    pool = FALLBACK_TOPICS_POOL.get(niche_name, [])
    return random.choice(pool).copy()

def get_best_arabic_font(size=60):
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

def clean_arabic_text(text):
    return re.sub(r'[^\w\s\d\u0600-\u06FF!؟,\.\:\-\(\)\"\$]+', '', text).strip()

# 5. طبقة التظليل السينمائي المزدوج (Vignette)
def generate_vignette_overlay(path="vignette_overlay.png", size=(1080, 1920)):
    w, h = size
    vignette = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(vignette)
    for y in range(320):
        alpha = int(190 * (1 - y / 320)**1.4)
        draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))
    for y in range(h - 550, h):
        alpha = int(220 * ((y - (h - 550)) / 550)**1.4)
        draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))
    vignette.save(path)
    return path

# 6. الخريطة التفاعلية ورادار الأقمار الصناعية (Animated 3D Geo-HUD)
def generate_geo_hud_overlay(coords_text, path="geo_hud.png", size=(1080, 1920)):
    """توليد رادار أقمار صناعية وإحداثيات GPS استقصائية بتصميم Johnny Harris"""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font_small = get_best_arabic_font(size=24)

    # زاوية الرادار العلوية اليسرى
    rx, ry = 80, 240
    draw.ellipse([rx - 25, ry - 25, rx + 25, ry + 25], outline=(0, 255, 200, 180), width=2)
    draw.ellipse([rx - 12, ry - 12, rx + 12, ry + 12], fill=(0, 255, 200, 220))
    draw.line([(rx - 35, ry), (rx + 35, ry)], fill=(0, 255, 200, 140), width=1)
    draw.line([(rx, ry - 35), (rx, ry + 35)], fill=(0, 255, 200, 140), width=1)

    hud_label = f"GPS: {coords_text}"
    draw.text((rx + 42, ry - 12), hud_label, font=font_small, fill=(0, 255, 200, 240))

    img.save(path)
    return path

# 7. العدادات الرقمية والنصوص بنمط الكاريوكي التفاعلي
def create_micro_caption_with_counter(text_phrase, ch_idx, scene_idx, step_idx, is_highlight=False, counter_val=None, size=(1080, 1920)):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = get_best_arabic_font(size=64)

    has_raqm = features.check("raqm")
    display_text = clean_arabic_text(text_phrase)

    # إذا وجد عداد رقمي يتم استبدال الرقم في النص بالعداد المتحرك
    if counter_val is not None:
        display_text = re.sub(r'\d+', str(counter_val), display_text)

    if not has_raqm:
        import arabic_reshaper
        from bidi.algorithm import get_display
        display_text = get_display(arabic_reshaper.reshape(display_text))

    text_color = (255, 235, 59, 255) if is_highlight else (255, 255, 255, 255)
    y_pos = 960

    if has_raqm:
        draw.text((540, y_pos), display_text, font=font, fill=text_color, stroke_width=8, stroke_fill=(0, 0, 0, 255), anchor="mm", direction="rtl")
    else:
        draw.text((540, y_pos), display_text, font=font, fill=text_color, stroke_width=8, stroke_fill=(0, 0, 0, 255), anchor="mm")

    path = f"cap_{ch_idx}_{scene_idx}_{step_idx}_{counter_val}.png"
    img.save(path)
    return path

def generate_alert_banner(text="تحذير: حقائق سرية وصادمة", path="alert_banner.png", size=(1080, 1920)):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = get_best_arabic_font(size=32)

    has_raqm = features.check("raqm")
    display_text = clean_arabic_text(text)
    if not has_raqm:
        import arabic_reshaper
        from bidi.algorithm import get_display
        display_text = get_display(arabic_reshaper.reshape(display_text))

    bbox = draw.textbbox((0, 0), display_text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    y_center = 255
    pad_x, pad_y = 28, 10
    x1 = 540 - (tw // 2) - pad_x
    x2 = 540 + (tw // 2) + pad_x
    y1 = y_center - pad_y
    y2 = y_center + th + pad_y

    draw.rounded_rectangle([x1, y1, x2, y2], radius=20, fill=(220, 38, 38, 240), outline=(255, 255, 255, 210), width=2)
    draw.text((540, y_center), display_text, font=font, fill=(255, 255, 255, 255), anchor="mt", direction="rtl" if has_raqm else None)

    img.save(path)
    return path

def create_header_badge(badge_text, size=(1080, 1920)):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = get_best_arabic_font(size=36)

    has_raqm = features.check("raqm")
    display_badge = clean_arabic_text(badge_text)
    if not has_raqm:
        import arabic_reshaper
        from bidi.algorithm import get_display
        display_badge = get_display(arabic_reshaper.reshape(display_badge))

    bbox = draw.textbbox((0, 0), display_badge, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    y_center = 175
    pad_x, pad_y = 35, 14
    box_x1 = 540 - (text_w // 2) - pad_x
    box_x2 = 540 + (text_w // 2) + pad_x
    box_y1 = y_center - pad_y
    box_y2 = y_center + text_h + pad_y

    draw.rounded_rectangle([box_x1, box_y1, box_x2, box_y2], radius=28, fill=(10, 15, 25, 215), outline=(255, 215, 0, 180), width=2)
    draw.text((540, y_center), display_badge, font=font, fill=(255, 255, 255, 255), anchor="mt", direction="rtl" if has_raqm else None)

    path = "header_badge.png"
    img.save(path)
    return path

# 8. التشكيل الصوتي الدرامي عبر SSML مع سكتات محسوبة
async def generate_voice_ssml(text, output_file, voice_id, rate_val):
    import edge_tts
    # تحويل النص إلى SSML مع سكتة درامية خاطفة مدتها 180ms قبل الصدمة
    ssml_text = f"""
    <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='ar-EG'>
        <voice name='{voice_id}'>
            <prosody rate='{rate_val}'>
                <break time='180ms'/>
                {text}
                <break time='140ms'/>
            </prosody>
        </voice>
    </speak>
    """
    communicate = edge_tts.Communicate(ssml_text, voice_id)
    await communicate.save(output_file)

def fetch_pexels_video_pair(query, file_a, file_b):
    clips_saved = 0
    if PEXELS_API_KEY:
        try:
            url = f"https://api.pexels.com/videos/search?query={query}&per_page=6&orientation=portrait"
            headers = {"Authorization": PEXELS_API_KEY, "User-Agent": "Mozilla/5.0"}
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200:
                videos = res.json().get("videos", [])
                targets = [file_a, file_b]
                for v_item in videos:
                    if clips_saved >= 2: break
                    v_files = v_item.get("video_files", [])
                    link = None
                    for vf in v_files:
                        if vf.get("file_type") == "video/mp4":
                            if vf.get("width") == 1080 or vf.get("height") == 1920:
                                link = vf["link"]
                                break
                    if not link and v_files:
                        link = v_files[0]["link"]

                    if link:
                        v_resp = requests.get(link, headers={"User-Agent": "Mozilla/5.0"}, stream=True, timeout=25)
                        if v_resp.status_code == 200:
                            with open(targets[clips_saved], "wb") as f:
                                for chunk in v_resp.iter_content(chunk_size=1024*1024):
                                    if chunk: f.write(chunk)
                            if os.path.exists(targets[clips_saved]) and os.path.getsize(targets[clips_saved]) > 80000:
                                clips_saved += 1
        except Exception:
            pass
    return clips_saved

def create_subclip_processed(file_path, duration, target_size=(1080, 1920), is_hook=False):
    clip = VideoFileClip(file_path).without_audio()
    if clip.duration < duration:
        clip = clip.fx(vfx.loop, duration=duration)
    else:
        clip = clip.subclip(0, duration)

    clip = clip.resize(height=target_size[1])
    if clip.w < target_size[0]:
        clip = clip.resize(width=target_size[0])
    clip = clip.crop(x_center=clip.w // 2, y_center=clip.h // 2, width=target_size[0], height=target_size[1])
    clip = clip.fx(vfx.colorx, 1.15)

    if is_hook:
        clip = clip.resize(lambda t: 1.12 - 0.12 * min(1.0, t / 0.45) if t < 0.45 else (1.0 + 0.05 * (t / duration)))
    else:
        clip = clip.resize(lambda t: 1.0 + 0.05 * (t / duration))

    return clip

# 9. محرك خفض وتعلية الموسيقى تلقائياً (Smart Audio Ducking)
def apply_audio_ducking(bgm_clip, speech_intervals, total_dur):
    """خفض الموسيقى إلى 8% أثناء الكلام وتصعيدها إلى 22% في السكتات والفواصل"""
    def volume_filter(gf, t):
        vol = np.full_like(t, 0.22, dtype=np.float32)
        for st, en in speech_intervals:
            mask = (t >= (st - 0.05)) & (t <= (en + 0.05))
            vol[mask] = 0.08
        samples = gf(t)
        return samples * vol[:, None]
    return bgm_clip.fl(volume_filter)

def build_viral_short(channel_name, content_data, ch_idx):
    ensure_audio_assets()
    size = (1080, 1920)
    profile = NICHE_PROFILES.get(channel_name, {"voice": "ar-EG-ShakirNeural", "rate": "+18%", "badge": "أبعاد جغرافية"})
    scenes_data = content_data["scenes"]

    scenes = []
    temp_files = []
    scene_start_times = []
    cut_transition_times = []
    pop_sfx_times = []
    speech_intervals = []
    current_time = 0.0
    voice_audio_clips = []

    for s_idx, item in enumerate(scenes_data):
        print(f"🎬 معالجة المشهد ({s_idx + 1}/{len(scenes_data)}): {item.get('query')}")

        aud_path = f"aud_{ch_idx}_{s_idx}.mp3"
        asyncio.run(generate_voice_ssml(item["hook"], aud_path, profile["voice"], profile["rate"]))
        aud_clip = AudioFileClip(aud_path)
        duration = aud_clip.duration + 0.15
        temp_files.append(aud_path)

        scene_start_times.append(current_time)
        speech_intervals.append((current_time, current_time + aud_clip.duration))
        voice_audio_clips.append(aud_clip.set_start(current_time))

        half_dur = duration / 2.0
        file_a = f"vid_a_{ch_idx}_{s_idx}.mp4"
        file_b = f"vid_b_{ch_idx}_{s_idx}.mp4"
        saved_count = fetch_pexels_video_pair(item.get("query", "nature"), file_a, file_b)

        subclips = []
        is_first_scene = (s_idx == 0)

        if saved_count >= 1:
            try:
                subclips.append(create_subclip_processed(file_a, half_dur, size, is_hook=is_first_scene))
                temp_files.append(file_a)
            except Exception:
                subclips = []

        if saved_count >= 2 and len(subclips) == 1:
            try:
                subclips.append(create_subclip_processed(file_b, duration - half_dur, size, is_hook=False))
                temp_files.append(file_b)
                cut_transition_times.append(current_time + half_dur)
            except Exception:
                pass

        if len(subclips) < 2:
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

            img_clip = (ImageClip(img_path)
                        .set_duration(duration)
                        .resize(lambda t: 1.0 + 0.05 * (t / duration))
                        .crop(x_center=540, y_center=960, width=1080, height=1920)
                        .fx(vfx.colorx, 1.15))
            scene_bg = img_clip
        else:
            scene_bg = concatenate_videoclips(subclips, method="compose")

        # إضافة رادار الأقمار الصناعية والإحداثيات
        coords_val = item.get("coords", "27°12'N 31°15'E")
        geo_hud_path = generate_geo_hud_overlay(coords_val, path=f"hud_{ch_idx}_{s_idx}.png", size=size)
        temp_files.append(geo_hud_path)
        geo_hud_clip = ImageClip(geo_hud_path).set_duration(duration).set_opacity(0.85)

        # العدادات الرقمية وتوهج الكلمات
        part1_text = item.get("part1", "معلومة لا تصدق")
        part2_text = item.get("part2", "حقيقة صادمة")

        # فحص إذا كان هناك رقم لتشغيل العداد المتحرك
        num_match = re.search(r'\d+', part2_text)
        cap_clips_for_scene = []

        cap_file_1 = create_micro_caption_with_counter(part1_text, ch_idx, s_idx, 0, is_highlight=False, size=size)
        temp_files.append(cap_file_1)
        cap_clip_1 = (ImageClip(cap_file_1)
                      .set_duration(half_dur)
                      .resize(lambda t: 1.10 - 0.10 * min(1.0, t / 0.15) if t < 0.15 else 1.0))
        cap_clips_for_scene.append(cap_clip_1)

        if num_match:
            target_num = int(num_match.group(0))
            counter_frames = []
            steps = 4
            for step_i in range(steps):
                current_cnt = int(target_num * ((step_i + 1) / steps))
                cf_path = create_micro_caption_with_counter(part2_text, ch_idx, s_idx, 1, is_highlight=True, counter_val=current_cnt, size=size)
                temp_files.append(cf_path)
                f_dur = (duration - half_dur) / steps
                c_clip = ImageClip(cf_path).set_duration(f_dur).set_start(half_dur + (step_i * f_dur))
                counter_frames.append(c_clip)
            cap_clips_for_scene.extend(counter_frames)
        else:
            cap_file_2 = create_micro_caption_with_counter(part2_text, ch_idx, s_idx, 1, is_highlight=True, size=size)
            temp_files.append(cap_file_2)
            cap_clip_2 = (ImageClip(cap_file_2)
                          .set_duration(duration - half_dur)
                          .set_start(half_dur)
                          .resize(lambda t: 1.10 - 0.10 * min(1.0, t / 0.15) if t < 0.15 else 1.0))
            cap_clips_for_scene.append(cap_clip_2)

        pop_sfx_times.append(current_time)
        pop_sfx_times.append(current_time + half_dur)

        scene = CompositeVideoClip([scene_bg, geo_hud_clip] + cap_clips_for_scene, size=size).set_duration(duration)
        scenes.append(scene)
        current_time += duration

    final_video = concatenate_videoclips(scenes, method="compose")
    total_duration = final_video.duration

    # تجهيز الطبقات العلوية
    overlay_clips = [final_video]

    # أ. التظليل السينمائي المزدوج
    vignette_path = generate_vignette_overlay()
    temp_files.append(vignette_path)
    vignette_clip = ImageClip(vignette_path).set_duration(total_duration)
    overlay_clips.append(vignette_clip)

    # ب. شريط التقدم التفاعلي
    progress_bar = (ColorClip(size=(1080, 14), color=(255, 235, 59))
                    .set_duration(total_duration)
                    .resize(lambda t: (max(2, int(1080 * min(1.0, max(0.0, t / total_duration)))), 14))
                    .set_position((0, 1920 - 20)))
    overlay_clips.append(progress_bar)

    # ج. الشارة العلوية الموثقة
    badge_path = create_header_badge(profile["badge"], size=size)
    temp_files.append(badge_path)
    badge_clip = ImageClip(badge_path).set_duration(total_duration)
    overlay_clips.append(badge_clip)

    # د. شريط التحذير النبضي
    alert_path = generate_alert_banner("تحذير: حقائق سرية وصادمة")
    temp_files.append(alert_path)
    alert_clip = ImageClip(alert_path).set_duration(1.2).resize(lambda t: 1.08 - 0.08 * min(1.0, t / 0.2) if t < 0.2 else 1.0)
    overlay_clips.append(alert_clip)

    # هـ. الوميض الأبيض الخاطف
    white_flash = ColorClip(size=size, color=(255, 255, 255)).set_duration(0.10).set_opacity(0.85)
    overlay_clips.append(white_flash)

    final_video = CompositeVideoClip(overlay_clips, size=size)

    # 10. دمج الصوت وخفض الموسيقى الذكي (Audio Ducking)
    audio_layers = voice_audio_clips

    if os.path.exists("sfx_impact.mp3"):
        try:
            impact_sfx = AudioFileClip("sfx_impact.mp3").volumex(0.75).set_start(0.0)
            audio_layers.append(impact_sfx)
        except Exception:
            pass

    if os.path.exists("sfx_whoosh.mp3"):
        try:
            for ct in (scene_start_times[1:] + cut_transition_times):
                whoosh_sfx = AudioFileClip("sfx_whoosh.mp3").volumex(0.35).set_start(max(0, ct - 0.12))
                audio_layers.append(whoosh_sfx)
        except Exception:
            pass

    if os.path.exists("sfx_pop.mp3"):
        try:
            for pt in pop_sfx_times:
                pop_sfx = AudioFileClip("sfx_pop.mp3").volumex(0.22).set_start(pt)
                audio_layers.append(pop_sfx)
        except Exception:
            pass

    if os.path.exists("bgm_track.mp3"):
        try:
            bgm = AudioFileClip("bgm_track.mp3")
            if bgm.duration < total_duration:
                bgm = bgm.fx(vfx.loop, duration=total_duration)
            else:
                bgm = bgm.subclip(0, total_duration)
            # تطبيق الـ Audio Ducking الذكي
            ducked_bgm = apply_audio_ducking(bgm, speech_intervals, total_duration)
            audio_layers.insert(0, ducked_bgm)
        except Exception:
            pass

    composite_audio = CompositeAudioClip(audio_layers).set_duration(total_duration)
    final_video = final_video.set_audio(composite_audio)

    out_name = f"short_{ch_idx}.mp4"
    final_video.write_videofile(
        out_name,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        bitrate="2600k",
        threads=4,
        preset="ultrafast"
    )

    for f in temp_files:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

    return out_name

def upload_video_file(file_path):
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
    except Exception:
        pass

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
        print(f"🚀 [القناة {idx+1}/{len(CHANNELS_LIST)}] إنتاج شورتس بمحرك Vox & Gabriel Emad: {niche_name}")
        print(f"=======================================================")

        content_data = get_channel_content(niche_name)
        video_path = build_viral_short(niche_name, content_data, idx)
        video_url = upload_video_file(video_path)

        print(f"⚡ نشر مباشر ولحظي إلى يوتيوب الآن...")
        publish_to_buffer_now(channel_id, content_data["title"], content_data["desc"], video_url)

        if os.path.exists(video_path):
            try: os.remove(video_path)
            except: pass

if __name__ == "__main__":
    main()
