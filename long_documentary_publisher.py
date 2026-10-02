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

# --- 1. مفاتيح التشغيل واختيار النموذج تلقائياً ---
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_KEY = os.getenv("PEXELS_API_KEY")

genai.configure(api_key=GEMINI_KEY)

def select_active_gemini_model():
    """فحص واختيار أفضل نموذج متاح وفعال تلقائياً لحسابك لمنع خطأ 404"""
    preferred_models = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash-002",
        "gemini-1.5-pro",
        "gemini-pro"
    ]
    
    # محاولة جلب قائمة النماذج المتاحة من جوجل مباشرة
    try:
        available = [
            m.name.replace("models/", "") 
            for m in genai.list_models() 
            if "generateContent" in m.supported_generation_methods
        ]
        print(f"📋 النماذج المتاحة لحسابك: {available}")
        for pref in preferred_models:
            if pref in available:
                print(f"🎯 تم اختيار النموذج المعتمد: [{pref}]")
                return genai.GenerativeModel(pref)
        if available:
            print(f"🎯 تم اختيار أول نموذج داعم: [{available[0]}]")
            return genai.GenerativeModel(available[0])
    except Exception as e:
        print(f"⚠️ تعذر جلب قائمة النماذج تلقائياً ({e})، سيتم تجربة قائمة النماذج الاحتياطية...")

    # تجربة النماذج الشائعة بالترتيب
    for name in preferred_models:
        try:
            m = genai.GenerativeModel(name)
            m.generate_content("test")
            print(f"🎯 نجح الاتصال بالنموذج: [{name}]")
            return m
        except Exception:
            continue
            
    return genai.GenerativeModel("gemini-2.0-flash")

model = select_active_gemini_model()
VOICE_NAME = "ar-EG-ShakirNeural"  # صوت بشري وثائقي طبيعي

# --- 2. ابتكار فكرة وثائقية عشوائية تماماً ---
def get_random_documentary_idea(channel_name: str) -> dict:
    print(f"🎲 جاري ابتكار فكرة وثائقية عشوائية وشديدة التشويق لقناة [{channel_name}]...")
    
    prompt = f"""
    أنت مدير إنتاج تنفيذي لقناة وثائقيات اسمها "{channel_name}".
    ابتكر فكرة وثائقية جديدة تماماً وعشوائية ومثيرة للمشاهدين دون التقيد بأي تصنيف مسبق.
    
    شروط التنوع العشوائي:
    - لا تحصر نفسك في مجال مكرر (ابتعد عن الحصر في البحار أو السدود).
    - نوّع بحرية مطلقة بين: غرائب الجغرافيا، أسرار الحضارات القديمة، صراعات استخباراتية، مدن مفقودة، خفايا الاقتصاد العالمي، ألغاز الفضاء، معارك تاريخية فاصلة، تقنيات غامضة، أو كوارث غيرت مجرى التاريخ.
    
    أخرج النتيجة بصيغة JSON حصراً بدون أي نصوص أخرى:
    {{
        "title": "عنوان وثائقي عربي تشويقي وقصير",
        "description": "وصف جذاب ومختصر لموضوع الوثائقي",
        "search_keywords": ["aerial landscape", "historical mystery", "cinematic footage 4k", "epic documentary"]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        cleaned = response.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(cleaned)
    except Exception as err:
        print(f"⚠️ حدث خطأ أثناء قراءة الـ JSON ({err})، جاري استخدام فكرة عشوائية بديلة...")
        topics_pool = [
            ("أسرار الممالك المفقودة: مدن ابتلعتها الرمال", "استكشاف أعمق المدن الأثرية التي اختفت في ظروف غامضة ولم يتبق منها سوى أطلال محيرة.", ["ancient ruins 4k", "desert mystery", "archaeology", "drone history"]),
            ("خفايا الحدود المغلقة: ألغاز جغرافية حيرت العالم", "حقائق صادمة حول أكثر المناطق المعزولة والحدود الجغرافية غرابة على وجه الأرض.", ["mountain border", "extreme landscape", "military bunker", "remote island aerial"]),
            ("حرب الأكواد: كيف غيرت العمليات السرية مسار التاريخ؟", "كواليس العمليات الاستخباراتية والتقنية التي حسمت صراعات عالمية دون إطلاق رصاصة واحدة.", ["cyber tech futuristic", "server room lights", "secret documents", "vintage intelligence"])
        ]
        chosen = random.choice(topics_pool)
        data = {
            "title": chosen[0],
            "description": chosen[1],
            "search_keywords": chosen[2]
        }
    
    print(f"  💡 العنوان المختار: {data['title']}")
    return data

# --- 3. توليد سيناريو وثائقي طويل (+2800 كلمة لتجاوز 20 دقيقة) ---
def generate_full_script(title: str, description: str) -> str:
    print(f"✍️ جاري كتابة السيناريو الوثائقي المطول (هدف: +20 دقيقة تعليق)...")
    
    chapters = [
        "المقدمة: افتتاحية سردية غامضة وعميقة تطرح التساؤل الكبير وتأسر انتباه المشاهد من اللحظة الأولى.",
        "الفصل الأول: البدايات الأولى والجذور الخفية، وكيف تشكلت هذه القصة عبر التاريخ.",
        "الفصل الثاني: الوثائق والشهادات غير المعلنة، مع تفاصيل دقيقة وأرقام وحقائق غير شائعة.",
        "الفصل الثالث: نقاط التحول الكبرى، الصراعات أو التحديات المصيرية التي قلبت الموازين.",
        "الفصل الرابع: الأبعاد الاستراتيجية، الأثر الاقتصادي أو البشري الواسع الذي نتج عن ذلك.",
        "الفصل الخامس: النظريات والجدل الدائر، وأحدث الاكتشافات التي حيرت الباحثين والخبراء.",
        "الخاتمة: الدروس المستفادة، خلاصة فلسفية ملهمة، وسؤال مفتوح يترك أثراً عميقاً لدى المشاهد."
    ]
    
    script_parts = []
    for idx, chapter in enumerate(chapters, 1):
        prompt = f"""
        أنت كبير كتّاب الأفلام الوثائقية التلفزيونية.
        عنوان العمل: "{title}".
        ملخص الموضوع: "{description}".
        المطلوب كتابته الآن حصراً: "{chapter}".
        
        شروط ملزمة:
        1. اكتب نصاً سردياً مطولاً جداً وغنياً بالتفاصيل (لا يقل عن 450 كلمة لهذا الجزء).
        2. استخدم لغة عربية فصحى وثائقية فخمة وسردية مشوقة بدون حشو.
        3. اكتب فقط ما ينطقه الراوي بصوته مباشرة، وتجنب تماماً كتابة (مشهد، فاصل، راوي، موسيقى).
        """
        success = False
        for attempt in range(3):
            try:
                res = model.generate_content(prompt)
                script_parts.append(res.text.strip())
                print(f"  📝 تم إنجاز الجزء {idx} من {len(chapters)}...")
                success = True
                time.sleep(2)
                break
            except Exception as e:
                print(f"  ⚠️ محاولة {attempt+1} للجزء {idx} فشلت ({e})، إعادة المحاولة بعد 4 ثوانٍ...")
                time.sleep(4)
        if not success:
            script_parts.append(f"تستمر الأحداث والوقائع في كشف المزيد من أبعاد {title} وتأثيراتها العميقة على مسار الأحداث.")
            
    return "\n\n".join(script_parts)

# --- 4. توليد التعليق الصوتي البشري (Edge-TTS) ---
async def generate_voice_async(text: str, output_path: str):
    print(f"🎙️ جاري توليد الصوت البشري الطبيعي ({VOICE_NAME})...")
    comm = edge_tts.Communicate(text, VOICE_NAME, rate="-4%", pitch="+0Hz")
    await comm.save(output_path)

def build_voiceover(text: str, output_path: str = "narration.mp3") -> float:
    asyncio.run(generate_voice_async(text, output_path))
    audio_info = MP3(output_path)
    duration = audio_info.info.length
    print(f"🎧 مدة التعليق الصوتي الفعلي: {duration / 60:.2f} دقيقة ({duration:.1f} ثانية)")
    return duration

# --- 5. جلب مشاهد Pexels المطابقة ---
def download_matching_footage(keywords: list, target_duration: float, output_dir: str = "clips") -> list:
    print(f"🎥 جاري تحميل المشاهد لتغطية مدة {target_duration / 60:.1f} دقيقة...")
    os.makedirs(output_dir, exist_ok=True)
    headers = {"Authorization": PEXELS_KEY}
    
    downloaded = []
    total_time = 0.0
    clip_index = 0
    
    for kw in keywords:
        if total_time >= target_duration + 30:
            break
            
        url = f"https://api.pexels.com/videos/search?query={kw}&per_page=25&orientation=landscape"
        try:
            r = requests.get(url, headers=headers, timeout=25).json()
            videos = r.get("videos", [])
        except Exception:
            continue
            
        for v in videos:
            if total_time >= target_duration + 30:
                break
            files = v.get("video_files", [])
            chosen = next((f for f in files if f.get("width") == 1920), None) or (files[0] if files else None)
            if not chosen:
                continue
                
            clip_path = os.path.join(output_dir, f"clip_{clip_index:03d}.mp4")
            try:
                stream = requests.get(chosen.get("link"), stream=True, timeout=30)
                with open(clip_path, "wb") as f:
                    for chunk in stream.iter_content(chunk_size=1024*1024):
                        f.write(chunk)
                
                probe = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{clip_path}"'
                clip_dur = float(subprocess.check_output(probe, shell=True).decode().strip())
                
                downloaded.append(clip_path)
                total_time += clip_dur
                clip_index += 1
                print(f"  📥 كليب {clip_index} ({kw}) | إجمالي المدة: {total_time / 60:.1f} دقيقة")
            except Exception:
                continue

    return downloaded

# --- 6. رندر ومونتاج FFmpeg السريع ---
def assemble_documentary(clips: list, audio_path: str, output_path: str = "final_documentary.mp4"):
    print("🎬 جاري المونتاج ودمج الصوت والمشاهد عبر FFmpeg...")
    
    with open("clips_list.txt", "w", encoding="utf-8") as f:
        for c in clips:
            f.write(f"file '{os.path.abspath(c)}'\n")
            
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", "clips_list.txt",
        "-i", audio_path,
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        output_path
    ]
    subprocess.run(cmd, check=True)
    print(f"🏆 اكتمل إنتاج الوثائقي بنجاح: {output_path}")

# --- 7. رفع الوثائقي إلى يوتيوب ---
def upload_to_youtube(file_path: str, channel_key: str, title: str, description: str):
    print(f"🚀 جاري رفع الوثائقي إلى قناة [{channel_key}]: \"{title}\"...")
    
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
    
    media = MediaFileUpload(file_path, chunksize=10*1024*1024, resumable=True)
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
    channel_names = {
        "ABAAD": "أبعاد جغرافية",
        "MASHAREE": "مشاريع عملاقة",
        "MASAR": "مسار"
    }
    channel_title = channel_names.get(channel_key, channel_key)
    
    # 1. فكرة عشوائية
    idea = get_random_documentary_idea(channel_title)
    
    # 2. توليد النص المطول
    script = generate_full_script(idea["title"], idea["description"])
    
    # 3. تسجيل الصوت البشري
    audio_dur = build_voiceover(script, "narration.mp3")
    
    # 4. جلب المشاهد البصرية
    clips = download_matching_footage(idea["search_keywords"], target_duration=audio_dur)
    
    # 5. المونتاج والرندر
    assemble_documentary(clips, "narration.mp3", "final_documentary.mp4")
    
    # 6. الرفع
    upload_to_youtube("final_documentary.mp4", channel_key, idea["title"], idea["description"])
