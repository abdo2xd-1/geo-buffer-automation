import os
import sys
import re
import json
import time
import random
import asyncio
import requests
import subprocess
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

try:
    import edge_tts
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "edge-tts"])
    import edge_tts

try:
    import gtts
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "gTTS"])
    import gtts

import google.generativeai as genai

# --- 1. الإعدادات والنموذج الفعال ---
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_KEY = os.getenv("PEXELS_API_KEY")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

def get_active_model():
    if not GEMINI_KEY:
        return None
    candidates = ["gemini-3.8-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro", "gemini-pro"]
    for c in candidates:
        try:
            m = genai.GenerativeModel(c)
            m.generate_content("test")
            print(f"🎯 تم تفعيل النموذج المعتمد: [{c}]")
            return m
        except Exception:
            continue
    return None

model = get_active_model()
VOICE_NAME = "ar-EG-ShakirNeural"

MIN_DURATION_SECONDS = 600   # 10 دقائق كحد أدنى
MAX_SAFE_SECONDS = 870       # 14.5 دقيقة لتفادي قيود يوتيوب

def clean_arabic_text(text: str) -> str:
    text = re.sub(r'[*#_`~>\[\]\(\)]', ' ', text)
    text = text.replace('"', ' ').replace("'", ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_audio_duration(file_path: str) -> float:
    try:
        cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file_path}"'
        res = subprocess.check_output(cmd, shell=True).decode().strip()
        return float(res)
    except Exception:
        return 0.0

# --- دالة الذكاء الاصطناعي المقاومة للحظر الجغرافي ---
def query_ai_robust(prompt: str) -> str:
    if model:
        try:
            res = model.generate_content(prompt)
            if res and res.text:
                return res.text.strip()
        except Exception as e:
            print(f"⚠️ تنبيه Gemini ({e})، جاري التحويل للمحرك البديل العالمي...")

    try:
        url = "https://text.pollinations.ai/"
        headers = {"Content-Type": "application/json"}
        payload = {
            "messages": [
                {"role": "system", "content": "أنت خبير كتابة وثائقيات تلفزيونية فخمة باللغة العربية الفصحى."},
                {"role": "user", "content": prompt}
            ],
            "model": "openai"
        }
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        if r.status_code == 200 and r.text:
            return r.text.strip()
    except Exception:
        pass

    return ""

# --- 2. توليد فكرة وفصول وثائقية كبرى (5-Act Narrative Arc) ---
def get_titan_documentary_meta(channel_name: str) -> dict:
    print(f"🎲 جاري ابتكار ملحمة وثائقية تلفزيونية كبرى لقناة [{channel_name}]...")
    prompt = f"""
    أنت كبير مديري إنتاج الأفلام الوثائقية العالمية في شبكة كبرى مثل National Geographic لقناة: "{channel_name}".
    ابتكر فكرة عمل وثائقي استثنائي وغامض، مع تنوع مطلق دون أي حصر مسبق (حضارات مفقودة، ألغاز جغرافية، عمليات استخباراتية، مدن تحت الأرض، كوارث غيرت العالم).
    
    المطلوب استخراجه بدقة بصيغة JSON حصراً:
    {{
        "title": "عنوان وثائقي ملحمي",
        "thumb_text": "نص الصورة المصغرة",
        "pinned_question": "سؤال التعليق الأول للتفاعل",
        "chapters": ["المقدمة واللغز", "الجذور غير المعلنة", "الأدلة والتحقيق", "الخاتمة والمصير"],
        "search_keywords": ["ancient ruins 4k", "desert mystery", "archaeology aerial", "lost civilization", "sand storm dunes", "ancient temple entrance"]
    }}
    """
    ai_raw = query_ai_robust(prompt)
    if ai_raw:
        try:
            cleaned = ai_raw.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)
            print(f"  💡 العنوان المختار: {data['title']}")
            return data
        except Exception:
            pass

    topics = [
        ("أسرار الممالك المفقودة: مدن طمستها الرمال", "الحقيقة الصادمة", "هل تعتقد أن هناك حضارات متطورة سادت قبلنا ومحيت تماماً؟", ["المقدمة واللغز", "حضارات طمستها الرمال", "اكتشافات حديثة", "السر الأعظم"], ["ancient ruins 4k", "desert mystery", "archaeology aerial", "lost civilization", "sand storm dunes", "ancient temple entrance"]),
        ("خفايا العمليات السرية: ملفات غيرت مسار التاريخ", "ملفات محظورة", "أي هذه العمليات السرية كان لها الأثر الأكبر على عالم اليوم؟", ["مقدمة الصراع", "خلف الأبواب المغلقة", "الوثائق المسربة", "المواجهة الأخيرة"], ["classified documents", "historical warfare", "vintage intelligence", "cinematic shadows", "cold war aerial", "secret bunker door"]),
        ("حدود الكوكب المجهولة: بقاع لم يطأها إنسان", "العالم الآخر", "ما هو المكان الأكثر غموضاً ورعباً على كوكب الأرض برأيك؟", ["أطراف العالم", "رحلات المستكشفين", "أسرار الطبيعة", "المصير المحتوم"], ["extreme wilderness", "mysterious mountains", "unexplored nature", "aerial drone 4k", "deep ocean abyss", "siberia frozen ice"])
    ]
    chosen = random.choice(topics)
    data = {
        "title": chosen[0],
        "thumb_text": chosen[1],
        "pinned_question": chosen[2],
        "chapters": chosen[3],
        "search_keywords": chosen[4]
    }
    print(f"  💡 العنوان المختار: {data['title']}")
    return data

# --- 3. كتابة سيناريو وثائقي متكامل بطول 1600 كلمة ---
def generate_titan_long_script(title: str) -> str:
    print(f"✍️ جاري صياغة السرد الوثائقي التلفزيوني المطول (11 إلى 14 دقيقة)...")
    prompt = f"""
    أنت كبير كتاب الوثائقيات التلفزيونية العالمية.
    عنوان العمل: "{title}".
    
    المطلوب: كتابة سيناريو وثائقي متكامل فخم ومترابط بنظام الـ 4 فصول التلفزيونية (المقدمة، الجذور الخفية، الأدلة والتحقيق، والخاتمة الفلسفية).
    
    شروط ملزمة:
    - اكتب نصاً سردياً متواصلاً يتراوح بدقة بين 1500 إلى 1700 كلمة باللغة العربية الفصحى الفخمة.
    - اكتب فقط النص المقروء الذي ينطقه الراوي بصوته مباشرة دون وضع أي توجيهات إخراجية أو أسماء للمشاهد.
    """
    ai_script = query_ai_robust(prompt)
    if ai_script:
        cleaned = clean_arabic_text(ai_script)
        if len(cleaned.split()) >= 800:
            print(f"  ✅ تم إنجاز النص السردي ({len(cleaned.split())} كلمة)!")
            return cleaned

    print("  ⚙️ تفعيل محرك التوليد الموسوعي الداخلي لضمان تخطي 11 دقيقة كاملة...")
    part1 = (
        f"في عمق التاريخ وأروقة الغموض الإنساني، يقف ملف {title} كأحد أعظم التحديات الفكرية والاستكشافية التي واجهت البشرية عبر العصور المتعاقبة. "
        "إن النظر في هذا الموضوع لا يقتصر على مجرد استعراض وقائع عابرة، بل هو غوص منهجي في أسرار غير معلنة صاغت موازين القوى وشكلت منعطفات حاسمة في الوعي الجمعي للإنسانية جمعاء. "
        "منذ اللحظات الأولى التي بدأت فيها ملامح هذه القصة بالظهور، انقسم الباحثون والمؤرخون بين مشكك في صحة الروايات المتداولة ومؤكد لوجود حقائق صادمة تم حجبها بعناية فائقة عن الرأي العام. "
        "الوثائق المتاحة اليوم تعيد رسم المشهد بشكل غير مسبوق، كاشفة عن تقاطعات مذهلة بين الأساطير الشعبية والحقائق الجيولوجية والتاريخية الموثقة علمياً بدقة بالغة. "
    )
    part2 = (
        "عند العودة إلى السجلات الأرشيفية والبيانات الميدانية المبكرة، نكتشف أن الشرارة الأولى انطلقت في ظروف استثنائية لم تحظَ بالتغطية الكافية في وسائل الإعلام التقليدية آنذاك. "
        "شهادات المعاصرين والبيانات الاستكشافية تشير بوضوح إلى تحركات مريبة ولقاءات مغلقة سبقت الإعلان الرسمي بسنوات عديدة، بعيداً عن أعين المتطفلين والمهتمين بالتوثيق التاريخي. "
        "تلك الحقبة شهدت صراعاً محتدماً بين رغبة جامحة في كشف الحقيقة وضغوط سياسية وأمنية هائلة فرضت طوقاً من السرية التامة لمنع تسرب أي معلومات قد تزعزع التوازن القائم وتثير جدلاً لا تحمد عقباه. "
        "الباحثون الأوائل تركوا وراءهم مذكرات مشفرة ومخطوطات نادرة تحوي تفاصيل مذهلة عن مواقع محظورة وطرق سرية وتجارب معقدة لم يجرؤ أحد على الحديث عنها علانية. "
    )
    part3 = (
        "ومع تقدم أعمال التنقيب والمسح الجيولوجي الدقيق باستخدام أحدث أجهزة الاستشعار عن بعد والأقمار الصناعية المتطورة، بدأت تتكشف ملامح غير مسبوقة لبنى تحتية معقدة وأنظمة هندسية بالغة الدقة سبقت عصرها بقرون طويلة. "
        "العلماء عثروا على أنماط غير مفسرة وخرائط طوبوغرافية دقيقة تعود لحقب زمنية غابرة، تؤكد وجود منشآت عملاقة وتقنيات بناء فريدة تعجز النظريات الأثرية السائدة عن تقديم تفسير منطقي وشامل لكيفية إنجازها في تلك العصور البدائية. "
        "هذه الاكتشافات وضعت المؤسسات الأكاديمية والبحثية في مأزق حقيقي، إذ أصبح من المستحيل الاستمرار في إنكار الظاهرة أو اختزالها في مجرد صدف عشوائية، مما فتح الباب على مصراعيه لفرضيات جديدة وجريئة. "
        "التحليلات المخبرية للعينات المأخوذة أظهرت نسباً غير طبيعية لعناصر نادرة وتأثيرات حرارية وكهرومغناطيسية هائلة، مما يرجح وقوع حوادث خارقة للعادة أو استخدام تقنيات طاقة مجهولة لم نتوصل إلى فك شفرتها حتى اللحظة. "
    )
    part4 = (
        "لم يكن هذا الملف مجرد لغز علمي أو تاريخي معزول، بل تحول سريعاً إلى ساحة لتنافس محموم بين قوى كبرى سعت كل منها لاحتكار أسراره واستثمارها لتحقيق تفوق استراتيجي وعسكري واقتصادي حاسم. "
        "الأرقام والإحصائيات والتحليلات الجيوسياسية تؤكد أن الميزانيات التي رُصدت لهذه العمليات فاقت التوقعات بمراحل، مما يبرهن على الأهمية الفائقة والقيمة الهائلة التي كانت تنطوي عليها تلك الاكتشافات في حسابات صناع القرار. "
        "الكثير من الشهود والخبراء والعلماء المستقلين الذين حاولوا التحدث علناً أو نشر أبحاثهم واجهوا تضييقاً ممنهجاً وحملات تشكيك واسعة، مما زاد من غموض المشهد وأثار تساؤلات مشروعة لا تزال تبحث عن إجابات قاطعة حتى يومنا هذا. "
        "التنسيق الاستخباري عالي المستوى وتصنيف الملفات تحت بند سري للغاية يعكسان بوضوح مدى حساسية الموقف والخشية من العواقب غير المتوقعة في حال تم كشف كامل التفاصيل للجمهور. "
    )
    part5 = (
        "في ختام هذه الرحلة الاستقصائية العميقة والشاملة، يتضح جلياً أن الحقيقة غالباً ما تكون أكثر تعقيداً وتشويقاً من كل الروايات الخيالية والأساطير التي نسجت حولها على مر الأجيال. "
        "إن ما تم الكشف عنه حتى الآن ليس سوى قمة جبل الجليد، بينما تظل الأعماق السحيقة تخفي أسراراً مدفونة قد تغير نظرتنا للماضي البشري وتفتح آفاقاً جديدة لفهم المستقبل ومسارات التطور الإنساني. "
        "يبقى السؤال الأهم الذي يفرض نفسه بإلحاح على الأذهان: هل ستشهد السنوات القادمة إماطة اللثام بالكامل عما تبقى من خفايا، أم أن هذا اللغز سيظل طي الكتمان مدفوناً في أعماق التاريخ إلى ما لا نهاية؟ "
        "إن استمرار البحث والتقصي يظل واجباً معرفياً لا غنى عنه، فالوعي بالتاريخ وحقائقه الكبرى هو البوصلة الحقيقية التي ترشد الأمم نحو فهم ذاتها وبناء مستقبلها على أسس راسخة لا تزعزعها الأكاذيب والغموض. "
    )
    full_block = f"{part1}\n\n{part2}\n\n{part3}\n\n{part4}\n\n{part5}"
    return f"{full_block}\n\n{full_block}\n\n{full_block}"

# --- 4. توليد الصوت البشري المجزأ ---
async def generate_chunk_edge_tts(chunk_text: str, output_file: str):
    comm = edge_tts.Communicate(chunk_text, VOICE_NAME, rate="-4%")
    await comm.save(output_file)

def build_guaranteed_audio(title: str) -> float:
    script_text = generate_titan_long_script(title)
    print(f"🎙️ جاري توليد التعليق الصوتي البشري الممتد...")
    
    words = script_text.split()
    chunk_size = 140
    chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    
    os.makedirs("audio_parts", exist_ok=True)
    part_files = []
    
    for idx, chunk in enumerate(chunks, 1):
        part_name = f"audio_parts/part_{idx:03d}.mp3"
        success = False
        for attempt in range(2):
            try:
                asyncio.run(generate_chunk_edge_tts(chunk, part_name))
                if os.path.exists(part_name) and os.path.getsize(part_name) > 1024:
                    part_files.append(part_name)
                    success = True
                    break
            except Exception:
                time.sleep(1)
        if not success:
            try:
                tts = gtts.gTTS(text=chunk, lang="ar")
                tts.save(part_name)
                if os.path.exists(part_name) and os.path.getsize(part_name) > 512:
                    part_files.append(part_name)
            except Exception:
                pass

    if part_files:
        with open("audio_list.txt", "w", encoding="utf-8") as f:
            for p in part_files:
                f.write(f"file '{os.path.abspath(p)}'\n")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "audio_list.txt", "-c", "copy", "narration.mp3"], check=True)
    else:
        gtts.gTTS(text="وثائقي استكشافي شامل يستعرض أهم الحقائق والتحليلات.", lang="ar").save("narration.mp3")

    duration = get_audio_duration("narration.mp3")
    print(f"🎧 مدة الصوت الحالية: {duration / 60:.2f} دقيقة ({duration:.0f} ثانية)")

    while duration < MIN_DURATION_SECONDS:
        extra_prompt = f"اكتب فقرة وثائقية تكميلية مطولة (350 كلمة) باللغة العربية الفصحى تضيف تحليلاً عميقاً حول: {title}."
        extra_text = query_ai_robust(extra_prompt)
        if not extra_text:
            extra_text = f"إن إعادة قراءة هذه المعطيات حول {title} تسلط الضوء على أبعاد غير مرئية تتكامل مع السرد الرئيسي لتؤكد أن البحث التاريخي يظل رحلة متجددة لا تتوقف عند حدود التفسيرات الجاهزة."
        extra_clean = clean_arabic_text(extra_text)

        try:
            asyncio.run(generate_chunk_edge_tts(extra_clean, "extra.mp3"))
        except Exception:
            gtts.gTTS(text=extra_clean, lang="ar").save("extra.mp3")
            
        with open("concat_extra.txt", "w", encoding="utf-8") as f:
            f.write(f"file '{os.path.abspath('narration.mp3')}'\nfile '{os.path.abspath('extra.mp3')}'\n")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "concat_extra.txt", "-c", "copy", "narration_final.mp3"], check=True)
        os.replace("narration_final.mp3", "narration.mp3")
        duration = get_audio_duration("narration.mp3")

    if duration > MAX_SAFE_SECONDS:
        subprocess.run(["ffmpeg", "-y", "-i", "narration.mp3", "-t", str(MAX_SAFE_SECONDS), "-c", "copy", "narration_trimmed.mp3"], check=True)
        os.replace("narration_trimmed.mp3", "narration.mp3")
        duration = get_audio_duration("narration.mp3")

    print(f"✅ تم تأكيد مدة الفيلم الوثائقي: {duration / 60:.2f} دقيقة!")
    return duration

# --- 5. جلب مشاهد Pexels المتنوعة ---
def prepare_video_footage(keywords: list, target_duration: float, output_dir: str = "clips") -> str:
    print(f"🎥 جاري جلب المشاهد لتغطية مدة {target_duration / 60:.1f} دقيقة من مصادر متعددة...")
    os.makedirs(output_dir, exist_ok=True)
    headers = {"Authorization": PEXELS_KEY}
    
    raw_clips = []
    for kw in keywords:
        url = f"https://api.pexels.com/videos/search?query={kw}&per_page=6&orientation=landscape"
        try:
            res = requests.get(url, headers=headers, timeout=20).json()
            for v in res.get("videos", []):
                files = v.get("video_files", [])
                chosen = next((f for f in files if f.get("width") == 1920), None) or (files[0] if files else None)
                if chosen:
                    raw_clips.append(chosen.get("link"))
        except Exception:
            continue
            
    unique_links = list(set(raw_clips))[:20]
    downloaded_files = []
    for idx, link in enumerate(unique_links, 1):
        c_path = os.path.join(output_dir, f"clip_{idx:02d}.mp4")
        try:
            r = requests.get(link, stream=True, timeout=30)
            with open(c_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    f.write(chunk)
            downloaded_files.append(c_path)
        except Exception:
            continue
            
    playlist_path = "full_playlist.txt"
    with open(playlist_path, "w", encoding="utf-8") as f:
        loops_needed = int((target_duration // max(1, len(downloaded_files) * 8)) + 3)
        playlist = []
        for _ in range(loops_needed):
            shuffled = downloaded_files.copy()
            random.shuffle(shuffled)
            playlist.extend(shuffled)
        for clip in playlist:
            f.write(f"file '{os.path.abspath(clip)}'\n")
            
    return playlist_path

# --- 6. رندر سينمائي فائق السرعة والمضبوط بالثانية بدقة ---
def render_titan_documentary(playlist_path: str, audio_path: str, channel_name: str, output_path: str = "final_documentary.mp4"):
    doc_dur = get_audio_duration(audio_path)
    print(f"🎨 جاري المونتاج السينمائي فائق السرعة المضبوط على {doc_dur / 60:.2f} دقيقة...")
    
    bgm_cmd = [
        "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=52:sample_rate=44100",
        "-t", str(doc_dur + 2), "-af", "lowpass=f=220,volume=0.08", "long_bgm.mp3"
    ]
    subprocess.run(bgm_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    audio_chain = (
        "[1:a]highpass=f=70,equalizer=f=120:width_type=o:width=1.6:g=4.0,"
        "equalizer=f=3500:width_type=o:width=1.4:g=2.5,loudnorm=I=-14:TP=-1.5:LRA=7[voice];"
        "[2:a]volume=0.08[bgm];"
        "[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
    )

    clean_tag = clean_arabic_text(channel_name.split('|')[0].strip())

    # تلوين وتظليل سينمائي سريع وخفيف بدون فلاتر ثقيلة تعطل المعالج
    video_chain = (
        "[0:v]fps=25,scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,"
        "eq=contrast=1.14:saturation=1.22:brightness=-0.01,vignette=angle=0.40,"
        f"drawtext=text='{clean_tag}':fontcolor=white@0.3:fontsize=38:x=60:y=60:box=1:boxcolor=black@0.2:boxborderw=10,"
        "format=yuv420p[vout]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-fflags", "+genpts",
        "-f", "concat", "-safe", "0", "-i", playlist_path,
        "-i", audio_path,
        "-i", "long_bgm.mp3",
        "-t", str(doc_dur),                         # إيقاف الرندر فور انتهاء الصوت بدقة
        "-filter_complex", f"{video_chain};{audio_chain}",
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "26",
        "-c:a", "aac", "-b:a", "192k",
        "-threads", "0",                            # استغلال كافة قدرات المعالج
        "-max_muxing_queue_size", "1024",
        output_path
    ]
    subprocess.run(cmd, check=True)
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"🏆 اكتمل إنتاج الفيلم الوثائقي بنجاح: {output_path} ({size_mb:.1f} ميجابايت)")

# --- 7. توليد صورة مصغرة نارية تلقائياً (Auto High-CTR Thumbnail) ---
def create_auto_thumbnail(video_path: str, thumb_text: str, output_thumb: str = "custom_thumb.jpg") -> str:
    print(f"🖼️ جاري صناعة صورة مصغرة سينمائية نارية (Headline: {thumb_text})...")
    raw_frame = "raw_frame.jpg"
    subprocess.run(["ffmpeg", "-y", "-ss", "00:00:18", "-i", video_path, "-vframes", "1", "-q:v", "2", raw_frame], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    clean_text = clean_arabic_text(thumb_text)
    vf = (
        "scale=1280:720,eq=contrast=1.25:saturation=1.35:brightness=-0.02,vignette=angle=0.55,"
        f"drawtext=text='{clean_text}':fontcolor=yellow:fontsize=75:x=(w-text_w)/2:y=(h-text_h)/2:"
        "box=1:boxcolor=black@0.75:boxborderw=20"
    )
    subprocess.run(["ffmpeg", "-y", "-i", raw_frame, "-vf", vf, "-q:v", "2", output_thumb], check=True)
    print(f"  ✅ تم إنتاج الصورة المصغرة بنجاح: {output_thumb}")
    return output_thumb

# --- 8. إنشاء فصول الفيديو التلقائية لرفع الـ SEO (YouTube Chapters) ---
def build_seo_description(meta: dict, total_duration: float) -> str:
    chaps = meta.get("chapters", ["المقدمة", "خفايا القصة", "كشف الحقائق", "الخاتمة"])
    step = total_duration / len(chaps)
    
    desc_lines = [
        f"{meta['title']}\n",
        "في هذا الوثائقي الشامل، نغوص في أعمق التفاصيل والحقائق غير المعلنة.\n",
        "📌 فصول الوثائقي (Timestamps):"
    ]
    for i, c in enumerate(chaps):
        sec = int(i * step)
        desc_lines.append(f"{sec//60:02d}:{sec%60:02d} - {c}")
        
    desc_lines.append(f"\n💬 شاركنا رأيك: {meta.get('pinned_question', 'ما هو رأيك في هذه الأحداث؟')}")
    desc_lines.append("\n#وثائقي #معلومات #استكشاف #حقائق #أسرار #تاريخ")
    return "\n".join(desc_lines)

# --- 9. رفع الوثائقي والصورة المصغرة والتعليق المثبت إلى يوتيوب ---
def upload_to_youtube(file_path: str, channel_key: str, meta: dict, total_duration: float):
    title = meta["title"]
    print(f"🚀 جاري رفع الوثائقي إلى يوتيوب [{channel_key}]: \"{title}\"...")
    
    client_id = os.getenv("YOUTUBE_CLIENT_ID")
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.getenv(f"REFRESH_TOKEN_{channel_key}")

    creds = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret
    )
    youtube = build("youtube", "v3", credentials=creds)
    
    description = build_seo_description(meta, total_duration)
    
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": ["وثائقي", "حقائق", "أسرار", "تاريخ", "علوم", "استكشاف"],
            "categoryId": "27"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }
    
    media = MediaFileUpload(file_path, chunksize=15*1024*1024, resumable=True)
    req = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)
    
    response = None
    while response is None:
        status, response = req.next_chunk()
        if status:
            print(f"  📊 نسبة الرفع: {int(status.progress() * 100)}%")
            
    video_id = response['id']
    print(f"🎉 تم النشر بنجاح على يوتيوب! رابط الفيديو: https://youtu.be/{video_id}")

    try:
        thumb_path = create_auto_thumbnail(file_path, meta.get("thumb_text", "وثائقي خاص"))
        youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumb_path)).execute()
        print(f"  🖼️ تم رفع الصورة المصغرة المخصصة (Custom Thumbnail) بنجاح!")
    except Exception as e:
        print(f"  ⚠️ ملاحظة الصورة المصغرة: {e}")

    try:
        comment_body = {
            "snippet": {
                "videoId": video_id,
                "topLevelComment": {
                    "snippet": {
                        "textOriginal": f"👇 {meta.get('pinned_question', 'شاركنا رأيك في التعليقات!')}"
                    }
                }
            }
        }
        youtube.commentThreads().insert(part="snippet", body=comment_body).execute()
        print(f"  💬 تم نشر التعليق التفاعلي الأول بنجاح!")
    except Exception as e:
        print(f"  ⚠️ ملاحظة التعليق: {e}")

# --- نقطة البداية ---
if __name__ == "__main__":
    channel_key = sys.argv[1] if len(sys.argv) > 1 else "MASHAREE"
    channel_names = {"ABAAD": "أبعاد جغرافية", "MASHAREE": "مشاريع عملاقة", "MASAR": "مسار"}
    channel_title = channel_names.get(channel_key, channel_key)
    
    meta = get_titan_documentary_meta(channel_title)
    duration = build_guaranteed_audio(meta["title"])
    playlist = prepare_video_footage(meta["search_keywords"], target_duration=duration)
    render_titan_documentary(playlist, "narration.mp3", channel_title, "final_documentary.mp4")
    upload_to_youtube("final_documentary.mp4", channel_key, meta, duration)
