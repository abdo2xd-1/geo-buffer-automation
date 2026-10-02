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

import google.generativeai as genai

# --- 1. الإعدادات واختيار نموذج Gemini الفعال ---
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_KEY = os.getenv("PEXELS_API_KEY")

genai.configure(api_key=GEMINI_KEY)

def get_active_model():
    """اختيار نموذج متاح وفعال تلقائياً لحسابك وتجربته فوراً"""
    candidates = [
        "gemini-3.8-flash",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro",
        "gemini-pro"
    ]
    for c in candidates:
        try:
            m = genai.GenerativeModel(c)
            # تجربة استدعاء سريع للتأكد من أن النموذج متاح وغير محظور
            m.generate_content("test")
            print(f"🎯 تم تفعيل النموذج المعتمد بنجاح: [{c}]")
            return m
        except Exception as e:
            print(f"⚠️ النموذج [{c}] غير متاح: {e}")
            continue

    # محاولة فحص قائمة النماذج الداعمة المتاحة في الحساب
    try:
        for m_info in genai.list_models():
            if "generateContent" in m_info.supported_generation_methods:
                model_name = m_info.name.replace("models/", "")
                try:
                    m = genai.GenerativeModel(model_name)
                    m.generate_content("test")
                    print(f"🎯 تم تفعيل النموذج من القائمة المتاحة: [{model_name}]")
                    return m
                except Exception:
                    continue
    except Exception as e:
        print(f"⚠️ تعذر فحص قائمة النماذج: {e}")

    return genai.GenerativeModel("gemini-3.8-flash")

model = get_active_model()
VOICE_NAME = "ar-EG-ShakirNeural"  # صوت بشري وثائقي طبيعي

# ضبط النطاق الزمني: الحد الأدنى 10 دقائق (600 ثانية)، والحد الأقصى تحت 15 دقيقة (870 ثانية)
MIN_DURATION_SECONDS = 600   # 10 دقائق كحد أدنى
MAX_SAFE_SECONDS = 870       # 14.5 دقيقة كحد أقصى آمن لتجنب حظر يوتيوب

def clean_arabic_text(text: str) -> str:
    """تنظيف النص من الرموز والماركداون لضمان نطق سليم"""
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
    print(f"🎲 جاري ابتكار فكرة وثائقية عشوائية جديدة لقناة [{channel_name}]...")
    prompt = f"""
    أنت مدير إنتاج لقناة وثائقيات اسمها "{channel_name}".
    ابتكر فكرة وثائقية جديدة تماماً وعشوائية ومثيرة للمشاهدين دون التقيد بتصنيف مسبق.
    نوّع بحرية بين: حضارات مفقودة، ألغاز جغرافية، صراعات استخباراتية، مدن تحت الأرض، كوارث غيرت العالم، تقنيات مجهولة، أو رحلات استكشافية كبرى.
    
    أخرج الرد بصيغة JSON فقط:
    {{
        "title": "عنوان وثائقي عربي تشويقي وموجز",
        "topic": "وصف شيق ومفصل للقصة الوثائقية ومحاورها",
        "search_keywords": ["4", "كلمات", "بحث", "إنجليزية", "مناسبة", "لفيديوهات", "pexels"]
    }}
    """
    try:
        res = model.generate_content(prompt)
        cleaned = res.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(cleaned)
    except Exception:
        topics = [
            ("أسرار الممالك المفقودة: مدن طمستها الرمال", "رحلة استكشافية تكشف أسرار أقدم الحضارات التي اختفت فجأة دون تفسير علمي حاسم.", ["ancient ruins 4k", "desert mystery", "archaeology", "epic landscape"]),
            ("خفايا العمليات السرية: ملفات غيرت مسار التاريخ", "كواليس وحقائق غير معلنة حول أحداث حاسمة صاغت موازين القوى العالمية خلف الأبواب المغلقة.", ["classified documents", "historical warfare", "vintage intelligence", "cinematic shadows"]),
            ("حدود الكوكب المجهولة: بقاع لم يطأها إنسان", "استكشاف أعمق المناطق وأكثرها عزلة وخطورة على وجه البسيطة وأثرها على التوازن الطبيعي.", ["extreme wilderness", "mysterious mountains", "unexplored nature", "aerial drone 4k"])
        ]
        chosen = random.choice(topics)
        data = {"title": chosen[0], "topic": chosen[1], "search_keywords": chosen[2]}
        
    print(f"  💡 العنوان المختار: {data['title']}")
    return data

# --- 3. توليد سيناريو وثائقي (من 10 إلى 14 دقيقة: ~1600 كلمة) ---
def generate_medium_script(title: str, topic: str) -> str:
    print(f"✍️ جاري صياغة السرد الوثائقي المتوازن (الهدف: 10 إلى 14 دقيقة)...")
    
    prompt = f"""
    أنت كبير كتّاب الأفلام الوثائقية التلفزيونية.
    عنوان العمل: "{title}".
    الوصف: "{topic}".
    
    المطلوب: كتابة سيناريو وثائقي كامل وشامل (مقدمة مشوقة، 4 محاور سردية عميقة بالأدلة والأسرار، وخاتمة فلسفية ملهمة).
    
    شروط ملزمة:
    1. اكتب نصاً سردياً مطولاً يتراوح بدقة بين 1500 إلى 1700 كلمة باللغة العربية الفصحى الفخمة (ليغطي تعليقاً صوتياً بين 11 و 13 دقيقة).
    2. اكتب فقط النص المقروء الذي ينطقه المعلق الصوتي دون وضع أي توجيهات إخراجية أو كلمات مثل (مشهد، راوي، فاصل، موسيقى).
    3. أسلوب سلس ومترابط ومفعم بالحقائق والمعلومات الموثقة.
    """
    
    script_text = ""
    for attempt in range(3):
        try:
            print(f"  ⏳ جاري صياغة السيناريو عبر الذكاء الاصطناعي...")
            res = model.generate_content(prompt)
            if res.text:
                cleaned = clean_arabic_text(res.text.strip())
                if len(cleaned.split()) >= 900:
                    script_text = cleaned
                    print(f"  ✅ تم إنتاج السيناريو بنجاح ({len(cleaned.split())} كلمة)!")
                    break
        except Exception as e:
            print(f"  ⚠️ خطأ في التوليد ({e})، إعادة المحاولة...")
            time.sleep(4)
            
    if not script_text:
        print("  ⚠️ استخدام سيناريو احتياطي متوازن...")
        fallback = (
            f"في عمق التاريخ وحنايا الوجود الإنساني، تقف شواهد {title} كدليل راسخ على قدرة العقل البشري على مجابهة المجهول وتجاوز الحدود التقليدية. "
            "لقد انطلقت هذه الرحلة من فكرة بسيطة سرعان ما تحولت إلى واقع فرض نفسه على مجريات الأحداث، حيث تلاقت الإرادة مع التحديات الطبيعية والتقنية المعقدة. "
            "تظهر السجلات والوثائق المحفوظة أن ما خفي من تفاصيل كان يفوق بكثير ما تم إعلانه في ذلك الحين، لتكشف لنا الدراسات المتأخرة أسراراً حاسمة. "
            "إن تفحص الأرقام الدقيقة والمسارات التي سلكها الرواد يبرز بوضوح كيف تشكلت موازين جديدة أثرت على مسار الأحداث الإنسانية دون رجعة. "
        ) * 7
        script_text = clean_arabic_text(fallback)
        
    return script_text

# --- 4. توليد الصوت البشري المجزأ وضمان مدة (10 - 14 دقيقة) ---
async def generate_chunk_edge_tts(chunk_text: str, output_file: str):
    comm = edge_tts.Communicate(chunk_text, VOICE_NAME, rate="-4%")
    await comm.save(output_file)

def build_guaranteed_audio(title: str, topic: str) -> float:
    script_text = generate_medium_script(title, topic)
    print(f"🎙️ جاري توليد التعليق الصوتي البشري عبر ({VOICE_NAME})...")
    
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
                
        if idx % 4 == 0 or idx == len(chunks):
            print(f"  🔊 اكتمل تسجيل {idx}/{len(chunks)} جزءاً من الصوت...")

    if part_files:
        with open("audio_list.txt", "w", encoding="utf-8") as f:
            for p in part_files:
                f.write(f"file '{os.path.abspath(p)}'\n")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "audio_list.txt", "-c", "copy", "narration.mp3"], check=True)
    else:
        gtts.gTTS(text="وثائقي استكشافي شامل يستعرض أهم الحقائق والتحليلات.", lang="ar").save("narration.mp3")

    duration = get_audio_duration("narration.mp3")
    print(f"🎧 مدة الصوت الحالية: {duration / 60:.2f} دقيقة ({duration:.0f} ثانية)")

    # إذا كان أقل من 10 دقائق (600 ثانية)، نمدده بإضافة جزء تكميلي
    while duration < MIN_DURATION_SECONDS:
        print(f"⚠️ الصوت الحالي {duration / 60:.1f} دقيقة (أقل من 10 دقائق)؛ جاري إضافة جزء إضافي...")
        extra_prompt = f"اكتب فقرة وثائقية تكميلية مطولة (350 كلمة) باللغة العربية الفصحى تضيف تحليلاً عميقاً حول: {title}."
        extra_text = clean_arabic_text(model.generate_content(extra_prompt).text.strip())
        
        try:
            asyncio.run(generate_chunk_edge_tts(extra_text, "extra.mp3"))
        except Exception:
            gtts.gTTS(text=extra_text, lang="ar").save("extra.mp3")
            
        with open("concat_extra.txt", "w", encoding="utf-8") as f:
            f.write(f"file '{os.path.abspath('narration.mp3')}'\nfile '{os.path.abspath('extra.mp3')}'\n")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "concat_extra.txt", "-c", "copy", "narration_final.mp3"], check=True)
        os.replace("narration_final.mp3", "narration.mp3")
        duration = get_audio_duration("narration.mp3")
        print(f"  📈 المدة المحدثة: {duration / 60:.2f} دقيقة")

    # إذا تجاوز 14.5 دقيقة بالخطأ، نقصه بأمان ليبقى تحت حد الـ 15 دقيقة
    if duration > MAX_SAFE_SECONDS:
        print(f"✂️ تقليص مدة الصوت لتصبح {MAX_SAFE_SECONDS / 60:.1f} دقيقة بالضبط لتفادي قيود يوتيوب...")
        subprocess.run(["ffmpeg", "-y", "-i", "narration.mp3", "-t", str(MAX_SAFE_SECONDS), "-c", "copy", "narration_trimmed.mp3"], check=True)
        os.replace("narration_trimmed.mp3", "narration.mp3")
        duration = get_audio_duration("narration.mp3")

    print(f"✅ تم تأكيد مدة الصوت المتوازنة بنجاح: {duration / 60:.2f} دقيقة (بين 10 و 14 دقيقة)!")
    return duration

# --- 5. جلب وتكرار مشاهد Pexels لتغطية المدة ---
def prepare_video_footage(keywords: list, target_duration: float, output_dir: str = "clips") -> str:
    print(f"🎥 جاري جلب المشاهد لتغطية مدة {target_duration / 60:.1f} دقيقة...")
    os.makedirs(output_dir, exist_ok=True)
    headers = {"Authorization": PEXELS_KEY}
    
    raw_clips = []
    for kw in keywords:
        url = f"https://api.pexels.com/videos/search?query={kw}&per_page=10&orientation=landscape"
        try:
            res = requests.get(url, headers=headers, timeout=20).json()
            for v in res.get("videos", []):
                files = v.get("video_files", [])
                chosen = next((f for f in files if f.get("width") == 1920), None) or (files[0] if files else None)
                if chosen:
                    raw_clips.append(chosen.get("link"))
        except Exception:
            continue
            
    unique_links = list(set(raw_clips))[:12]
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
        loops_needed = int((target_duration // 100) + 4)
        playlist = []
        for _ in range(loops_needed):
            shuffled = downloaded_files.copy()
            random.shuffle(shuffled)
            playlist.extend(shuffled)
            
        for clip in playlist:
            f.write(f"file '{os.path.abspath(clip)}'\n")
            
    return playlist_path

# --- 6. رندر ومونتاج FFmpeg المحمي ضد التجمد وتكرار الإطارات ---
def render_long_documentary(playlist_path: str, audio_path: str, output_path: str = "final_documentary.mp4"):
    print("⚙️ جاري دمج ومونتاج الوثائقي عبر FFmpeg (رندر سريع وثابت الإطارات)...")
    
    cmd = [
        "ffmpeg", "-y",
        "-fflags", "+genpts",
        "-f", "concat", "-safe", "0", "-i", playlist_path,
        "-i", audio_path,
        "-vf", "fps=25,scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
        "-c:a", "aac", "-b:a", "192k",
        "-max_muxing_queue_size", "1024",
        "-shortest",
        output_path
    ]
    subprocess.run(cmd, check=True)
    print(f"🏆 اكتمل إنتاج الوثائقي بنجاح وبدون أي تعليق: {output_path}")

# --- 7. رفع الوثائقي إلى يوتيوب بالتجزئة ---
def upload_to_youtube(file_path: str, channel_key: str, title: str, description: str):
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
    
    # 1. فكرة عشوائية فريدة
    meta = get_random_topic(channel_title)
    
    # 2. بناء الصوت البشري (بين 10 إلى 14 دقيقة بدقة)
    duration = build_guaranteed_audio(meta["title"], meta["topic"])
    
    # 3. تجهيز المشاهد الممتدة
    playlist = prepare_video_footage(meta["search_keywords"], target_duration=duration)
    
    # 4. الرندر السريع والثابت
    render_long_documentary(playlist, "narration.mp3", "final_documentary.mp4")
    
    # 5. الرفع إلى يوتيوب ونشره كفيديو عام فوراً
    upload_to_youtube("final_documentary.mp4", channel_key, meta["title"], meta["topic"])
