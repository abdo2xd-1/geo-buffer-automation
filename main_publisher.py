import os
import sys
import re
import json
import time
import random
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

# --- 1. الإعدادات والنموذج الفعال ---
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_KEY = os.getenv("PEXELS_API_KEY")
BUFFER_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN")
BUFFER_PROFILE_ID = os.getenv("BUFFER_PROFILE_ID")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

def get_active_model():
    candidates = ["gemini-3.8-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro", "gemini-pro"]
    for c in candidates:
        try:
            m = genai.GenerativeModel(c)
            m.generate_content("test")
            print(f"🎯 تم تفعيل النموذج المعتمد: [{c}]")
            return m
        except Exception:
            continue
    try:
        for m_info in genai.list_models():
            if "generateContent" in m_info.supported_generation_methods:
                model_name = m_info.name.replace("models/", "")
                try:
                    m = genai.GenerativeModel(model_name)
                    m.generate_content("test")
                    return m
                except Exception:
                    continue
    except Exception:
        pass
    return genai.GenerativeModel("gemini-3.8-flash")

model = get_active_model() if GEMINI_KEY else None
VOICE_NAME = "ar-EG-ShakirNeural"  # صوت بشري وثائقي طبيعي

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

# --- 2. توليد فكرة شورتس فريدة وعشوائية لكل قناة على حدة ---
def generate_unique_short_for_channel(channel_name: str) -> dict:
    print(f"🎲 جاري ابتكار فكرة شورتس حصرية ومميزة ومختلفة لقناة [{channel_name}]...")
    prompt = f"""
    أنت صانع محتوى فيروسي متخصص في يوتيوب شورتس (YouTube Shorts) الوثائقية والغامضة.
    قناتنا الحالية هي: "{channel_name}".
    
    مهم جداً:
    - لا تحصر القناة في نطاق ضيق أو مكرر إطلاقاً.
    - ابتكر موضوعاً عشوائياً ومثيراً وفضولياً يناسب المشاهد العربي. نوّع بحرية مطلقة بين:
      * ألغاز واكتشافات أثرية صادمة،
      * غرائب وظواهر كونية أو جغرافية غير مفسرة،
      * أسرار عسكرية أو تقنية غامضة،
      * معالم أو مدن مفقودة ومحظورة،
      * كوارث أو صدف تاريخية غيرت مجرى الأحداث.
    
    شروط كتابة الشورتس:
    1. Hook أول 3 ثوانٍ: جملة افتتاحية صادمة تخطف الانتباه فوراً.
    2. الطول: نص مركز يتراوح بين 60 إلى 80 كلمة فقط (ليكون زمن الصوت بين 30 إلى 45 ثانية كحد أقصى).
    3. لغة عربية فصحى مشوقة بدون أي توجيهات إخراجية أو أسماء مشاهد.
    
    أخرج النتيجة بصيغة JSON حصراً:
    {{
        "title": "عنوان جذاب جداً مع إيموجي للشورتس",
        "script": "النص الكامل الذي سينطقه المعلق الصوتي مباشرة",
        "search_keywords": ["3", "كلمات", "بحث", "إنجليزية", "portrait", "mystery"]
    }}
    """
    try:
        res = model.generate_content(prompt)
        cleaned = res.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(cleaned)
    except Exception:
        fallback_pool = [
            {
                "title": "أغرب مكان محظور على وجه الأرض! 😱",
                "script": "هل تعلم أن هناك جزيرة معزولة في المحيط ممنوع على أي بشري الاقتراب منها؟ كل من حاول الهبوط عليها اختفى دون أثر. الحكومات تحيطها بحراسة عسكرية مشددة. ما هو السر المخيف الذي يخفونه هناك؟",
                "search_keywords": ["mysterious island aerial", "dangerous nature", "ocean waves dark"]
            },
            {
                "title": "أعظم سر دفن تحت أهرامات الجيزة! 🏛️",
                "script": "لآلاف السنين ظننا أننا كشفنا كل أسرار الأهرامات، لكن أحدث مسح كوني فجر مفاجأة مرعبة! فراغ عملاق بحجم طائرة مخفي في قلب الهرم الأكبر، لم تطأه قدم إنسان منذ آلاف السنين. ماذا يوجد بداخله؟",
                "search_keywords": ["ancient pyramids egypt", "archaeology mystery", "golden desert aerial"]
            },
            {
                "title": "حفرة نهاية العالم: لغز أعماق سيبيريا! ❄️",
                "script": "في أقصى صقيع سيبيريا، ظهرت فجأة فوهة عملاقة تبتلع الأرض بعمق مئات الأمتار! العلماء سجلوا أصواتاً مريبة تصدر من باطنها وغازات غريبة تنبعث بلا توقف. هل هي بداية كارثة بيئية أم لغز لم يُفسر؟",
                "search_keywords": ["mysterious crater aerial", "siberia ice wilderness", "deep cave darkness"]
            },
            {
                "title": "مدينة تحت الرمال: لغز الربع الخالي! 🏜️",
                "script": "في قلب صحراء الربع الخالي، رصدت الأقمار الصناعية أطلالاً لمدينة ضخمة مطمورة تحت الكثبان! أساطير تحكي عن حضارة امتلكت ثراءً خيالياً ثم اختفت في ليلة واحدة. هل وجد العلماء إرم ذات العماد؟",
                "search_keywords": ["desert ruins sand", "ancient city aerial", "empty quarter mystery"]
            },
            {
                "title": "الباب المغلق الذي يخشى العلماء فتحه! 🚪",
                "script": "في أحد أقدم المعابد في الهند، يوجد باب سري لا يملك أقفالاً ولا مفاتيح، ولم يُفتح منذ مئات السنين! الأساطير تحذر من أن فتحه سيجلب كارثة عالمية، وحتى اليوم ترفض السلطات لمسه. ما الذي يقبع خلفه؟",
                "search_keywords": ["ancient temple secret", "mysterious door vault", "dark history relics"]
            }
        ]
        data = random.choice(fallback_pool)
        
    print(f"  💡 عنوان الشورتس لـ [{channel_name}]: {data['title']}")
    return data

# --- 3. توليد صوت الشورتس ---
async def generate_short_voice_async(text: str, output_path: str):
    comm = edge_tts.Communicate(text, VOICE_NAME, rate="-2%")
    await comm.save(output_path)

def create_short_audio(script_text: str, output_path: str) -> float:
    print(f"🎙️ جاري توليد صوت الشورتس البشري ({VOICE_NAME})...")
    cleaned = clean_arabic_text(script_text)
    try:
        asyncio.run(generate_short_voice_async(cleaned, output_path))
    except Exception:
        gtts.gTTS(text=cleaned, lang="ar").save(output_path)
        
    dur = get_audio_duration(output_path)
    print(f"🎧 مدة التعليق الصوتي: {dur:.1f} ثانية")
    return dur

# --- 4. جلب المشاهد الرأسية (9:16) من Pexels ---
def download_vertical_clips(keywords: list, target_duration: float, output_dir: str) -> str:
    print(f"📱 جاري تنزيل مشاهد عمودية (Shorts 9:16) لتغطية {target_duration:.1f} ثانية...")
    os.makedirs(output_dir, exist_ok=True)
    headers = {"Authorization": PEXELS_KEY}
    
    downloaded_files = []
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
                    
                c_path = os.path.join(output_dir, f"vclip_{clip_counter:02d}.mp4")
                r = requests.get(chosen.get("link"), stream=True, timeout=30)
                with open(c_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        f.write(chunk)
                        
                dur = get_audio_duration(c_path)
                downloaded_files.append(c_path)
                total_footage_sec += dur
                clip_counter += 1
                print(f"  📥 تم تحميل كليب رأسي {clip_counter} ({dur:.1f} ثانية)")
        except Exception:
            continue
            
    playlist_path = os.path.join(output_dir, "short_playlist.txt")
    with open(playlist_path, "w", encoding="utf-8") as f:
        loops_needed = max(2, int((target_duration // max(1, total_footage_sec)) + 2))
        extended_list = (downloaded_files * loops_needed)
        for clip in extended_list:
            f.write(f"file '{os.path.abspath(clip)}'\n")
            
    return playlist_path

# --- 5. رندر الشورتس العمودي السريع ---
def render_short_video(playlist_path: str, audio_path: str, output_path: str):
    print("⚙️ جاري دمج ومونتاج الشورتس العمودي (1080x1920)...")
    cmd = [
        "ffmpeg", "-y",
        "-fflags", "+genpts",
        "-f", "concat", "-safe", "0", "-i", playlist_path,
        "-i", audio_path,
        "-vf", "fps=30,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "28",
        "-b:v", "2500k", "-maxrate", "3000k", "-bufsize", "6000k",
        "-c:a", "aac", "-b:a", "128k",
        "-max_muxing_queue_size", "1024",
        "-shortest",
        output_path
    ]
    subprocess.run(cmd, check=True)
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"🎬 اكتمل إنتاج الشورتس بنجاح: {output_path} (حجم الملف: {size_mb:.1f} ميجابايت)")

# --- 6. رفع الفيديو برابط مباشر يقبله Buffer 100% ---
def get_public_video_url(file_path: str) -> str:
    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    print(f"🌐 جاري رفع الفيديو بحجم {size_mb:.1f} ميجابايت للحصول على رابط مباشر لـ Buffer...")

    # 1. Catbox الرسمي عبر curl (رابط MP4 مباشر وثابت)
    try:
        cmd = ["curl", "-s", "-F", "reqtype=fileupload", "-F", f"fileToUpload=@{file_path}", "https://catbox.moe/user/api.php"]
        res = subprocess.check_output(cmd, timeout=60).decode().strip()
        if res.startswith("http") and ".mp4" in res:
            print(f"  🔗 تم الرفع بنجاح عبر Catbox: {res}")
            return res
    except Exception as e:
        print(f"⚠️ Catbox curl: {e}")

    # 2. Litterbox المؤقت عبر curl
    try:
        cmd = ["curl", "-s", "-F", "reqtype=fileupload", "-F", "time=24h", "-F", f"fileToUpload=@{file_path}", "https://litterbox.catbox.moe/resources/internals/api.php"]
        res = subprocess.check_output(cmd, timeout=60).decode().strip()
        if res.startswith("http"):
            print(f"  🔗 تم الرفع بنجاح عبر Litterbox: {res}")
            return res
    except Exception as e:
        print(f"⚠️ Litterbox curl: {e}")

    # 3. Uguu.se عبر curl
    try:
        cmd = ["curl", "-s", "-F", f"files[]=@{file_path}", "https://uguu.se/upload"]
        res_raw = subprocess.check_output(cmd, timeout=60).decode().strip()
        data = json.loads(res_raw)
        if data.get("success") and data.get("files"):
            url = data["files"][0].get("url")
            print(f"  🔗 تم الرفع بنجاح عبر Uguu: {url}")
            return url
    except Exception as e:
        print(f"⚠️ Uguu curl: {e}")

    # 4. 0x0.st عبر curl
    try:
        cmd = ["curl", "-s", "-F", f"file=@{file_path}", "https://0x0.st"]
        res = subprocess.check_output(cmd, timeout=60).decode().strip()
        if res.startswith("http"):
            print(f"  🔗 تم الرفع بنجاح عبر 0x0.st: {res}")
            return res
    except Exception as e:
        print(f"⚠️ 0x0.st curl: {e}")

    return ""

# --- 7. قائمة القنوات وواجهة Buffer GraphQL ---
def get_buffer_channels(buffer_token):
    headers = {
        "Authorization": f"Bearer {buffer_token}",
        "Content-Type": "application/json"
    }
    graphql_url = "https://api.buffer.com"
    
    try:
        q_orgs = """
        query {
          account {
            organizations {
              id
              name
            }
          }
        }
        """
        res = requests.post(graphql_url, json={"query": q_orgs}, headers=headers, timeout=20).json()
        orgs = res.get("data", {}).get("account", {}).get("organizations", [])
        channels = []
        for org in orgs:
            org_id = org.get("id")
            q_chan = """
            query GetChannels($input: ChannelsInput!) {
              channels(input: $input) {
                id
                name
                service
              }
            }
            """
            c_res = requests.post(graphql_url, json={"query": q_chan, "variables": {"input": {"organizationId": org_id}}}, headers=headers, timeout=20).json()
            ch_list = c_res.get("data", {}).get("channels", [])
            for c in ch_list:
                channels.append(c)
        if channels:
            return channels
    except Exception as e:
        print(f"⚠️ استعلام القنوات من GraphQL: {e}")

    fallback = [
        {"id": "6abace7bea19ca0bde181dff", "name": "مسار | Masar", "service": "youtube"},
        {"id": "6abace11ea19ca0bde181821", "name": "مشاريع عملاقة | MegaBuilds", "service": "youtube"},
        {"id": "6abacd06ea19ca0bde180ef9", "name": "أبعاد جغرافية | Abaad", "service": "youtube"}
    ]
    return fallback

def send_short_to_channel(channel_id: str, channel_name: str, video_url: str, title: str) -> bool:
    graphql_url = "https://api.buffer.com"
    headers = {
        "Authorization": f"Bearer {BUFFER_TOKEN}",
        "Content-Type": "application/json"
    }
    caption_text = f"{title}\n\nهل كنت تعلم هذه المعلومة من قبل؟ شاركنا رأيك في التعليقات! 👇\n\n#Shorts #shorts #معلومات #حقائق #وثائقي #استكشاف"

    mutation_query = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess {
          post {
            id
            text
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
        "assets": [
            {
                "video": {
                    "url": video_url
                }
            }
        ],
        "metadata": {
            "youtube": {
                "title": title[:100],
                "categoryId": "27",
                "privacy": "public",
                "madeForKids": False
            }
        }
    }

    body = {
        "query": mutation_query,
        "variables": {"input": inp_data}
    }

    try:
        res = requests.post(graphql_url, json=body, headers=headers, timeout=40)
        res_data = res.json()
        data_result = res_data.get("data", {}).get("createPost", {})
        post_info = data_result.get("post")
        err_msg = data_result.get("message")
        top_errors = res_data.get("errors")

        if post_info and post_info.get("id"):
            print(f"  🎉 تم النشر بنجاح على [{channel_name}]! Post ID: {post_info.get('id')}")
            return True
        elif err_msg:
            print(f"  ⚠️ رسالة بافر: {err_msg}")
        elif top_errors:
            print(f"  ⚠️ خطأ الاستعلام: {top_errors[0].get('message')}")
    except Exception as e:
        print(f"  ⚠️ استثناء اتصال: {e}")

    return False

# --- نقطة البداية: إنتاج فيديو مستقل تماماً لكل قناة ونشره ---
if __name__ == "__main__":
    if not BUFFER_TOKEN:
        print("❌ خطأ: متغير BUFFER_ACCESS_TOKEN غير موجود في إعدادات Secrets!")
        sys.exit(1)

    channels = get_buffer_channels(BUFFER_TOKEN)
    print(f"🚀 بدء أتمتة إنتاج ونشر فيديوهات Shorts مستقلة لـ {len(channels)} قنوات...")

    success_count = 0
    for idx, ch in enumerate(channels, 1):
        ch_id = ch.get("id")
        ch_name = ch.get("name", f"قناة {idx}")
        print(f"\n{'='*50}")
        print(f"🎬 [القناة {idx}/{len(channels)}]: تجهيز فيديو شورتس مخصص وحصري لـ [{ch_name}]")
        print(f"{'='*50}")

        # 1. ابتكار فكرة وسيناريو فريد وعشوائي تماماً لهذه القناة
        short_data = generate_unique_short_for_channel(ch_name)
        
        # 2. توليد صوت مستقل
        audio_file = f"narration_{idx}.mp3"
        duration = create_short_audio(short_data["script"], audio_file)
        
        # 3. جلب مشاهد Pexels عمودية خاصة بموضوع الفيديو
        clips_dir = f"clips_ch_{idx}"
        playlist = download_vertical_clips(short_data["search_keywords"], target_duration=duration, output_dir=clips_dir)
        
        # 4. رندر المقطع
        video_file = f"final_short_{idx}.mp4"
        render_short_video(playlist, audio_file, video_file)
        
        # 5. رفع الفيديو برابط مباشر
        pub_url = get_public_video_url(video_file)
        
        # 6. النشر على القناة المحددة في بافر
        if pub_url:
            if send_short_to_channel(ch_id, ch_name, pub_url, short_data["title"]):
                success_count += 1
        else:
            print(f"❌ تعذر استخراج رابط الفيديو المباشر لـ [{ch_name}].")

        time.sleep(3)

    print(f"\n{'='*50}")
    if success_count > 0:
        print(f"🏆 تم إنتاج ونشر {success_count} فيديوهات شورتس مختلفة وحصرية بنجاح على قنواتك!")
    else:
        print("❌ تعذر نشر الفيديوهات على القنوات. يرجى مراجعة السجلات.")
        sys.exit(1)
