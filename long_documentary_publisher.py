import os
import sys
import random
import asyncio
import json
import re
import subprocess
import requests
import PIL.Image

# ترقيع التوافق بين Pillow و MoviePy
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

# 1. المفاتيح والمجالات
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

NICHE_NAMES = ["أبعاد جغرافية", "مشاريع عملاقة", "مسار"]

# بنك سيناريوهات احتياطي متكامل للـ 8 دقائق في حال انقطاع الـ API
FALLBACK_LONG_DOCS = {
    "أبعاد جغرافية": {
        "title": "أسرار الممرات المائية الأخطر في تاريخ كوكب الأرض",
        "desc": "تحقيق وثائقي استقصائي شامل يكشف كواليس أخطر المضائق والممرات الملاحية.\n\n#أبعاد_جغرافية #وثائقي #جغرافيا #مضائق",
        "chapters": [
            {
                "chapter_title": "الفصل الأول: شريان العالم المهدد",
                "scenes": [
                    {
                        "narration": "من آلاف السنين، وخريطة كوكب الأرض بتتحكم فيها ممرات مائية ضيقة جداً، قادرة في ثواني معدودة تعطل حركة الكوكب كله.",
                        "query": "aerial ocean strait cargo ship",
                        "lower_third": "📍 مضيق هرمز - الخليج العربي"
                    },
                    {
                        "narration": "المضيق ده بيعبر منه خُمس استهلاك العالم من الطاقة يومياً، يعني أي تهديد أمني صغير هنا معناه شلل مباشر في مصانع ومطارات العالم.",
                        "query": "oil tanker ocean cinematic drone",
                        "lower_third": "🛢️ 20% من نفط الكوكب يومياً"
                    },
                    {
                        "narration": "والسؤال اللي شاغل كل أجهزة المخابرات الدولية: إيه السيناريو اللي ممكن يحصل لو ممر زي ده اتقفل تماماً؟",
                        "query": "military ship naval ocean patrol",
                        "lower_third": "⚠️ التهديد الاستراتيجي الأخطر"
                    }
                ]
            },
            {
                "chapter_title": "الفصل الثاني: معجزة الحفر وتاريخ السويس",
                "scenes": [
                    {
                        "narration": "علشان نفهم حجم الكارثة دي، لازم نرجع بالزمن لنقطة التحول الأكبر في الملاحة البحرية: قناة السويس المصرية.",
                        "query": "suez canal aerial cargo navigation",
                        "lower_third": "📍 قناة السويس - مصر"
                    },
                    {
                        "narration": "حفر القناة كان معجزة بشرية دفع فيها مئات الآلاف أرواحهم، علشان يختصروا رحلة الدوران حول قارة إفريقيا بآلاف الأميال.",
                        "query": "historical desert excavation workers",
                        "lower_third": "⏳ اختصار 7000 كيلومتر بحري"
                    },
                    {
                        "narration": "لكن هل الطرق البديلة زي طريق رأس الرجاء الصالح ممكن تكون حل عملي في الأزمات؟ الإجابة بتكشف عنها لغة الأرقام والتكاليف.",
                        "query": "cape of good hope stormy ocean",
                        "lower_third": "🌊 طريق رأس الرجاء الصالح"
                    }
                ]
            },
            {
                "chapter_title": "الفصل الثالث: أزمة إيفر جيفن ولحظة الصدمة",
                "scenes": [
                    {
                        "narration": "في مارس 2021، سفينة حاويات عملاقة بحجم ناطحة سحاب انحرفت عن مسارها، وعلقت في الرمال لتوقف حركة التجارة الدولية تماماً.",
                        "query": "massive container vessel stuck canal",
                        "lower_third": "🚨 حادثة جنوح إيفر جيفن"
                    },
                    {
                        "narration": "كل ساعة تأخير كانت بتكلف الاقتصاد العالمي 400 مليون دولار، وطوابير السفن امتدت في البحر الأحمر والبحر المتوسط لأيام طويلة.",
                        "query": "cargo fleet anchored open sea",
                        "lower_third": "💸 خسائر: 400 مليون $ كل ساعة"
                    },
                    {
                        "narration": "العالم وقتها أدرك حقيقة مرعبة: سلاسل الإمداد العالمية كلها معلقة على خيط رفيع جداً قابل للقطع في أي لحظة.",
                        "query": "container port cranes time lapse",
                        "lower_third": "📦 شلل سلاسل الإمداد العالمية"
                    }
                ]
            },
            {
                "chapter_title": "الفصل الرابع: صراع الممرات البديلة والقطب الشمالي",
                "scenes": [
                    {
                        "narration": "ومع ذوبان الجليد في القطب الشمالي، ظهر ممر جديد بيتصارع عليه الكبار: طريق الملاحة الشمالي عبر المياه الروسية.",
                        "query": "arctic icebreaker ship ice frozen",
                        "lower_third": "❄️ طريق الملاحة الشمالي - القطب"
                    },
                    {
                        "narration": "روسيا والصين بيستثمروا مليارات الدولارات في كاسحات الجليد النووية، علشان يفتحوا طريق أسرع بين آسيا وأوروبا بعيداً عن نقاط الاختناق التقليدية.",
                        "query": "nuclear icebreaker drone arctic",
                        "lower_third": "🚢 أسطول كاسحات الجليد النووية"
                    },
                    {
                        "narration": "لكن المخاطر المناخية والتكاليف اللوجستية الضخمة لسه بتخلي الممر ده تحدي هندسي وجغرافي معقد جداً.",
                        "query": "glaciers melting arctic cold ocean",
                        "lower_third": "🧭 تحديات البيئة واللوجستيات"
                    }
                ]
            },
            {
                "chapter_title": "الفصل الخامس: صراع المستقبل والكلمة الأخيرة",
                "scenes": [
                    {
                        "narration": "الصراع في القرن الحادي والعشرين مش مجرد صراع على الأراضي، ده صراع على التحكم في الشرايين اللي بتغذي العالم بكل احتياجاته.",
                        "query": "world map satellite digital network",
                        "lower_third": "🌐 خريطة التجارة للقرن 21"
                    },
                    {
                        "narration": "من هرمز لباب المندب لقناة بنما، كل نقطة مائية على الكوكب أصبحت ساحة شطرنج تديرها القوى العظمى بكل حذر.",
                        "query": "panama canal locks ship crossing",
                        "lower_third": "📍 قناة بنما - المحيط الهادئ"
                    },
                    {
                        "narration": "تفتكروا إيه الممر المائي اللي ممكن يشهد الأزمة القادمة؟ اكتبوا لنا رأيكم في التعليقات واشتركوا في القناة لمتابعة تحقيقاتنا القادمة.",
                        "query": "cinematic sunset ocean horizon drone",
                        "lower_third": "💬 شاركنا رأيك في التعليقات"
                    }
                ]
            }
        ]
    }
}

# 2. إعداد الخط العربي
def get_best_arabic_font(size=44):
    for p in [
        "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoKufiArabic-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()

def clean_arabic(text):
    return re.sub(r'[^\w\s\d\u0600-\u06FF!؟,\.\:\-\(\)\"\$]+', '', text).strip()

# 3. محرك الاستدعاء الذكي للنماذج المتاحة من Gemini
def find_working_gemini_model():
    """البحث في حساب المستخدم عن اسم الموديل النشط تلقائياً"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            models_list = res.json().get("models", [])
            for m in models_list:
                m_name = m.get("name", "")
                supported = m.get("supportedGenerationMethods", [])
                if "generateContent" in supported:
                    # تفضيل موديلات الفلاش السريعة
                    if "flash" in m_name:
                        return m_name.replace("models/", "")
            # إذا لم نجد فلاش، نأخذ أول نموذج يدعم توليد المحتوى
            for m in models_list:
                if "generateContent" in m.get("supportedGenerationMethods", []):
                    return m.get("name", "").replace("models/", "")
    except Exception as e:
        print(f"⚠️ تعذر فحص قائمة الموديلات: {e}")
    return "gemini-1.5-flash-latest"

def generate_8min_documentary(niche_name):
    if not GEMINI_API_KEY:
        print("⚠️ مفتاح GEMINI_API_KEY غير موجود، استخدام السكربت الاحتياطي.")
        return FALLBACK_LONG_DOCS.get(niche_name, FALLBACK_LONG_DOCS["أبعاد جغرافية"])

    chosen_model = find_working_gemini_model()
    print(f"🤖 الموديل المعتمد للتوليد: {chosen_model}")

    prompt = f"""
أنت مخرج ومحقق وثائقي محترف تصنع أفلاماً استقصائية مشوقة بالعامية المصرية بأسلوب "غابرييل عماد" و "Vox".
المجال المستهدف: {niche_name}.
المطلوب: إنتاج سيناريو فيلم وثائقي استقصائي متكامل مدته 8 دقائق (حوالي 1100 كلمة).

قسّم الفيلم إلى 5 فصول رئيسية:
- الفصل 1: اللغز والكارثة الافتتاحية (The Mystery Hook).
- الفصل 2: البعد الجغرافي والجذور التاريخية (Geopolitical Context).
- الفصل 3: صلب المعركة والأرقام الخارقة (The Core Conflict / Engineering Feat).
- الفصل 4: مليارات الدولارات وسلاسل الإمداد (Economic Fallout).
- الفصل 5: الخاتمة وسؤال المستقبل المفتوح (The Conclusion & Debate).

في كل فصل، ضع 3 مشاهد تفصيلية. في كل مشهد اكتب:
- "narration": نص سردي مشوق وطويل نسبياً بالعامية المصرية الراقية (حوالي 70 إلى 80 كلمة لكل مشهد).
- "query": كلمة بحث سينمائية بالإنجليزية لجلب لقطات عريضة من Pexels (Landscape).
- "lower_third": عنوان توثيقي يظهر أسفل الشاشة (مثل: "📍 مضيق هرمز - الخليج العربي").

أخرج النتيجة بتنسيق JSON خالص وبدون أي علامات Markdown:
{{
  "title": "عنوان وثائقي ناري وجذاب جداً",
  "desc": "وصف مفصل للوثائقي مع روابط الفصول والهاشتاجات",
  "chapters": [
    {{
      "chapter_title": "عنوان الفصل الأول",
      "scenes": [
        {{
          "narration": "النص السردي الكامل بالعامية المصرية...",
          "query": "cinematic landscape cargo ship aerial 4k",
          "lower_third": "📍 بورسعيد - مدخل قناة السويس"
        }}
      ]
    }}
  ]
}}
    """

    # تجربة الموديل المكتشف ثم النماذج الشائعة تباعاً
    candidate_urls = [
        f"https://generativelanguage.googleapis.com/v1beta/models/{chosen_model}:generateContent?key={GEMINI_API_KEY}",
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}",
        f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}",
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={GEMINI_API_KEY}"
    ]

    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    for endpoint in candidate_urls:
        try:
            res = requests.post(endpoint, json=payload, timeout=45)
            if res.status_code == 200:
                raw_text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                raw_text = raw_text.strip().replace("```json", "").replace("```", "")
                data = json.loads(raw_text)
                if "chapters" in data and len(data["chapters"]) >= 4:
                    print(f"✅ تم توليد السيناريو بنجاح عبر: {endpoint.split('models/')[1].split(':')[0]}")
                    return data
        except Exception:
            continue

    print("⚠️ تعذر استجابة نماذج Gemini، سيتم استخدام السكربت الاحتياطي عالي الجودة.")
    return FALLBACK_LONG_DOCS.get(niche_name, FALLBACK_LONG_DOCS["أبعاد جغرافية"])

# 4. التوليد الصوتي
async def generate_voice(text, output_file):
    import edge_tts
    communicate = edge_tts.Communicate(text, "ar-EG-ShakirNeural", rate="+6%")
    await communicate.save(output_file)

# 5. سحب لقطات أفقية (Landscape 16:9)
def fetch_landscape_video(query, target_filename):
    if PEXELS_API_KEY:
        try:
            url = f"https://api.pexels.com/videos/search?query={query}&per_page=5&orientation=landscape"
            headers = {"Authorization": PEXELS_API_KEY, "User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=20)
            if r.status_code == 200:
                vids = r.json().get("videos", [])
                if vids:
                    video_files = vids[0].get("video_files", [])
                    selected_link = None
                    for vf in video_files:
                        if vf.get("width") == 1920 and vf.get("height") == 1080:
                            selected_link = vf.get("link")
                            break
                    if not selected_link and video_files:
                        selected_link = video_files[0].get("link")

                    if selected_link:
                        v_resp = requests.get(selected_link, stream=True, timeout=40)
                        if v_resp.status_code == 200:
                            with open(target_filename, "wb") as f:
                                for chunk in v_resp.iter_content(chunk_size=1024*1024):
                                    if chunk: f.write(chunk)
                            return True
        except Exception as e:
            print(f"⚠️ خطأ في سحب لقطة {query}: {e}")
    return False

# 6. تصميم لوحة التعريف السفلية (Lower-Third 16:9)
def create_lower_third(text, target_path, size=(1920, 1080)):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = get_best_arabic_font(size=36)

    clean_txt = clean_arabic(text)
    has_raqm = features.check("raqm")
    if not has_raqm:
        import arabic_reshaper
        from bidi.algorithm import get_display
        clean_txt = get_display(arabic_reshaper.reshape(clean_txt))

    bbox = draw.textbbox((0, 0), clean_txt, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    bx2 = 1920 - 100
    bx1 = bx2 - tw - 50
    by1 = 1080 - 180
    by2 = by1 + th + 24

    draw.rounded_rectangle([bx1, by1, bx2, by2], radius=14, fill=(10, 15, 25, 220), outline=(0, 230, 255, 200), width=2)
    draw.text(((bx1 + bx2) // 2, by1 + 10), clean_txt, font=font, fill=(255, 255, 255, 255), anchor="mt", direction="rtl" if has_raqm else None)
    img.save(target_path)

# 7. بناء ريندر الفصل وتصديره
def render_chapter_chunk(chapter_data, chapter_idx):
    size = (1920, 1080)
    scenes = []
    temp_files = []
    voice_clips = []
    current_time = 0.0

    print(f"\n🎬 معالجة الفصل {chapter_idx + 1}: {chapter_data['chapter_title']}")

    for s_idx, sc in enumerate(chapter_data["scenes"]):
        aud_path = f"aud_c{chapter_idx}_s{s_idx}.mp3"
        asyncio.run(generate_voice(sc["narration"], aud_path))
        aud_clip = AudioFileClip(aud_path)
        duration = aud_clip.duration + 0.3
        temp_files.append(aud_path)

        voice_clips.append(aud_clip.set_start(current_time))

        vid_path = f"vid_c{chapter_idx}_s{s_idx}.mp4"
        success = fetch_landscape_video(sc["query"], vid_path)

        if success:
            try:
                clip = VideoFileClip(vid_path).without_audio()
                if clip.duration < duration:
                    clip = clip.fx(vfx.loop, duration=duration)
                else:
                    clip = clip.subclip(0, duration)
                clip = clip.resize(size)
                temp_files.append(vid_path)
            except Exception:
                clip = ColorClip(size=size, color=(15, 23, 42)).set_duration(duration)
        else:
            clip = ColorClip(size=size, color=(15, 23, 42)).set_duration(duration)

        lt_path = f"lt_c{chapter_idx}_s{s_idx}.png"
        create_lower_third(sc.get("lower_third", "وثائقي استقصائي"), lt_path, size=size)
        temp_files.append(lt_path)
        lt_clip = ImageClip(lt_path).set_duration(min(4.0, duration)).set_start(0.5)

        composed_scene = CompositeVideoClip([clip, lt_clip], size=size).set_duration(duration)
        scenes.append(composed_scene)
        current_time += duration

    chapter_video = concatenate_videoclips(scenes, method="compose")
    chapter_audio = CompositeAudioClip(voice_clips).set_duration(chapter_video.duration)
    chapter_video = chapter_video.set_audio(chapter_audio)

    chunk_filename = f"chunk_chapter_{chapter_idx}.mp4"
    chapter_video.write_videofile(
        chunk_filename,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        bitrate="4000k",
        preset="ultrafast",
        threads=2
    )

    for f in temp_files:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

    return chunk_filename

# 8. دمج الفصول بـ FFmpeg
def stitch_chapters_with_ffmpeg(chunk_files, output_filename="documentary_8min.mp4"):
    print("\n⚡ بدء الدمج الفوري للفصول عبر FFmpeg Concat...")
    list_path = "chapters_list.txt"
    with open(list_path, "w", encoding="utf-8") as f:
        for chunk in chunk_files:
            f.write(f"file '{chunk}'\n")

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_path,
        "-c", "copy",
        output_filename
    ]
    subprocess.run(cmd, check=True)

    if os.path.exists(list_path):
        os.remove(list_path)
    for chunk in chunk_files:
        if os.path.exists(chunk):
            os.remove(chunk)

    print(f"🎉 تم إنتاج الفيلم الوثائقي الكامل بنجاح: {output_filename}")
    return output_filename

# 9. نقطة التشغيل الرئيسية
def main():
    niche_name = NICHE_NAMES[0]
    print(f"=======================================================")
    print(f"🚀 بدء إنتاج فيلم وثائقي طويل (8 دقائق): {niche_name}")
    print(f"=======================================================")

    doc_data = generate_8min_documentary(niche_name)
    print(f"📌 عنوان الوثائقي: {doc_data['title']}")

    chunk_files = []
    for idx, chapter in enumerate(doc_data["chapters"]):
        chunk_path = render_chapter_chunk(chapter, idx)
        chunk_files.append(chunk_path)

    final_video_path = stitch_chapters_with_ffmpeg(chunk_files, "documentary_8min.mp4")

    with open("video_metadata.json", "w", encoding="utf-8") as f:
        json.dump({
            "title": doc_data["title"],
            "desc": doc_data["desc"]
        }, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
