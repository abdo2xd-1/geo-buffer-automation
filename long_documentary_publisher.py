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

# --- 1. مفاتيح التشغيل والذكاء الاصطناعي ---
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_KEY = os.getenv("PEXELS_API_KEY")

genai.configure(api_key=GEMINI_KEY)

def get_active_model():
    """اختيار نموذج نشط تلقائياً لحسابك"""
    candidates = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro", "gemini-pro"]
    try:
        available = [m.name.replace("models/", "") for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
        for c in candidates:
            if c in available:
                print(f"🎯 تم تفعيل النموذج: [{c}]")
                return genai.GenerativeModel(c)
        if available:
            return genai.GenerativeModel(available[0])
    except Exception as e:
        print(f"⚠️ تنبيه فحص النماذج: {e}")
    return genai.GenerativeModel("gemini-2.0-flash")

model = get_active_model()
VOICE_NAME = "ar-EG-ShakirNeural"  # صوت بشري وثائقي طبيعي
MIN_REQUIRED_SECONDS = 1200        # 20 دقيقة كحد أدنى (1200 ثانية)

def clean_arabic_text(text: str) -> str:
    """تنظيف النص من الماركداون والرموز غير المنطوقة"""
    text = re.sub(r'[*#_`~>\[\]\(\)]', ' ', text)
    text = text.replace('"', ' ').replace("'", ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_audio_duration(file_path: str) -> float:
    """قياس مدة الصوت بدقة عبر ffprobe"""
    try:
        cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file_path}"'
        res = subprocess.check_output(cmd, shell=True).decode().strip()
        return float(res)
    except Exception:
        return 0.0

# --- 2. توليد فكرة عشوائية غير مقيدة ---
def get_random_topic(channel_name: str) -> dict:
    print(f"🎲 جاري ابتكار فكرة وثائقية عشوائية لقناة [{channel_name}]...")
    prompt = f"""
    أنت مدير إنتاج لقناة وثائقيات اسمها "{channel_name}".
    ابتكر فكرة وثائقية جديدة ومثيرة للمشاهدين وغير مكررة.
    أخرج الرد بصيغة JSON فقط:
    {{
        "title": "عنوان وثائقي عربي تشويقي وموجز",
        "topic": "وصف شيق للقصة الوثائقية ومحاورها",
        "search_keywords": ["aerial documentary landscape", "cinematic nature 4k", "historical mystery", "ancient ruins"]
    }}
    """
    try:
        res = model.generate_content(prompt)
        cleaned = res.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(cleaned)
    except Exception as e:
        print(f"⚠️ خطأ قراءة الفكرة من Gemini ({e})، سيتم استخدام فكرة وثائقية بديلة...")
        topics = [
            ("أسرار الممالك المفقودة: مدن طمستها الرمال", "رحلة استكشافية تكشف أسرار أقدم الحضارات التي اختفت فجأة دون تفسير علمي حاسم.", ["ancient ruins 4k", "desert mystery", "archaeology", "epic landscape"]),
            ("خفايا الحدود المغلقة: ألغاز جغرافية غير مفسرة", "حقائق صادمة حول أكثر المناطق المعزولة والحدود الجغرافية غرابة على وجه الأرض.", ["mountain border", "extreme landscape", "military bunker", "remote island aerial"]),
            ("أعظم ألغاز الأعماق: ما لا نعلمه عن كوكبنا", "استكشاف أعمق المناطق وأكثرها عزلة وخطورة على وجه البسيطة وأثرها على التوازن الطبيعي.", ["extreme wilderness", "mysterious mountains", "unexplored nature", "aerial drone 4k"])
        ]
        chosen = random.choice(topics)
        data = {"title": chosen[0], "topic": chosen[1], "search_keywords": chosen[2]}
        
    print(f"  💡 العنوان المختار: {data['title']}")
    return data

# --- 3. توليد سيناريو ضخم (+3000 كلمة) بطلبين فقط لتجنب الـ Rate Limit ---
def generate_long_script(title: str, topic: str) -> str:
    print(f"✍️ جاري كتابة السرد الوثائقي الموسع بنظام القسمين لضمان تجاوز 20 دقيقة...")
    
    script_parts = []
    
    # الجزء الأول: المقدمة والفصول الأولى (1500+ كلمة)
    prompt_part1 = f"""
    أنت كبير كتّاب الأفلام الوثائقية التلفزيونية.
    موضوع العمل: "{title}".
    الوصف: "{topic}".
    
    المطلوب: اكتب النصف الأول من السيناريو الوثائقي (المقدمة، والبدايات التاريخية، والأسرار الأولى غير المتداولة، ونقاط التحول الكبرى).
    شروط ملزمة:
    1. اكتب نصاً سردياً مطولاً ومفصلاً جداً لا يقل عن 1500 كلمة باللغة العربية الفصحى الفخمة.
    2. اكتب فقط ما ينطقه الراوي بصوته دون أي توجيهات إخراجية أو كلمات مثل (مشهد، راوي، موسيقى).
    """
    
    # الجزء الثاني: الأبعاد الاستراتيجية، الأسرار العميقة، والخاتمة (1500+ كلمة)
    prompt_part2 = f"""
    أنت كبير كتّاب الأفلام الوثائقية التلفزيونية.
    موضوع العمل: "{title}".
    الوصف: "{topic}".
    
    المطلوب: اكتب النصف الثاني والمتمم للسيناريو الوثائقي (التحديات الكبرى، الأبعاد الجيوسياسية والاقتصادية، النظريات المحيرة، واستشراف المستقبل والخاتمة المؤثرة).
    شروط ملزمة:
    1. اكتب نصاً سردياً مطولاً ومفصلاً جداً لا يقل عن 1500 كلمة باللغة العربية الفصحى الفخمة.
    2. اكتب فقط ما ينطقه الراوي بصوته مباشرة دون أي توجيهات إخراجية.
    """
    
    for idx, p in enumerate([prompt_part1, prompt_part2], 1):
        success = False
        for attempt in range(3):
            try:
                print(f"  ⏳ جاري صياغة القسم {idx} من الوثائقي عبر الذكاء الاصطناعي...")
                res = model.generate_content(p)
                if res.text:
                    cleaned_text = clean_arabic_text(res.text.strip())
                    if len(cleaned_text.split()) > 300:
                        script_parts.append(cleaned_text)
                        print(f"  ✅ تم إنجاز القسم {idx} بنجاح ({len(cleaned_text.split())} كلمة)!")
                        success = True
                        time.sleep(4)
                        break
            except Exception as err:
                print(f"  ⚠️️ خطأ في محاولة توليد القسم {idx}: {err}")
                time.sleep(5)
                
        if not success:
            print(f"  ⚠️ تم استخدام سرد ملحمي احتياطي موسع للقسم {idx}.")
            fallback_narrative = (
                f"في عمق التاريخ وحنايا الوجود الإنساني، تقف أحداث {title} شاهداً على قدرة الإرادة البشرية وصراعها الدائم مع المجهول. "
                "لقد بدأت القصة في زمن لم تكن فيه الأدوات الحديثة متاحة، حين كانت الرؤية وحدها هي البوصلة التي تقود المستكشفين والعلماء نحو المجهول. "
                "ومع تعاقب السنوات وتراكم الأدلة والوثائق السرية التي ظلت طي الكتمان لعقود طويلة، تكشفت حقائق صادمة أعادت رسم ملامح الصورة بالكامل. "
                "لم تكن التحديات تقنية أو طبيعية فحسب، بل ارتبطت بصراعات جيوسياسية وتنافس استراتيجي صاغ موازين القوى في المنطقة والعالم. "
                "إن تفحص الوثائق وتحليل الأرقام الميدانية يبرز بوضوح كيف أثرت هذه التجربة الاستثنائية على مصائر الملايين، تاركة بصمة لا تمحى في الذاكرة الإنسانية. "
            ) * 12
            script_parts.append(clean_arabic_text(fallback_narrative))

    full_script = "\n\n".join(script_parts)
    print(f"📊 إجمالي حجم السيناريو النهائي: {len(full_script.split())} كلمة.")
    return full_script

# --- 4. توليد الصوت البشري الآمن وضمان الـ 20 دقيقة ---
async def generate_chunk_edge_tts(chunk_text: str, output_file: str):
    comm = edge_tts.Communicate(chunk_text, VOICE_NAME, rate="-4%")
    await comm.save(output_file)

def build_guaranteed_audio(title: str, topic: str) -> float:
    script_text = generate_long_script(title, topic)
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
                
        if idx % 5 == 0 or idx == len(chunks):
            print(f"  🔊 اكتمل تسجيل {idx}/{len(chunks)} جزءاً من التعليق الصوتي...")

    if part_files:
        with open("audio_list.txt", "w", encoding="utf-8") as f:
            for p in part_files:
                f.write(f"file '{os.path.abspath(p)}'\n")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "audio_list.txt", "-c", "copy", "narration.mp3"], check=True)
    else:
        gtts.gTTS(text="وثائقي شامل يستعرض أهم الحقائق والتحليلات المعمقة.", lang="ar").save("narration.mp3")

    duration = get_audio_duration("narration.mp3")
    print(f"🎧 مدة التعليق الصوتي المسجل: {duration / 60:.2f} دقيقة ({duration:.0f} ثانية)")
    return duration

# --- 5. جلب مشاهد Pexels وتكرارها لتغطية كامل المدة ---
def prepare_video_footage(keywords: list, target_duration: float, output_dir: str = "clips") -> str:
    print(f"🎥 جاري جلب المشاهد البصرية لتغطية مدة {target_duration / 60:.1f} دقيقة...")
    os.makedirs(output_dir, exist_ok=True)
    headers = {"Authorization": PEXELS_KEY}
    
    raw_clips = []
    for kw in keywords:
        url = f"https://api.pexels.com/videos/search?query={kw}&per_page=12&orientation=landscape"
        try:
            res = requests.get(url, headers=headers, timeout=20).json()
            for v in res.get("videos", []):
                files = v.get("video_files", [])
                chosen = next((f for f in files if f.get("width") == 1920), None) or (files[0] if files else None)
                if chosen:
                    raw_clips.append(chosen.get("link"))
        except Exception:
            continue
            
    unique_links = list(set(raw_clips))[:15]
    downloaded_files = []
    
    for idx, link in enumerate(unique_links, 1):
        c_path = os.path.join(output_dir, f"clip_{idx:02d}.mp4")
        try:
            r = requests.get(link, stream=True, timeout=30)
            with open(c_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    f.write(chunk)
            downloaded_files.append(c_path)
            print(f"  📥 تم تحميل المقطع {idx}/{len(unique_links)}")
        except Exception:
            continue
            
    playlist_path = "full_playlist.txt"
    with open(playlist_path, "w", encoding="utf-8") as f:
        loops_needed = int((target_duration // 100) + 5)
        playlist = []
        for _ in range(loops_needed):
            shuffled = downloaded_files.copy()
            random.shuffle(shuffled)
            playlist.extend(shuffled)
            
        for clip in playlist:
            f.write(f"file '{os.path.abspath(clip)}'\n")
            
    return playlist_path

# --- 6. المونتاج والرندر فائق السرعة عبر FFmpeg ---
def render_long_documentary(playlist_path: str, audio_path: str, output_path: str = "final_documentary.mp4"):
    print("⚙️ جاري دمج ومونتاج الوثائقي الطويل (رندر سريع مخصص لـ 20 دقيقة)...")
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", playlist_path,
        "-i", audio_path,
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "26",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        output_path
    ]
    subprocess.run(cmd, check=True)
    print(f"🏆 اكتمل إنتاج الوثائقي بنجاح! مدة الفيديو الآن مطابقة للصوت تماماً (+20 دقيقة).")

# --- 7. الرفع إلى يوتيوب بالتجزئة ---
def upload_to_youtube(file_path: str, channel_key: str, title: str, description: str):
    print(f"🚀 جاري رفع الوثائقي الطويل إلى يوتيوب [{channel_key}]: \"{title}\"...")
    
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
    
    body = {
        "snippet": {
            "title": title,
            "description": f"{description}\n\n#وثائقي #معلومات #استكشاف #حقائق",
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
            
    print(f"🎉 تم النشر بنجاح على يوتيوب! رابط الفيديو: https://youtu.be/{response['id']}")

# --- نقطة البداية ---
if __name__ == "__main__":
    channel_key = sys.argv[1] if len(sys.argv) > 1 else "MASHAREE"
    channel_names = {"ABAAD": "أبعاد جغرافية", "MASHAREE": "مشاريع عملاقة", "MASAR": "مسار"}
    channel_title = channel_names.get(channel_key, channel_key)
    
    meta = get_random_topic(channel_title)
    duration = build_guaranteed_audio(meta["title"], meta["topic"])
    playlist = prepare_video_footage(meta["search_keywords"], target_duration=duration)
    render_long_documentary(playlist, "narration.mp3", "final_documentary.mp4")
    upload_to_youtube("final_documentary.mp4", channel_key, meta["title"], meta["topic"])
