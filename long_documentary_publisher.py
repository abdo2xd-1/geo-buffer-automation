import os
import sys
import json
import time
import random
import asyncio
import requests
import subprocess
import edge_tts
import google.generativeai as genai
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# --- 1. الإعدادات واختيار نموذج Gemini المتاح ---
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_KEY = os.getenv("PEXELS_API_KEY")

genai.configure(api_key=GEMINI_KEY)

def get_active_model():
    """اختيار نموذج نشط تلقائياً لحسابك لتفادي أخطاء 404"""
    models_to_try = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro",
        "gemini-pro"
    ]
    try:
        available = [m.name.replace("models/", "") for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
        for m in models_to_try:
            if m in available:
                print(f"🎯 تم تفعيل النموذج: [{m}]")
                return genai.GenerativeModel(m)
        if available:
            return genai.GenerativeModel(available[0])
    except Exception:
        pass
    return genai.GenerativeModel("gemini-2.0-flash")

model = get_active_model()
VOICE_NAME = "ar-EG-ShakirNeural"  # صوت بشري وثائقي طبيعي
MIN_REQUIRED_SECONDS = 1200        # الحد الأدنى الصارم: 20 دقيقة (1200 ثانية)

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
    أنت مدير محتوى لقناة وثائقية عالمية اسمها "{channel_name}".
    ابتكر فكرة وثائقية جديدة تماماً ومثيرة للمشاهدين وغير مكررة بدون التقيد بتصنيف معين.
    نوّع بحرية بين: حضارات مجهولة، ألغاز علمية وجغرافية، صراعات استخباراتية، مدن تحت الأرض، كوارث غيرت العالم، تقنيات مجهولة، أو رحلات استكشافية كبرى.
    
    أخرج الرد بصيغة JSON فقط:
    {{
        "title": "عنوان وثائقي عربي جذاب وقصير",
        "topic": "وصف شيق ومفصل للقصة الوثائقية",
        "search_keywords": ["4", "كلمات", "بحث", "إنجليزية", "تصلح", "لفيديوهات", "pexels"]
    }}
    """
    try:
        res = model.generate_content(prompt)
        cleaned = res.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(cleaned)
    except Exception:
        topics = [
            ("أسرار الممالك المفقودة: مدن طمستها الرمال", "رحلة استكشافية تكشف أسرار أقدم الحضارات التي اختفت فجأة دون تفسير علمي حاسم.", ["ancient ruins", "desert mystery", "archaeology", "epic landscape"]),
            ("خفايا العمليات السرية: ملفات غيرت مسار التاريخ", "كواليس وحقائق غير معلنة حول أحداث حاسمة صاغت موازين القوى العالمية خلف الأبواب المغلقة.", ["classified documents", "historical warfare", "vintage intelligence", "cinematic shadows"]),
            ("حدود الكوكب المجهولة: بقاع لم يطأها إنسان", "استكشاف أعمق المناطق وأكثرها عزلة وخطورة على وجه البسيطة وأثرها على التوازن الطبيعي.", ["extreme wilderness", "mysterious mountains", "unexplored nature", "aerial drone 4k"])
        ]
        chosen = random.choice(topics)
        data = {"title": chosen[0], "topic": chosen[1], "search_keywords": chosen[2]}
        
    print(f"  💡 العنوان المختار: {data['title']}")
    return data

# --- 3. توليد سيناريو ضخم بنظام الفصول الممتدة (+3000 كلمة) ---
def generate_long_script(title: str, topic: str) -> str:
    print(f"✍️ جاري كتابة السرد الوثائقي الطويل لضمان تخطي 20 دقيقة...")
    
    chapters = [
        "المقدمة: مدخل سردي فلسفي عميق، طرح التساؤل المريب الذي يدور حوله الوثائقي.",
        "الفصل الأول: البدايات الأولى، الجذور الخفية، وكيف تشكلت هذه الظاهرة تاريخياً.",
        "الفصل الثاني: الوثائق والشهادات غير المتداولة، مع ذكر الأرقام والتواريخ والأدلة الدقيقة.",
        "الفصل الثالث: التحديات الكبرى والأزمات التي واجهت الأطراف المعنية وكادت توقف كل شيء.",
        "الفصل الرابع: الأبعاد السياسية، الجيوسياسية، أو البيئية والاقتصادية المصاحبة.",
        "الفصل الخامس: الأسرار والفرضيات المتباينة التي حيرت الخبراء والمؤرخين حتى اليوم.",
        "الفصل السادس: تفاصيل تقنية وميدانية كاشفة تنشر لأول مرة في هذا الإطار.",
        "الخاتمة: استشراف المستقبل، الدرس المستفاد، وخلاصة مؤثرة تبقى عالقة في ذهن المشاهد."
    ]
    
    script_parts = []
    for idx, chapter in enumerate(chapters, 1):
        prompt = f"""
        أنت كبير كتّاب الأفلام الوثائقية العالمية.
        موضوع العمل: "{title}".
        تفاصيل الموضوع: "{topic}".
        الجزء المطلوب كتابته الآن: "{chapter}".
        
        شروط إلزامية:
        1. اكتب نصاً سردياً مطولاً جداً وغنياً بالمعلومات (لا يقل عن 450 كلمة لهذا الفصل حصراً).
        2. لغة عربية فصحى وثائقية فخمة ومترابطة ومشوقة.
        3. اكتب فقط النص المقروء الذي سينطقه المعلق الصوتي دون وضع توجيهات مثل (مشهد، راوي، فاصل).
        """
        for _ in range(3):
            try:
                res = model.generate_content(prompt)
                script_parts.append(res.text.strip())
                print(f"  📝 تم إنجاز الجزء {idx} من {len(chapters)}...")
                time.sleep(2)
                break
            except Exception:
                time.sleep(3)
                
    return "\n\n".join(script_parts)

# --- 4. توليد الصوت البشري المجزأ وحمايته من السقوط ---
async def generate_chunk_audio(chunk_text: str, output_file: str):
    comm = edge_tts.Communicate(chunk_text, VOICE_NAME, rate="-4%", pitch="+0Hz")
    await comm.save(output_file)

def synthesize_long_text_safe(text: str, final_output: str = "narration.mp3") -> float:
    """تقسيم النص لفقرات وتوليدها بشكل آمن ثم دمجها عبر FFmpeg"""
    words = text.split()
    chunk_size = 180  # 180 كلمة لكل ملف لضمان استقرار جلسات مايكروسوفت
    chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    
    os.makedirs("audio_parts", exist_ok=True)
    part_files = []
    
    print(f"🎙️ جاري معالجة الصوت على {len(chunks)} مقطعاً لضمان الجودة والاستقرار...")
    for idx, chunk in enumerate(chunks, 1):
        part_name = f"audio_parts/part_{idx:03d}.mp3"
        for attempt in range(3):
            try:
                asyncio.run(generate_chunk_audio(chunk, part_name))
                if os.path.exists(part_name) and os.path.getsize(part_name) > 1024:
                    part_files.append(part_name)
                    break
            except Exception as e:
                time.sleep(2)
        print(f"  🔊 تم توليد مقطع الصوت {idx}/{len(chunks)}")
        time.sleep(0.5)

    # إنشاء ملف دمج مقاطع الصوت
    with open("audio_list.txt", "w", encoding="utf-8") as f:
        for p in part_files:
            f.write(f"file '{os.path.abspath(p)}'\n")

    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "audio_list.txt", "-c", "copy", final_output], check=True)
    return get_audio_duration(final_output)

def build_guaranteed_audio(title: str, topic: str) -> float:
    script_text = generate_long_script(title, topic)
    duration = synthesize_long_text_safe(script_text, "narration.mp3")
    print(f"🎧 مدة التعليق الصوتي الإجمالية: {duration / 60:.2f} دقيقة ({duration:.0f} ثانية)")

    # في حال قل الصوت عن 20 دقيقة، توليد محتوى تكميلي إضافي
    while duration < MIN_REQUIRED_SECONDS:
        print(f"⚠️ الصوت الحالي {duration / 60:.1f} دقيقة؛ جاري إضافة ملحق وثائقي للوصول إلى 20 دقيقة...")
        extra_prompt = f"""
        اكتب فصلاً وثائقياً تكميلياً موسعاً (800 كلمة) باللغة العربية الفصحى يحلل بعمق زوايا وخفايا غير مطروحة حول: "{title}".
        اكتب نص التعليق فقط.
        """
        extra_text = model.generate_content(extra_prompt).text.strip()
        extra_dur = synthesize_long_text_safe(extra_text, "extra.mp3")
        
        with open("concat_final_audio.txt", "w", encoding="utf-8") as f:
            f.write("file 'narration.mp3'\nfile 'extra.mp3'\n")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "concat_final_audio.txt", "-c", "copy", "narration_final.mp3"], check=True)
        os.replace("narration_final.mp3", "narration.mp3")
        duration = get_audio_duration("narration.mp3")
        print(f"  📈 المدة المحدثة: {duration / 60:.2f} دقيقة")

    print(f"✅ تم تأكيد استيفاء المدة المطلوبة بنجاح: {duration / 60:.2f} دقيقة!")
    return duration

# --- 5. جلب مشاهد Pexels وتكرارها لتغطية المدة ---
def prepare_video_footage(keywords: list, target_duration: float, output_dir: str = "clips") -> str:
    print(f"🎥 جاري جلب المشاهد البصرية لتغطية مدة {target_duration / 60:.1f} دقيقة بالكامل...")
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
            
    # إنشاء قائمة تشغيل متكررة تغطي كامل مدة الصوت
    playlist_path = "full_playlist.txt"
    with open(playlist_path, "w", encoding="utf-8") as f:
        loops_needed = int((target_duration // 150) + 3)
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
    print("⚙️ جاري دمج ومونتاج الوثائقي الطويل عبر FFmpeg...")
    
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
    
    # 1. فكرة عشوائية
    meta = get_random_topic(channel_title)
    
    # 2. بناء الصوت البشري المجزأ والآمن (+20 دقيقة)
    duration = build_guaranteed_audio(meta["title"], meta["topic"])
    
    # 3. تجهيز المشاهد الممتدة
    playlist = prepare_video_footage(meta["search_keywords"], target_duration=duration)
    
    # 4. الرندر السريع
    render_long_documentary(playlist, "narration.mp3", "final_documentary.mp4")
    
    # 5. الرفع
    upload_to_youtube("final_documentary.mp4", channel_key, meta["title"], meta["topic"])
