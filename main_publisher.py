import os
import sys
import re
import json
import time
import random
import datetime
import asyncio
import requests
import subprocess

# تثبيت المكتبات الاحتياطية تلقائياً
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

try:
    import google.generativeai as genai
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "google-generativeai"])
    import google.generativeai as genai

# --- 1. مفاتيح التشغيل واختيار النموذج الذكي ---
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_KEY = os.getenv("PEXELS_API_KEY")
BUFFER_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if GEMINI_KEY:
    try:
        genai.configure(api_key=GEMINI_KEY)
    except Exception:
        pass

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

def send_telegram_alert(message: str):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
            requests.post(url, json=payload, timeout=10)
        except Exception:
            pass

# --- 2. خريطة القنوات والتصنيفات المتغيرة يومياً لمنع التكرار ---
CHANNELS_MAP = {
    "MASAR": {"id": "6abace7bea19ca0bde181dff", "name": "مسار | Masar", "index": 0},
    "MASHAREE": {"id": "6abace11ea19ca0bde181821", "name": "مشاريع عملاقة | MegaBuilds", "index": 1},
    "ABAAD": {"id": "6abacd06ea19ca0bde180ef9", "name": "أبعاد جغرافية | Abaad", "index": 2}
}

CATEGORIES = [
    "حضارات قديمة منسية وآثار ومخطوطات محرمة",
    "منشآت عسكرية تحت الأرض ومدن سرية محظورة",
    "ظواهر كونية وفلكية وأجرام فضائية مجهولة",
    "أعماق المحيطات وأغرب المخلوقات والخنادق المائية السحيقة",
    "كوارث تاريخية غامضة وحوادث اختفاء لم تُحل حتى اليوم",
    "عجائب هندسية عملاقة مهجورة ومشاريع خيالية سابقة لعصرها",
    "أسرار علمية وتجارب فيزيائية كادت تدمر الكوكب",
    "جزر نائية محرمة على البشر وقبائل معزولة عن العالم",
    "معالم جغرافية صادمة وتضاريس غريبة كأنها من كوكب آخر",
    "مفارقات تاريخية ووثائق استخباراتية سرية رُفعت عنها السرية",
    "مدن غارقة تحت الماء وحضارات ابتلعها البحر",
    "ألغاز الثروات والكنوز المفقودة التي اختفى كل من بحث عنها"
]

# بنك طوارئ مستقل تماماً لكل قناة (مستحيل قناة تأخذ فكرة الأخرى)
FALLBACK_BANKS = {
    "MASAR": [
        {
            "title": "مخطوطة فوينيتش: النص الذي عجزت عنه البشرية! 📜",
            "script": "هذا الكتاب الغامض حير أعظم علماء التشفير وأجهزة الاستخبارات لعقود طويلة. كُتب بلغة مجهولة ورسومات لنباتات لا وجود لها على كوكبنا، ولم يستطع أي حاسوب فك رموزه حتى اليوم، ليبقى السؤال قائماً: من كتب هذا الكتاب الغامض...",
            "scene_keywords": ["ancient manuscript vintage", "mysterious book pages", "cryptography symbols", "ancient library dark", "medieval history"]
        },
        {
            "title": "جيش التراكوتا: لغز الإمبراطور الأول! ⚔️",
            "script": "آلاف الجنود المصنوعين من الطين يقفون تحت الأرض لحراسة قبر إمبراطور الصين الأول. المفاجأة أن ملامح كل جندي تختلف تماماً عن الآخر، ولا يزال القبر الرئيسي مغلقاً حتى اليوم خوفاً من أنهار الزئبق السامة التي تحيط بجيش التراكوتا...",
            "scene_keywords": ["terracotta army china", "ancient tomb underground", "emperor mausoleum", "chinese history archaeology", "dark ancient chamber"]
        },
        {
            "title": "مدينة البتراء: اللغز المنحوت في الصخر! 🏛️",
            "script": "مدينة كاملة نُحتت بدقة إعجازية في قلب الجبال الوردية، دون استخدام أي معدات حديثة. الأنباط شيدوا نظام مياه سري جعلها واحة وسط الصحراء القاحلة، قبل أن يختفوا فجأة دون أن يتركوا أي وثيقة تشرح سر مدينة البتراء...",
            "scene_keywords": ["petra jordan ancient", "rock carved temple", "desert canyon aerial", "ancient civilization architecture", "middle east history"]
        }
    ],
    "MASHAREE": [
        {
            "title": "مدينة ديرينكويو: أعظم لغز تحت الأرض! 🕳️",
            "script": "مدينة عملاقة تحت الأرض بعمق ثمانية عشر طابقاً كانت تتسع لعشرين ألف إنسان مع ماشيتهم ومؤنهم. بنيت بفتحات تهوية إعجازية وأبواب حجرية لا تفتح إلا من الداخل، ولا أحد يعرف بدقة من بدأ بحفر هذه المدينة العملاقة...",
            "scene_keywords": ["derinkuyu underground city", "ancient stone tunnels", "deep cavern darkness", "subterranean complex", "cappadocia underground"]
        },
        {
            "title": "مشروع كولا العملاق: أعمق حفرة على الأرض! 🌋",
            "script": "أعمق حفرة حفرها البشر في التاريخ وصلت إلى عمق اثني عشر كيلومتراً في القشرة الأرضية. العلماء سجلوا درجات حرارة خيالية وغازات غير مسبوقة قبل أن تتوقف أعمال الحفر فجأة بسبب أصوات مريبة سُجلت في أعمق حفرة...",
            "scene_keywords": ["deep drilling rig arctic", "drilling core hole", "dark abyss underground", "scientific industrial machine", "extreme geology"]
        },
        {
            "title": "سد الممرات الثلاثة: المشروع الذي أبطأ دوران الأرض! ⚡",
            "script": "أضخم سد كهرومائي عرفته البشرية يحجز وراءه مليارات الأطنان من المياه. العلماء أكدوا أن وزنه الهائل أدى إلى إبطاء دوران كوكب الأرض بجزء من الثانية، مما يجعله المشروع الأكثر تأثيراً على الجغرافيا في تاريخ هذا السد...",
            "scene_keywords": ["three gorges dam aerial", "massive hydro dam water", "megastructure engineering", "river flooding powerful", "industrial aerial view"]
        }
    ],
    "ABAAD": [
        {
            "title": "خندق ماريانا: أعمق نقطة على كوكب الأرض! 🌊",
            "script": "في هذا العمق السحيق الذي يتجاوز أحد عشر كيلومتراً، يعادل الضغط وزن آلاف الأطنان على الإنش الواحد. في هذا الظلام الدامس اكتشف العلماء كائنات شفافة تعيش في ظروف مستحيلة لم يتخيل العلم وجودها في هذا العمق السحيق...",
            "scene_keywords": ["mariana trench deep ocean", "abyssal sea creature", "dark underwater pressure", "submarine explore trench", "ocean darkness depth"]
        },
        {
            "title": "عين الصحراء: اللغز الجيولوجي الفضائي! 👁️",
            "script": "تكوين جيولوجي دائري عملاق في صحراء موريتانيا يبلغ قطره أربعين كيلومتراً ولا يظهر بوضوح إلا من الفضاء. دوائر متحدة المركز حيرت العلماء في تفسير سبب تشكلها، ليبقى السؤال: هل هو نيزك أم بركان أم بقايا حضارة عين الصحراء...",
            "scene_keywords": ["richat structure mauritania", "eye of the sahara space", "desert anomaly aerial", "circular geological crater", "sahara golden dunes"]
        },
        {
            "title": "شلالات الدم في القارة القطبية! 🩸",
            "script": "وسط صقيع أنتاركتيكا المتجمد، يتدفق شلال لونه أحمر قاني كالدماء على صفائح الجليد الأبيض. اللغز كشف عن بحيرة محبوسة تحت الجليد منذ مليوني عام تعيش فيها بكتيريا بلا ضوء ولا أكسجين، وهي مصدر هذه الشلالات...",
            "scene_keywords": ["blood falls antarctica", "red waterfall glacier", "frozen wilderness ice", "antarctic aerial landscape", "extreme cold nature"]
        }
    ]
}

# --- 3. محرك الذكاء الاصطناعي المقاوم للحظر الجغرافي ---
def query_ai_robust(prompt: str) -> str:
    if model:
        try:
            res = model.generate_content(prompt)
            if res and res.text:
                return res.text.strip()
        except Exception:
            pass

    try:
        url = "https://text.pollinations.ai/"
        headers = {"Content-Type": "application/json"}
        payload = {
            "messages": [
                {"role": "system", "content": "أنت خبير صناعة محتوى يوتيوب شورتس باللغة العربية الفصحى."},
                {"role": "user", "content": prompt}
            ],
            "model": "openai"
        }
        r = requests.post(url, json=payload, headers=headers, timeout=25)
        if r.status_code == 200 and r.text:
            return r.text.strip()
    except Exception:
        pass

    return ""

# --- 4. توليد المحتوى الحصري بنظام التوزيع الرياضي ---
def generate_apex_short(channel_key: str, channel_name: str) -> dict:
    day_of_year = datetime.datetime.now().timetuple().tm_yday
    ch_info = CHANNELS_MAP.get(channel_key.upper(), {"index": 0})
    ch_idx = ch_info.get("index", 0)
    
    # ضمان تصنيف مختلف ومستقل 100% لكل قناة على مدار العام
    cat_idx = (day_of_year * 4 + ch_idx) % len(CATEGORIES)
    assigned_category = CATEGORIES[cat_idx]

    print(f"🧠 [Apex Studio]: جاري هندسة فكرة وسيناريو حصري لقناة [{channel_name}] في مجال [{assigned_category}]...")

    prompt_stage1 = f"""
    أنت العقل المدبر لأكبر قنوات الوثائقيات الفيروسية العالمية (YouTube Shorts).
    قناتنا الحالية هي: "{channel_name}".
    المجال الحصري المخصص لهذه القناة اليوم هو: "{assigned_category}".
    
    قاعدة ذهبية لمنع التكرار:
    - يجب أن تكون الفكرة حصرية تماماً لقناة {channel_name} وفي نطاق ({assigned_category}).
    - ممنوع منعاً باتاً تكرار الأفكار المستهلكة أو الشائعة (مثل: أهرامات الجيزة، مثلث برمودا، حفرة سيبيريا، بئر برهوت، جزيرة سينتينل، سور الصين).
    - ركّز على قصة غامضة أو واقعة غير متوقعة لم يسمع بها أغلب المشاهدين.
    
    شروط السرد الفيروسي (Infinite Loop):
    1. Hook الصدمة (أول ثانيتين): جملة تجعل المشاهد يتوقف فوراً عن التمرير.
    2. الحبكة: سرد سريع لمعلومات تاريخية أو علمية موثقة ومثيرة للذهول.
    3. The Infinite Loop: اربط الكلمة الأخيرة في السيناريو ببداية الجملة الأولى ليكتمل المعنى ويعيد الفيديو تشغيل نفسه بلا نهاية.
    4. الطول: من 65 إلى 80 كلمة فقط (ليكون زمن الصوت بين 30 إلى 40 ثانية).
    5. حدد 5 عبارات بحث بصرية سينمائية بالإنجليزية تناسب مقاطع Pexels.
    
    أخرج الرد بصيغة JSON حصراً:
    {{
        "title": "عنوان مثير مع إيموجي",
        "script": "النص المنطوق فقط بدون أي توجيهات",
        "scene_keywords": ["keyword 1", "keyword 2", "keyword 3", "keyword 4", "keyword 5"]
    }}
    """
    ai_raw = query_ai_robust(prompt_stage1)
    if ai_raw:
        try:
            cleaned = ai_raw.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)
            print(f"  💡 العنوان المعتمد لـ [{channel_name}]: {data['title']}")
            return data
        except Exception:
            pass

    # بنك الطوارئ الحصري لكل قناة (لا يوجد أي تكرار بين القنوات)
    bank = FALLBACK_BANKS.get(channel_key.upper(), FALLBACK_BANKS["MASAR"])
    data = random.choice(bank)
    print(f"  💡 العنوان المعتمد من البنك الحصري لـ [{channel_name}]: {data['title']}")
    return data

# --- 5. توليد الصوت البشري الفخم ---
async def generate_short_voice_async(text: str, output_path: str):
    comm = edge_tts.Communicate(text, VOICE_NAME, rate="-2%")
    await comm.save(output_path)

def create_short_audio(script_text: str, output_path: str) -> float:
    print(f"🎙️ جاري توليد التعليق الصوتي الوثائقي الإذاعي ({VOICE_NAME})...")
    cleaned = clean_arabic_text(script_text)
    try:
        asyncio.run(generate_short_voice_async(cleaned, output_path))
    except Exception:
        gtts.gTTS(text=cleaned, lang="ar").save(output_path)
        
    dur = get_audio_duration(output_path)
    print(f"🎧 مدة الصوت: {dur:.1f} ثانية")
    return dur

# --- 6. تنزيل ومعالجة المقاطع لمنع الشاشة السوداء نهائياً ---
def download_vertical_clips(keywords: list, target_duration: float, output_dir: str) -> str:
    print(f"📱 جاري جلب وتوحيد اللقطات السينمائية لمنع أي شاشة سوداء بين المقاطع...")
    os.makedirs(output_dir, exist_ok=True)
    headers = {"Authorization": PEXELS_KEY}
    
    normalized_files = []
    clip_counter = 0
    total_footage_sec = 0.0
    
    for kw in keywords:
        if total_footage_sec >= target_duration + 10:
            break
        url = f"https://api.pexels.com/videos/search?query={kw}&per_page=6&orientation=portrait"
        try:
            res = requests.get(url, headers=headers, timeout=20).json()
            for v in res.get("videos", []):
                if total_footage_sec >= target_duration + 10:
                    break
                files = v.get("video_files", [])
                chosen = next((f for f in files if f.get("height", 0) > f.get("width", 0)), None) or (files[0] if files else None)
                if not chosen:
                    continue
                    
                raw_path = os.path.join(output_dir, f"raw_{clip_counter:02d}.mp4")
                norm_path = os.path.join(output_dir, f"norm_{clip_counter:02d}.mp4")
                
                # تحميل الملف الأصلي
                r = requests.get(chosen.get("link"), stream=True, timeout=30)
                with open(raw_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        f.write(chunk)
                
                # توحيد الكليب: تجريد الصوت + توحيد المقاس 1080x1920 + 30fps
                conv_cmd = [
                    "ffmpeg", "-y", "-i", raw_path,
                    "-an",
                    "-vf", "fps=30,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,format=yuv420p",
                    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "24",
                    norm_path
                ]
                subprocess.run(conv_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                if os.path.exists(norm_path) and os.path.getsize(norm_path) > 1024:
                    dur = get_audio_duration(norm_path)
                    normalized_files.append(norm_path)
                    total_footage_sec += dur
                    clip_counter += 1
                
                if os.path.exists(raw_path):
                    os.remove(raw_path)
        except Exception:
            continue
            
    playlist_path = os.path.join(output_dir, "short_playlist.txt")
    with open(playlist_path, "w", encoding="utf-8") as f:
        loops_needed = max(2, int((target_duration // max(1, total_footage_sec)) + 2))
        extended_list = (normalized_files * loops_needed)
        for clip in extended_list:
            f.write(f"file '{os.path.abspath(clip)}'\n")
            
    return playlist_path

# --- 7. الترجمة المتحركة بنمط الكاريوكي الفسفوري ثلاثي الأبعاد ---
def generate_karaoke_ass(script_text: str, total_duration: float, output_ass: str = "subs.ass") -> str:
    words = script_text.split()
    if not words:
        words = [script_text]
        
    chunk_size = 3
    chunks = [words[i:i + chunk_size] for i in range(0, len(words), chunk_size)]
    time_per_chunk = max(1.0, total_duration / len(chunks))
    
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,72,&H0000FFFF,&H000000FF,&H00000000,&HB0000000,-1,0,0,0,100,100,0,0,1,7,5,2,40,40,440,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    current_time = 0.3
    for chunk in chunks:
        start_t = current_time
        end_t = min(total_duration, current_time + time_per_chunk)
        start_str = f"0:{int(start_t//60):02d}:{start_t%60:05.2f}"
        end_str = f"0:{int(end_t//60):02d}:{end_t%60:05.2f}"
        line_text = clean_arabic_text(" ".join(chunk))
        events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{{\\b1\\c&H00FFFF&}}{line_text}{{\\r}}")
        current_time = end_t

    with open(output_ass, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events))
    return output_ass

# --- 8. هندسة صوتية ثلاثية الطبقات ---
def generate_apex_soundtrack(duration: float, output_path: str = "soundtrack.mp3"):
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "sine=frequency=46:sample_rate=44100",
        "-f", "lavfi", "-i", "sine=frequency=64:sample_rate=44100",
        "-filter_complex",
        "[0:a]volume=0.07[amb];"
        "[1:a]tremolo=f=1.6:d=0.75,lowpass=f=180,volume=0.10[pulse];"
        "anoisesrc=d=2:c=pink:r=44100,lowpass=f=95,volume=0.22[drop];"
        "[amb][pulse]amix=inputs=2[bed];"
        "[bed][drop]amix=inputs=2:duration=first[aout]",
        "-map", "[aout]",
        "-t", str(duration + 2),
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_path

# --- 9. رندر سينمائي بحبيبات الفيلم (Noise) وشريط التقدم ---
def render_apex_short(playlist_path: str, voice_path: str, script_text: str, channel_name: str, output_path: str):
    print("🎬 [Render]: جاري تطبيق المونتاج السينمائي بحبيبات الفيلم 35mm والانتقالات السلسة...")
    voice_dur = get_audio_duration(voice_path)
    sfx_path = generate_apex_soundtrack(voice_dur, "sfx.mp3")
    ass_path = generate_karaoke_ass(script_text, voice_dur, "subs.ass")

    audio_chain = (
        "[1:a]highpass=f=75,equalizer=f=120:width_type=o:width=1.6:g=4.2,"
        "equalizer=f=3500:width_type=o:width=1.3:g=3.0,loudnorm=I=-14:TP=-1.5:LRA=7[voice];"
        "[2:a]volume=0.10[sfx];"
        "[voice][sfx]amix=inputs=2:duration=first:dropout_transition=2[aout]"
    )

    clean_channel_tag = clean_arabic_text(channel_name.split('|')[0].strip())

    # تلوين + تظليل + حبيبات فيلم (Noise) + شعار مائي + ترجمة + شريط تقدم
    video_chain = (
        "[0:v]eq=contrast=1.16:saturation=1.24:brightness=-0.01,vignette=angle=0.45,"
        "noise=alls=10:allf=t+u,"
        f"drawtext=text='{clean_channel_tag}':fontcolor=white@0.35:fontsize=36:x=50:y=70:box=1:boxcolor=black@0.25:boxborderw=10,"
        f"subtitles={ass_path}[vgraded];"
        f"color=c=yellow:s=1080x14[pbar];"
        f"[vgraded][pbar]overlay=x='-W+W*(t/{voice_dur:.2f})':y=H-14:shortest=1[vout]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", playlist_path,
        "-i", voice_path,
        "-i", sfx_path,
        "-t", str(voice_dur),
        "-filter_complex", f"{video_chain};{audio_chain}",
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "25",
        "-c:a", "aac", "-b:a", "192k",
        "-max_muxing_queue_size", "1024",
        output_path
    ]
    subprocess.run(cmd, check=True)
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"🏆 اكتمل إنتاج فيلم الشورتس بنجاح: {output_path} ({size_mb:.1f} ميجابايت)")

# --- 10. الرفع برابط مباشر موثوق ---
def get_public_video_url(file_path: str) -> str:
    print(f"🌐 جاري رفع الفيديو للحصول على رابط مباشر لخوادم Buffer...")
    try:
        cmd = ["curl", "-s", "-F", "reqtype=fileupload", "-F", f"fileToUpload=@{file_path}", "https://catbox.moe/user/api.php"]
        res = subprocess.check_output(cmd, timeout=60).decode().strip()
        if res.startswith("http") and ".mp4" in res:
            print(f"  🔗 تم الرفع بنجاح عبر Catbox: {res}")
            return res
    except Exception as e:
        print(f"⚠️ Catbox: {e}")

    try:
        cmd = ["curl", "-s", "-F", "reqtype=fileupload", "-F", "time=24h", "-F", f"fileToUpload=@{file_path}", "https://litterbox.catbox.moe/resources/internals/api.php"]
        res = subprocess.check_output(cmd, timeout=60).decode().strip()
        if res.startswith("http"):
            print(f"  🔗 تم الرفع بنجاح عبر Litterbox: {res}")
            return res
    except Exception as e:
        print(f"⚠️ Litterbox: {e}")

    try:
        cmd = ["curl", "-s", "-F", f"files[]=@{file_path}", "https://uguu.se/upload"]
        res_raw = subprocess.check_output(cmd, timeout=60).decode().strip()
        data = json.loads(res_raw)
        if data.get("success") and data.get("files"):
            url = data["files"][0].get("url")
            print(f"  🔗 تم الرفع بنجاح عبر Uguu: {url}")
            return url
    except Exception as e:
        print(f"⚠️ Uguu: {e}")

    return ""

# --- 11. قنوات Buffer ودعم الـ Matrix المباشر ---
def get_target_channels(channel_arg=None):
    if channel_arg and channel_arg.upper() in CHANNELS_MAP:
        return [CHANNELS_MAP[channel_arg.upper()]]
    return list(CHANNELS_MAP.values())

def send_short_to_channel(channel_id: str, channel_name: str, video_url: str, title: str) -> bool:
    graphql_url = "https://api.buffer.com"
    headers = {"Authorization": f"Bearer {BUFFER_TOKEN}", "Content-Type": "application/json"}
    caption_text = f"{title}\n\nهل كنت تعلم هذه المعلومة من قبل؟ شاركنا رأيك في التعليقات! 👇\n\n#Shorts #shorts #معلومات #حقائق #وثائقي #استكشاف"

    mutation_query = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess {
          post {
            id
          }
        }
        ... on MutationError {
          message
        }
      }
    }
    """

    inp_data = {
        "channelId": channel_id,
        "text": caption_text,
        "schedulingType": "automatic",
        "mode": "shareNow",
        "assets": [{"video": {"url": video_url}}],
        "metadata": {
            "youtube": {
                "title": title[:100],
                "categoryId": "27",
                "privacy": "public",
                "madeForKids": False
            }
        }
    }

    payload = {
        "query": mutation_query,
        "variables": {"input": inp_data}
    }

    try:
        res = requests.post(graphql_url, json=payload, headers=headers, timeout=40)
        res_data = res.json()
        data_result = res_data.get("data", {}).get("createPost", {})
        post_info = data_result.get("post")

        if post_info and post_info.get("id"):
            print(f"  🎉 تم النشر بنجاح على [{channel_name}]! Post ID: {post_info.get('id')}")
            send_telegram_alert(f"🚀 <b>تم نشر شورتس جديد!</b>\n📺 القناة: {channel_name}\n📌 العنوان: {title}\n🔗 الرابط: {video_url}")
            return True
        else:
            print(f"  ⚠️ استجابة Buffer: {data_result.get('message') or res_data.get('errors')}")
    except Exception as e:
        print(f"  ⚠️ خطأ اتصال: {e}")

    return False

# --- نقطة البداية الداعمة للـ Matrix والتشغيل الفردي ---
if __name__ == "__main__":
    if not BUFFER_TOKEN:
        print("❌ خطأ: متغير BUFFER_ACCESS_TOKEN غير موجود في إعدادات Secrets!")
        sys.exit(1)

    target_channel_key = sys.argv[1] if len(sys.argv) > 1 else "MASAR"
    channels = get_target_channels(target_channel_key)
    print(f"🚀 بدء أتمتة Matrix Shorts لقناة [{target_channel_key}]...")

    success_count = 0
    for idx, ch in enumerate(channels, 1):
        ch_id = ch.get("id")
        ch_name = ch.get("name", f"قناة {idx}")
        print(f"\n{'='*55}")
        print(f"🎬 صناعة فيلم شورتس استثنائي وحصري لقناة [{ch_name}]")
        print(f"{'='*55}")

        short_data = generate_apex_short(target_channel_key, ch_name)
        audio_file = f"narration_{ch_id}.mp3"
        duration = create_short_audio(short_data["script"], audio_file)
        
        clips_dir = f"clips_{ch_id}"
        playlist = download_vertical_clips(short_data["scene_keywords"], target_duration=duration, output_dir=clips_dir)
        
        video_file = f"final_short_{ch_id}.mp4"
        render_apex_short(playlist, audio_file, short_data["script"], ch_name, video_file)
        
        pub_url = get_public_video_url(video_file)
        if pub_url and send_short_to_channel(ch_id, ch_name, pub_url, short_data["title"]):
            success_count += 1
        time.sleep(2)

    print(f"\n{'='*55}")
    if success_count > 0:
        print(f"🏆 تم بنجاح إنتاج ونشر الفيديو بنمط Matrix!")
    else:
        sys.exit(1)
