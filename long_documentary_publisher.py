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
DOC_BGM_URL = "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3?filename=dark-mystery-trailer-111586.mp3"

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
        url = f"https://generativelanguage.googleapis.com/{ver}/models/{mod}:generateContent?key={GEMINI_API_KEY}"
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
            if res.status_code == 200:
                txt = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                return txt.strip().replace("```json", "").replace("
