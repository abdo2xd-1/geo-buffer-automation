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

# موسيقى وثائقية سينمائية محيطية طويلة
DOC_BGM_URL = "[https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3?filename=dark-mystery-trailer-111586.mp3](https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3?filename=dark-mystery-trailer-111586.mp3)"

# ==============================================================================
# بنك السيناريو الموسع الكامل (30 دقيقة - 6 فصول كبرى و 30 مشهداً دسمة)
# ==============================================================================
MASTER_30MIN_FALLBACK = {
    "title": "شرايين الكوكب الخفية: المعركة السرية للتحكم في ممرات العالم المائية",
    "desc": "تحقيق وثائقي استقصائي شامل يمتد لـ 30 دقيقة، يكشف كواليس أخطر نقاط الاختناق الملاحية وصراعات الممرات والنفط وسلاسل الإمداد الدولية.\n\n#أبعاد_جغرافية #وثائقي #جغرافيا #مشاريع #مضائق #اقتصاد",
    "chapters": [
        {
            "chapter_idx": 1,
            "title": "الفصل الأول: لغز نقاط الاختناق القاتلة",
            "scenes": [
                {
                    "narration": "من آلاف السنين، وخريطة القوة على كوكب الأرض مش بتتحدد بحجم الجيوش ولا بمساحة الأراضي، لكن بنقاط جغرافية ضيقة جداً اسمها نقاط الاختناق البحري، قادرة في ثواني معدودة تعطل حركة الحضارة البشرية بالكامل.",
                    "query": "aerial ocean strait cargo ship cinematic",
                    "lower_third": "📍 نقاط الاختناق الجغرافي الحاكمة"
                },
                {
                    "narration": "تسعين بالمئة من كل بضائع العالم بتتحرك في أعالي البحار قبل ما توصل ليدك، من شاشات الموبايلات لبراميل البترول وحبوب القمح. كل ده بيعبر من ممرات عرض بعضها لا يتجاوز بضعة كيلومترات فقط.",
                    "query": "huge container vessel open sea storm",
                    "lower_third": "📦 90% من تجارة العالم تعبر البحار"
                },
                {
                    "narration": "المضائق دي مش مجرد ممرات مياه عادية، دي شرايين حيوية لو ضغط عليها طرف واحد بقرار عسكري أو سياسي، أسعار الطاقة والسلع في أقصى قارات الأرض هتشتعل في نفس اللحظة.",
                    "query": "oil tanker terminal ocean drone",
                    "lower_third": "⚡ تريليونات الدولارات تحت التهديد"
                },
                {
                    "narration": "والسؤال اللي شغل أدمغة القادة والجنرالات عبر القرون: إزاي طبيعة كوكب الأرض فرضت على العالم ممرات إجبارية مستحيل الاستغناء عنها بدون دفع تكلفة كارثية؟",
                    "query": "satellite world map digital lines glowing",
                    "lower_third": "🌐 المعضلة الجغرافية الأزلية"
                },
                {
                    "narration": "علشان نفك اللغز ده من جذوره، لازم نبدأ الرحلة من أكتر بقعة مائية مشتعلة على وجه البسيطة، البقعة اللي بتخرج منها طاقة العالم يومياً.",
                    "query": "persian gulf middle east aerial coastline",
                    "lower_third": "🧭 بداية الرحلة الاستقصائية"
                }
            ]
        },
        {
            "chapter_idx": 2,
            "title": "الفصل الثاني: كواليس مضيق هرمز وصراع الطاقة",
            "scenes": [
                {
                    "narration": "مضيق هرمز هو الرئة النفطية لكوكب الأرض. بيمر منه يومياً أكتر من عشرين مليون برميل نفط، يعني خُمس إجمالي الاستهلاك العالمي من الطاقة السائلة في ممر مائي أضيق نقطة فيه لا تتعدى تسعة وثلاثين كيلومتراً.",
                    "query": "strait of hormuz oil tanker drone aerial",
                    "lower_third": "📍 مضيق هرمز - الخليج العربي"
                },
                {
                    "narration": "المسار الملاحي الفعلي للسفن داخل المضيق عرضه ميلين بحريين فقط للدخول وميلين للخروج. مساحة ضيقة جداً بتخلي حركة أضخم ناقلات النفط في العالم زي السير على حبل مشدود فوق حقل ألغام.",
                    "query": "massive supertanker crude oil ocean",
                    "lower_third": "🛢️ 20 مليون برميل نفط يومياً"
                },
                {
                    "narration": "أي توتر عسكري أو حادثة احتجاز لناقلة واحدة، كفيلة برفع أسعار التأمين البحري وأسعار خام برنت بنسب مرعبة، وده بيترجم فوراً لزيادة في تكلفة النقل والمعيشة في كل عاصمة حول العالم.",
                    "query": "naval patrol boat military escort sea",
                    "lower_third": "⚠️ اشتعال أسعار التأمين الملاحي"
                },
                {
                    "narration": "القوى الاقتصادية الآسيوية الكبرى زي الصين واليابان والهند بتعتمد بشكل شبه كلي على نفط الخليج اللي بيعبر من هنا، وده بيخلي أمن المضيق مسألة حياة أو موت لاقتصادات قائمة بتضم مليارات البشر.",
                    "query": "modern mega city night traffic shanghai",
                    "lower_third": "🏭 شريان الصناعة الآسيوية الكبرى"
                },
                {
                    "narration": "لكن بينما هرمز بيتحكم في طاقة العالم، في ممر تاني في قلب الشرق الأوسط غير وجه التجارة الدولية إلى الأبد وصنع معجزة هندسية مستمرة.",
                    "query": "cargo navigation open sea horizon sunset",
                    "lower_third": "🚢 الانتقال إلى معجزة السويس"
                }
            ]
        },
        {
            "chapter_idx": 3,
            "title": "الفصل الثالث: ملحمة قناة السويس وكارثة إيفر جيفن",
            "scenes": [
                {
                    "narration": "في قلب مصر، شقت قناة السويس طريقها في الرمال علشان تصنع أقصر رابط بحري بين الشرق والغرب، وتختصر على أساطيل التجارة الدوران الطويل والمهلك حول القارة الإفريقية بآلاف الأميال البحرية.",
                    "query": "suez canal aerial ship convoy egypt",
                    "lower_third": "📍 قناة السويس - مصر"
                },
                {
                    "narration": "القناة بيمر منها قرابة اثني عشر بالمئة من إجمالي حركة التجارة العالمية، وما يقرب من ثلاثين بالمئة من حركة الحاويات الدولية، مما يجعلها الشريان الأسرع والأكثر فاعلية لنقل السلع والمعدات بين آسيا وأوروبا.",
                    "query": "port said container terminal time lapse",
                    "lower_third": "⏳ اختصار 7000 كيلومتر بحري"
                },
                {
                    "narration": "لكن في مارس 2021، العالم كله حبس أنفاسه لما سفينة الحاويات العملاقة إيفر جيفن انحرفت في القناة وعثرت في الضفة، لتغلق المجرى الملاحي تماماً وتظهر هشاشة الاعتماد على مسار واحد غير قابل للبديل السريع.",
                    "query": "massive container vessel stuck canal",
                    "lower_third": "🚨 صدمة جنوح إيفر جيفن"
                },
                {
                    "narration": "كل ساعة توقف كانت بتكلف التجارة العالمية أربعمئة مليون دولار، وطوابير مئات السفن اللي علقت في البحر الأحمر والمتوسط كشفت إن العالم المعاصر مربوط ببعضه برباط أرق مما يتخيل أي اقتصادي.",
                    "query": "fleet of ships waiting anchored sea",
                    "lower_third": "💸 خسائر: 400 مليون $ كل ساعة"
                },
                {
                    "narration": "نجاح المهندسين وأطقم الكراكات المصرية في تعويم الوحش العائم وإعادة فتح القناة في وقت قياسي كان بمثابة إنقاذ للاقتصاد الدولي من كارثة تموينية كانت هتضرب الأسواق لشهور طويلة.",
                    "query": "tugboats pulling huge ship water splash",
                    "lower_third": "🏗️ ملحمة التعويم الاستثنائية"
                }
            ]
        },
        {
            "chapter_idx": 4,
            "title": "الفصل الرابع: باب المندب وخفايا البحر الأحمر",
            "scenes": [
                {
                    "narration": "البوابة الجنوبية للبحر الأحمر، مضيق باب المندب، هو الحارس الصارم اللي بيربط المحيط الهندي وخليج عدن بقناة السويس. ممر بيتحكم في عبور أكثر من واحد وعشرين ألف سفينة تجارية عملاقة سنوياً.",
                    "query": "bab el mandeb strait coast mountains sea",
                    "lower_third": "📍 مضيق باب المندب - البحر الأحمر"
                },
                {
                    "narration": "المضيق بيبلغ عرضه حوالي عشرين كيلومتراً فقط، ومقسم إلى ممرين ملاحيين تفصل بينهم جزيرة بريم، مما يجعله هدفاً استراتيجياً حساساً لأي توترات جيوسياسية في منطقة القرن الإفريقي أو شبه الجزيرة العربية.",
                    "query": "red sea coastline aerial dramatic drone",
                    "lower_third": "🛡️ الحارس الجنوبي للملاحة الدولية"
                },
                {
                    "narration": "الاضطرابات والتهديدات الأمنية اللي شهدها الممر دفعت كبرى خطوط الشحن العالمية لتغيير مساراتها قسرياً نحو طريق رأس الرجاء الصالح القديم، وهو ما رفع تكاليف الوقود وزمن الشحن بأسابيع إضافية.",
                    "query": "cape of good hope stormy ocean waves",
                    "lower_third": "🌊 العودة لطريق رأس الرجاء الصالح"
                },
                {
                    "narration": "كل رحلة بتدور حول إفريقيا بتكلف السفينة الواحدة ما يقرب من مليون دولار إضافية في بند الوقود والتأخيرات، وده اللي أكد للدول العظمى إن تأمين باب المندب هو أولوية أمن قومي غير قابلة للمساومة.",
                    "query": "modern freight ship battling rough waves",
                    "lower_third": "💰 مليون $ تكلفة إضافية للرحلة"
                },
                {
                    "narration": "ومع تزايد الضغوط على الممرات الدافئة، بدأت عيون الدول العظمى تبص نحو الشمال الأقصى المتجمد، بحثاً عن معجزة ملاحية جديدة كانت مستحيلة في الماضي.",
                    "query": "arctic ocean iceberg frozen ice landscape",
                    "lower_third": "🧭 التحول نحو الصقيع القطبي"
                }
            ]
        },
        {
            "chapter_idx": 5,
            "title": "الفصل الخامس: صراع القطب الشمالي والممرات البديلة",
            "scenes": [
                {
                    "narration": "طريق الملاحة الشمالي عبر القطب المتجمد بيعيد رسم خريطة الجغرافيا بالكامل. مع انحسار الجليد في شهور الصيف، بيوفر المسار ده اختصاراً بنسبة أربعين بالمئة في المسافة بين موانئ شرق آسيا وغرب أوروبا.",
                    "query": "arctic icebreaker cutting through ice frozen",
                    "lower_third": "❄️ طريق الملاحة الشمالي - القطب"
                },
                {
                    "narration": "روسيا بتبني أكبر أسطول لكاسحات الجليد النووية في التاريخ، بهدف تحويل هذا المسار المتجمد إلى أوتوستراد مائي دائم يعمل على مدار العام تحت إدارتها ورقابتها الصارمة.",
                    "query": "nuclear icebreaker drone shot aerial ice",
                    "lower_third": "🚢 أسطول كاسحات الجليد النووية"
                },
                {
                    "narration": "الصين من جهتها أعلنت عن استراتيجية طريق الحرير القطبي، وبتستثمر مليارات الدولارات في موانئ وبنية تحتية شمالية بالتعاون مع موسكو لكسر الاعتماد على المضائق التي تراقبها القوات البحرية الغربية.",
                    "query": "modern arctic port cargo facility winter",
                    "lower_third": "🇨🇳 طريق الحرير القطبي الصيني"
                },
                {
                    "narration": "لكن البيئة القطبية القاسية والتكاليف الباهظة لسفن العبور المصممة لتحمل الاصطدام بالجليد، بتخلي الممر ده سلاحاً استراتيجياً للمستقبل أكتر منه بديلاً شاملاً لحركة التجارة اللحظية اليوم.",
                    "query": "blizzard storm arctic freezing conditions",
                    "lower_third": "⚠️ مخاطر البيئة واللوجستيات القطبية"
                },
                {
                    "narration": "بين مياه هرمز الدافئة وصقيع القطب المتجمد، المعركة على الممرات المائية دخلت طوراً جديداً هيحدد شكل الهيمنة الاقتصادية على مدار المئة عام القادمة.",
                    "query": "cinematic globe rotation space atmosphere",
                    "lower_third": "🌐 صراع المئة عام القادمة"
                }
            ]
        },
        {
            "chapter_idx": 6,
            "title": "الفصل السادس: سيناريوهات المستقبل والكلمة الأخيرة",
            "scenes": [
                {
                    "narration": "الصراع في القرن الحادي والعشرين مش صراع على الحدود البرية زي ما كان في القرون الماضية، ده صراع لوجستي بحت على التحكم في نقاط الاختناق اللي بتتحكم في تدفق الحياة نفسها للبشرية.",
                    "query": "digital container logistics automated port",
                    "lower_third": "🏗️ حروب اللوجستيات وسلاسل الإمداد"
                },
                {
                    "narration": "من مضيق ملقا في جنوب شرق آسيا اللي بيمر منه ثلث تجارة العالم، لقناة بنما في الأمريكتين اللي بتعاني من الجفاف وانخفاض منسوب المياه، كل قطرة ماء صالحة للملاحة أصبحت ورقة ضغط سياسية كبرى.",
                    "query": "panama canal aerial locks container crossing",
                    "lower_third": "📍 قناة بنما ومضيق ملقا"
                },
                {
                    "narration": "الدول اللي بتمتلك السيطرة على الممرات دي مش بس بتجني رسوم عبور بمليارات الدولارات، دي بتمتلك أوراق تفاوض سيادية قادرة على تعديل موازين القوى في أي صراع دولي قادم.",
                    "query": "world economic forum leadership conference",
                    "lower_third": "🏛️ أوراق الضغط السيادية الكبرى"
                },
                {
                    "narration": "ومع تطور التجارة الرقمية وسفن الشحن ذاتية القيادة، هيفضل العنصر الجغرافي هو الثابت الوحيد: الأرض هتفضل هي الأرض، والممرات المائية هتفضل شرايينها التي لا يمكن تعويضها.",
                    "query": "autonomous modern concept cargo ship ocean",
                    "lower_third": "🤖 مستقبل الشحن البحري الذكي"
                },
                {
                    "narration": "تفتكروا إيه الممر المائي اللي ممكن يشهد الصدمة الكبرى القادمة ويهدد بإيقاف حركة العالم؟ شاركونا آراءكم في التعليقات، واشتركوا في القناة لمتابعة تحقيقاتنا الوثائقية القادمة.",
                    "query": "cinematic ocean sunset drone horizon calm",
                    "lower_third": "💬 شاركنا رأيك بالتعليقات واشترك بالقناة"
                }
            ]
        }
    ]
}

def ensure_bgm():
    if not os.path.exists("doc_bgm.mp3"):
        try:
            r = requests.get(DOC_BGM_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=25)
            if r.status_code == 200:
                with open("doc_bgm.mp3", "wb") as f:
                    f.write(r.content)
        except Exception as e:
            print(f"⚠️ تعذر تنزيل الموسيقى: {e}")

def get_best_arabic_font(size=42):
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

# استدعاء Gemini مع معالجة الأخطاء والعودة التلقائية دون انهيار
def call_gemini_safe(prompt):
    if not GEMINI_API_KEY:
        return None
    models_to_try = [
        ("v1beta", "gemini-1.5-flash-latest"),
        ("v1beta", "gemini-1.5-flash"),
        ("v1", "gemini-1.5-flash"),
        ("v1beta", "gemini-2.0-flash"),
        ("v1beta", "gemini-pro")
    ]
    for ver, mod in models_to_try:
        url = f"[https://generativelanguage.googleapis.com/](https://generativelanguage.googleapis.com/){ver}/models/{mod}:generateContent?key={GEMINI_API_KEY}"
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
            if res.status_code == 200:
                txt = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                clean_txt = txt.strip()
                clean_txt = clean_txt.replace("```json", "").replace("```", "")
                return clean_txt.strip()
            else:
                print(f"⚠️ فحص {mod} على {ver} أعاد كود: {res.status_code}")
        except Exception:
            continue
    return None

def get_documentary_outline(niche_name):
    print("🧠 جاري تحضير المخطط الاستقصائي للوثائقي الكبير (30 دقيقة)...")
    prompt = f"""
أنت مخرج ومحقق وثائقي محترف. المطلوب هيكل فيلم وثائقي 30 دقيقة لمجال: {niche_name}.
قسّم الفيلم إلى 6 فصول رئيسية في صيغة JSON فقط:
{{
  "title": "عنوان وثائقي ملحمي",
  "desc": "وصف مفصل للوثائقي",
  "chapters": [
    {{"chapter_idx": 1, "title": "عنوان الفصل الأول"}},
    {{"chapter_idx": 2, "title": "عنوان الفصل الثاني"}},
    {{"chapter_idx": 3, "title": "عنوان الفصل الثالث"}},
    {{"chapter_idx": 4, "title": "عنوان الفصل الرابع"}},
    {{"chapter_idx": 5, "title": "عنوان الفصل الخامس"}},
    {{"chapter_idx": 6, "title": "عنوان الفصل السادس"}}
  ]
}}
    """
    raw_res = call_gemini_safe(prompt)
    if raw_res:
        try:
            data = json.loads(raw_res)
            if "chapters" in data and len(data["chapters"]) >= 5:
                print("✅ تم بنجاح استلام المخطط المولد من Gemini.")
                return data
        except Exception:
            pass

    print("🛡️ سيتم الاعتماد مباشرة على السيناريو الموسع المتكامل عالي الجودة.")
    return MASTER_30MIN_FALLBACK

def get_chapter_scenes(niche_name, doc_title, chapter_info, chapter_idx):
    prompt = f"""
أنت محقق وثائقي. الفيلم: "{doc_title}". الفصل: "{chapter_info['title']}".
اكتب 5 مشاهد مفصلة بالعامية المصرية الراقية (80 إلى 100 كلمة لكل مشهد).
JSON فقط:
{{
  "scenes": [
    {{
      "narration": "النص السردي المفصل...",
      "query": "cinematic 4k landscape stock footage english",
      "lower_third": "📍 الموقع أو التوثيق"
    }}
  ]
}}
    """
    raw_res = call_gemini_safe(prompt)
    if raw_res:
        try:
            data = json.loads(raw_res)
            if "scenes" in data and len(data["scenes"]) >= 3:
                return data["scenes"]
        except Exception:
            pass

    fallback_chapters = MASTER_30MIN_FALLBACK["chapters"]
    fallback_ch = fallback_chapters[(chapter_idx - 1) % len(fallback_chapters)]
    return fallback_ch["scenes"]

# 2. التوليد الصوتي
async def generate_voice(text, output_file):
    import edge_tts
    communicate = edge_tts.Communicate(text, "ar-EG-ShakirNeural", rate="+4%")
    await communicate.save(output_file)

# 3. جلب مقاطع الفيديو العريضة
def fetch_landscape_video(query, target_filename):
    if PEXELS_API_KEY:
        try:
            url = f"[https://api.pexels.com/videos/search?query=](https://api.pexels.com/videos/search?query=){query}&per_page=5&orientation=landscape"
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
        except Exception:
            pass
    return False

# 4. لوحة التعريف السفلية (Lower-Third 16:9)
def create_lower_third(text, target_path, size=(1920, 1080)):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = get_best_arabic_font(size=34)

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

# 5. بناء رندر الفصل الواحد كملف مستقل (Chunk)
def render_chapter_chunk(scenes_list, chapter_title, chapter_idx):
    size = (1920, 1080)
    scenes = []
    temp_files = []
    voice_clips = []
    current_time = 0.0

    print(f"\n🎬 معالجة وتصدير الفصل {chapter_idx}: {chapter_title} ({len(scenes_list)} مشاهد)...")

    for s_idx, sc in enumerate(scenes_list):
        aud_path = f"aud_c{chapter_idx}_s{s_idx}.mp3"
        asyncio.run(generate_voice(sc["narration"], aud_path))
        aud_clip = AudioFileClip(aud_path)
        duration = aud_clip.duration + 0.35
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
        create_lower_third(sc.get("lower_third", chapter_title), lt_path, size=size)
        temp_files.append(lt_path)
        lt_clip = ImageClip(lt_path).set_duration(min(5.0, duration)).set_start(0.5)

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
        bitrate="3500k",
        preset="ultrafast",
        threads=2
    )

    for f in temp_files:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

    return chunk_filename

# 6. دمج الفصول وإضافة الموسيقى التصويرية الممتدة عبر FFmpeg
def stitch_and_finalize_documentary(chunk_files, output_filename="documentary_30min.mp4"):
    print("\n⚡ بدء الدمج الفوري لجميع الفصول عبر FFmpeg Concat...")
    list_path = "chapters_list.txt"
    with open(list_path, "w", encoding="utf-8") as f:
        for chunk in chunk_files:
            f.write(f"file '{chunk}'\n")

    temp_stitched = "temp_raw_stitched.mp4"
    cmd_concat = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_path,
        "-c", "copy",
        temp_stitched
    ]
    subprocess.run(cmd_concat, check=True)

    ensure_bgm()
    if os.path.exists("doc_bgm.mp3"):
        print("🎵 دمج الموسيقى التصويرية الوثائقية بكامل مدة الفيلم...")
        cmd_audio = [
            "ffmpeg", "-y",
            "-i", temp_stitched,
            "-stream_loop", "-1", "-i", "doc_bgm.mp3",
            "-filter_complex", "[1:a]volume=0.08[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=3[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            output_filename
        ]
        subprocess.run(cmd_audio, check=True)
        if os.path.exists(temp_stitched):
            os.remove(temp_stitched)
    else:
        os.rename(temp_stitched, output_filename)

    if os.path.exists(list_path):
        os.remove(list_path)
    for chunk in chunk_files:
        if os.path.exists(chunk):
            os.remove(chunk)

    print(f"🎉 تم بنجاح إنتاج الفيلم الوثائقي الطويل: {output_filename}")
    return output_filename

def main():
    niche_name = NICHE_NAMES[0]
    print(f"=======================================================")
    print(f"🚀 بدء إنتاج فيلم وثائقي ضخم (25 - 30 دقيقة): {niche_name}")
    print(f"=======================================================")

    doc_outline = get_documentary_outline(niche_name)
    print(f"📌 عنوان الوثائقي: {doc_outline['title']}")

    chunk_files = []
    for ch in doc_outline["chapters"]:
        scenes = get_chapter_scenes(niche_name, doc_outline["title"], ch, ch["chapter_idx"])
        chunk_file = render_chapter_chunk(scenes, ch["title"], ch["chapter_idx"])
        chunk_files.append(chunk_file)

    final_video_path = stitch_and_finalize_documentary(chunk_files, "documentary_30min.mp4")

    with open("video_metadata.json", "w", encoding="utf-8") as f:
        json.dump({
            "title": doc_outline["title"],
            "desc": doc_outline["desc"]
        }, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
