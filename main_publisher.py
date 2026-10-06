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

# --- 1. مفاتيح التشغيل واختيار النموذج الذكي ---
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_KEY = os.getenv("PEXELS_API_KEY")
BUFFER_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

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

# --- 2. إدارة ذاكرة السجل لمنع التكرار ---
HISTORY_FILE = "shorts_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(history):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history[-120:], f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# --- 3. محرك الذكاء الاصطناعي المقاوم للحظر الجغرافي ---
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

# --- 4. توليد المحتوى الفيروسي الذكي بنظام Infinite Loop ---
def generate_apex_short(channel_name: str) -> dict:
    print(f"🧠 [Apex Studio]: جاري هندسة فكرة وسيناريو شورتس لقناة [{channel_name}]...")
    history = load_history()
    recent_titles = [item.get("title", "") for item in history[-25:]]
    exclude_text = f"ممنوع تكرار هذه المواضيع نهائياً: {', '.join(recent_titles)}" if recent_titles else ""

    prompt_stage1 = f"""
    أنت العقل المدبر لأكبر قنوات الوثائقيات الفيروسية العالمية (Shorts & Reels).
    قناتنا هي: "{channel_name}".
    {exclude_text}
    
    المطلوب:
    ابتكر فكرة غامضة ومثيرة للاهتمام للغاية، واكتب سيناريو شورتس باللغة العربية الفصحى.
    شروط إلزامية:
    1. Hook الصدمة (أول ثانيتين): سؤال أو حقيقة تمنع التمرير وتثير الذهول فوراً.
    2. الحبكة: سرد سريع لمعلومات تاريخية أو علمية أو عسكرية موثقة وصادمة.
    3. The Infinite Loop: اربط الكلمة الأخيرة في السيناريو ببداية الجملة الأولى ليكتمل المعنى ويعيد الفيديو تشغيل نفسه بلا نهاية.
    4. الطول: من 65 إلى 80 كلمة فقط (ليكون زمن الصوت بين 30 إلى 42 ثانية).
    5. حدد 5 عبارات بحث بصرية سينمائية بالإنجليزية تناسب مقاطع Pexels.
    
    أخرج الرد بصيغة JSON حصراً:
    {{
        "title": "عنوان مثير مع إيموجي",
        "script": "النص المنطوق فقط",
        "scene_keywords": ["keyword 1", "keyword 2", "keyword 3", "keyword 4", "keyword 5"]
    }}
    """
    ai_raw = query_ai_robust(prompt_stage1)
    if ai_raw:
        try:
            cleaned = ai_raw.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)
            
            prompt_refine = f"راجع هذا النص واجعله أكثر سرعة وإثارة مع الحفاظ على طوله (65-80 كلمة) وربط نهايته ببدايته: {data['script']}"
            refined = query_ai_robust(prompt_refine)
            if refined and len(refined.split()) >= 45:
                data['script'] = refined

            history.append({"title": data["title"], "time": time.time()})
            save_history(history)
            print(f"  💡 العنوان المعتمد لـ [{channel_name}]: {data['title']}")
            return data
        except Exception:
            pass

    fallback_pool = [
        {
            "title": "أغرب مكان محظور على وجه الأرض! 😱",
            "script": "هذا هو المكان الوحيد على كوكبنا الذي يُمنع أي إنسان من دخوله تحت تهديد السلاح. في أعماق المحيط، تقف جزيرة معزولة لا يسكنها إلا أكثر الكائنات فتكاً في العالم. كل من حاول الاقتراب منها اختفى دون أثر، ولذلك سيبقى لغزها غامضاً لأن هذا هو المكان الوحيد...",
            "scene_keywords": ["isolated island aerial", "military patrol ocean", "dark waves mystery", "restricted area forbidden", "ocean storm dark"]
        },
        {
            "title": "أعظم سر دفن تحت أهرامات الجيزة! 🏛️",
            "script": "هذا التجويف السري في قلب الهرم الأكبر حير كل أجهزة المسح بالأشعة الكونية. فراغ عملاق بحجم طائرة ركاب، مغلق بإحكام منذ آلاف السنين، ولم يجرؤ أحد على فتحه حتى الآن، خوفاً من كشف الحقيقة الصادمة عن هذا التجويف السري...",
            "scene_keywords": ["pyramids giza 4k", "secret ancient chamber", "cosmic scan archaeology", "egypt desert golden", "ancient hieroglyphs"]
        },
        {
            "title": "حفرة نهاية العالم: لغز أعماق سيبيريا! ❄️",
            "script": "هذه الفوهة الغامضة التي ابتلعت الأرض فجأة في سيبيريا فجرت رعباً علمياً غير مسبوق. عمق سحيق ينبعث منه غاز مجهول وأصوات مرعبة سجلتها الحساسات الأرضية. ما زال الباحثون عاجزين عن تفسير بداية هذه الفوهة الغامضة...",
            "scene_keywords": ["siberia tundra snow", "massive mysterious crater", "deep underground abyss", "dark mist winter", "extreme cold wilderness"]
        }
    ]
    data = random.choice(fallback_pool)
    history.append({"title": data["title"], "time": time.time()})
    save_history(history)
    print(f"  💡 العنوان المعتمد لـ [{channel_name}]: {data['title']}")
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

# --- 6. جلب مشاهد Pexels الرأسية المتنوعة ---
def download_vertical_clips(keywords: list, target_duration: float, output_dir: str) -> str:
    print(f"📱 جاري جلب لقطات سينمائية رأسية وتوزيعها بإيقاع سريع...")
    os.makedirs(output_dir, exist_ok=True)
    headers = {"Authorization": PEXELS_KEY}
    
    downloaded_files = []
    clip_counter = 0
    total_footage_sec = 0.0
    
    for kw in keywords:
        if total_footage_sec >= target_duration + 12:
            break
        url = f"https://api.pexels.com/videos/search?query={kw}&per_page=6&orientation=portrait"
        try:
            res = requests.get(url, headers=headers, timeout=20).json()
            for v in res.get("videos", []):
                if total_footage_sec >= target_duration + 12:
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
        except Exception:
            continue
            
    playlist_path = os.path.join(output_dir, "short_playlist.txt")
    with open(playlist_path, "w", encoding="utf-8") as f:
        loops_needed = max(2, int((target_duration // max(1, total_footage_sec)) + 2))
        extended_list = (downloaded_files * loops_needed)
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

# --- 8. هندسة صوتية ثلاثية الطبقات (Ambience + Heartbeat Pulse + Sub-Drop) ---
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

# --- 9. رندر سينمائي متكامل (Apex Cinema Mastering) ---
def render_apex_short(playlist_path: str, voice_path: str, script_text: str, channel_name: str, output_path: str):
    print("🎬 [Render]: جاري تطبيق المونتاج السينمائي المتكامل (Film Look + Dynamic Progress + 3D Subs)...")
    voice_dur = get_audio_duration(voice_path)
    sfx_path = generate_apex_soundtrack(voice_dur, "sfx.mp3")
    ass_path = generate_karaoke_ass(script_text, voice_dur, "subs.ass")

    audio_chain = (
        "[1:a]highpass=f=75,equalizer=f=120:width_type=o:width=1.6:g=4.2,"
        "equalizer=f=3500:width_type=o:width=1.3:g=3.0,loudnorm=I=-14:TP=-1.5:LRA=7[voice];"
        "[2:a]volume=0.12[sfx];"
        "[voice][sfx]amix=inputs=2:duration=first:dropout_transition=2[aout]"
    )

    clean_channel_tag = clean_arabic_text(channel_name.split('|')[0].strip())

    video_chain = (
        "[0:v]fps=30,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,"
        "eq=contrast=1.17:saturation=1.26:brightness=-0.01,vignette=angle=0.46,"
        "noise=alls=11:allf=t+u,"
        f"drawtext=text='{clean_channel_tag}':fontcolor=white@0.35:fontsize=36:x=50:y=70:box=1:boxcolor=black@0.25:boxborderw=10,"
        f"subtitles={ass_path}[vgraded];"
        f"color=c=yellow:s=1080x14[pbar];"
        f"[vgraded][pbar]overlay=x='-W+W*(t/{voice_dur:.2f})':y=H-14:shortest=1[vout]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-fflags", "+genpts",
        "-f", "concat", "-safe", "0", "-i", playlist_path,
        "-i", voice_path,
        "-i", sfx_path,
        "-filter_complex", f"{video_chain};{audio_chain}",
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
        "-b:v", "2800k", "-maxrate", "3500k", "-bufsize", "6000k",
        "-c:a", "aac", "-b:a", "192k",
        "-max_muxing_queue_size", "1024",
        "-shortest",
        output_path
    ]
    subprocess.run(cmd, check=True)
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"🏆 اكتمل إنتاج فيلم الشورتس بمستوى (Apex Studio Grade): {output_path} ({size_mb:.1f} ميجابايت)")

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
        print(f"⚠️️ Catbox: {e}")

    try:
        cmd = ["curl", "-s", "-F", "reqtype=fileupload", "-F", "time=24h", "-F", f"fileToUpload=@{file_path}", "https://litterbox.catbox.moe/resources/internals/api.php"]
        res = subprocess.check_output(cmd, timeout=60).decode().strip()
        if res.startswith("http"):
            print(f"  🔗 تم الرفع بنجاح عبر Litterbox: {res}")
            return res
    except Exception as e:
        print(f"⚠️️ Litterbox: {e}")

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
CHANNELS_MAP = {
    "MASAR": {"id": "6abace7bea19ca0bde181dff", "name": "مسار | Masar"},
    "MASHAREE": {"id": "6abace11ea19ca0bde181821", "name": "مشاريع عملاقة | MegaBuilds"},
    "ABAAD": {"id": "6abacd06ea19ca0bde180ef9", "name": "أبعاد جغرافية | Abaad"}
}

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

    # القالب الصحيح: دمج الاستعلام والمتغيرات معاً في قاموس json
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

    target_channel_key = sys.argv[1] if len(sys.argv) > 1 else None
    channels = get_target_channels(target_channel_key)
    print(f"🚀 بدء أتمتة Matrix Shorts لـ {len(channels)} قنوات...")

    success_count = 0
    for idx, ch in enumerate(channels, 1):
        ch_id = ch.get("id")
        ch_name = ch.get("name", f"قناة {idx}")
        print(f"\n{'='*55}")
        print(f"🎬 صناعة فيلم شورتس استثنائي لقناة [{ch_name}]")
        print(f"{'='*55}")

        short_data = generate_apex_short(ch_name)
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
        print(f"🏆 تم بنجاح إنتاج ونشر الفيديوهات بنمط Matrix!")
    else:
        sys.exit(1)
