import os
import sys
import json
import time
import random
import asyncio
import requests
import subprocess
from mutagen.mp3 import MP3
import edge_tts
import google.generativeai as genai
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# --- 1. الإعدادات واختيار نموذج Gemini الفعال ---
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_KEY = os.getenv("PEXELS_API_KEY")

genai.configure(api_key=GEMINI_KEY)

def get_active_model():
    """اختيار نموذج متاح وفعال تلقائياً لتفادي أخطاء 404"""
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
        "search_keywords": ["4", "كلمات", "بحث", "إنجليزية", "تصلح", "لفيديوهات", "pexel"]
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
            ("حدود الكوكب المجهولة: بقاع لم يطأها إنسان", "استكشاف أعمق المناطق وأكثرها عزوبة وخطورة على وجه البسيطة وأثرها على التوازن الطبيعي.", ["extreme wilderness", "mysterious mountains", "unexplored nature", "aerial drone 4k"])
        ]
        chosen = random.choice(topics)
        data = {"title": chosen[0], "topic": chosen[1], "search_keywords": chosen[2]}
        
    print(f"  💡 العنوان المختار: {data['title']}")
    return data

# --- 3. توليد سيناريو ضخم بنظام الفصول الممتدة (+2800 كلمة) ---
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

# --- 4. توليد الصوت البشري والتأكد الصارم من تجاوزه 20 دقيقة ---
async def create_voice_async(text: str, output_path: str):
    comm = edge_tts.Communicate(text, VOICE_NAME, rate="-4%", pitch="+0Hz")
    await comm.save(output_path)

def build_guaranteed_audio(title: str, topic: str) -> float:
    script_text = generate_long_script(title, topic)
    print(f"🎙️ جاري توليد التعليق الصوتي البشري عبر ({VOICE_NAME})...")
    asyncio.run(create_voice_async(script_text, "narration.mp3"))
    
    audio_info = MP3("narration.mp3")
    duration = audio_info.info.length
    print(f"🎧 مدة التعليق الصوتي الحالية: {duration / 60:.2f} دقيقة ({duration:.0f} ثانية)")
    
    # حلقة أمان: لو كان الصوت أقل من 20 دقيقة، نزيد فصول إضافية فوراً
    while duration < MIN_REQUIRED_SECONDS:
        print(f"⚠️ الصوت الحالي {duration / 60:.1f} دقيقة وهو أقل من 20 دقيقة! جاري كتابة ملحق وثائقي وتمديد الصوت...")
        extra_prompt = f"""
        اكتب فصلاً وثائقياً إضافياً مطولاً (700 كلمة) باللغة العربية الفصحى يحلل بعمق أبعاداً جديدة ومثيرة حول: "{title}".
        اكتب ما ينطقه الراوي فقط.
        """
        extra_text = model.generate_content(extra_prompt).text.strip()
        asyncio.run(create_voice_async(extra_text, "extra_part.mp3"))
        
        # دمج ملفات الصوت عبر FFmpeg
        with open("concat_audio.txt", "w", encoding="utf-8") as f:
            f.write("file 'narration.mp3'\nfile 'extra_part.mp3'\n")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "concat_audio.txt", "-c", "copy", "narration_merged.mp3"], check=True)
        os.replace("narration_merged.mp3", "narration.mp3")
        
        duration = MP3("narration.mp3").info.length
        print(f"  📈 المدة بعد التمديد: {duration / 60:.2f} دقيقة ({duration:.0f} ثانية)")
        
    print(f"✅ تم تأكيد وصول الصوت للهدف المطلوب بنجاح: {duration / 60:.2f} دقيقة!")
    return duration

# --- 5. جلب مقاطع Pexels وتكرارها لسد كامل الـ 20 دقيقة ---
def prepare_video_footage(keywords: list, target_duration: float, output_dir: str = "clips") -> str:
    print(f"🎥 جاري جلب المشاهد البصرية لتغطية مدة {target_duration / 60:.1f} دقيقة بالكامل...")
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
            
    # تنزيل ما بين 12 إلى 16 مقطعاً متنوعاً
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
            
    # إنشاء قائمة تشغيل مكررة ومبعثرة لتتجاوز مدة الصوت تماماً (Looping)
    playlist_path = "full_playlist.txt"
    with open(playlist_path, "w", encoding="utf-8") as f:
        # تكرار المشاهد بترتيب عشوائي حتى تغطي أكثر من 25 دقيقة
        loops_needed = int((target_duration // 150) + 3)
        playlist = []
        for _ in range(loops_needed):
            shuffled = downloaded_files.copy()
            random.shuffle(shuffled)
            playlist.extend(shuffled)
            
        for clip in playlist:
            f.write(f"file '{os.path.abspath(clip)}'\n")
            
    print(f"🎬 تم تجهيز قائمة مشاهد ممتدة تضمن استمرار العرض حتى آخر ثانية من الصوت!")
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

# --- 7. الرفع إلى يوتيوب بتقنية التجزئة الثابتة ---
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
    
    # 2. بناء الصوت البشري الإجباري (+20 دقيقة)
    duration = build_guaranteed_audio(meta["title"], meta["topic"])
    
    # 3. تجهيز المشاهد الممتدة
    playlist = prepare_video_footage(meta["search_keywords"], target_duration=duration)
    
    # 4. الرندر السريع
    render_long_documentary(playlist, "narration.mp3", "final_documentary.mp4")
    
    # 5. الرفع
    upload_to_youtube("final_documentary.mp4", channel_key, meta["title"], meta["topic"])
