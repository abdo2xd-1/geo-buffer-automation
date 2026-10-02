import os
import sys
import json
import time
import argparse
import requests
import subprocess
from pathlib import Path

# إعداد المتغيرات والمفاتيح
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "").strip()

CHANNEL_TOPICS = {
    "abaad": {
        "name": "أبعاد جغرافية",
        "topic": "الممرات الملاحية والمضائق الاستراتيجية وصراع التجارة البحرية الدولية",
        "voice": "ar-EG-ShakirNeural",
        "search_keywords": ["cargo ship ocean", "panama canal", "shipping containers", "satellite earth"]
    },
    "masharee": {
        "name": "مشاريع عملاقة",
        "topic": "أضخم الإنشاءات الهندسية وناطحات السحاب والأنفاق العملاقة حول العالم",
        "voice": "ar-SA-HamedNeural",
        "search_keywords": ["mega construction", "skyscraper build", "bridge engineering", "heavy machinery"]
    },
    "masar": {
        "name": "مسار",
        "topic": "خفايا سلاسل الإمداد العالمية وصعود القوى الاقتصادية الكبرى ومستقبل التجارة",
        "voice": "ar-SA-HamedNeural",
        "search_keywords": ["global economy", "freight train", "modern factory", "container terminal"]
    }
}

def generate_script(channel_key):
    """توليد سيناريو وثائقي عبر Gemini API مع نص تعليق احترافي"""
    cfg = CHANNEL_TOPICS.get(channel_key, CHANNEL_TOPICS["masar"])
    print(f"🧠 جاري توليد سيناريو لقناة [{cfg['name']}]...")

    prompt = f"""
    أنت كاتب وثائقيات استقصائية مخضرم. اكتب نص تعليق صوتي لوثائقي شيق لقناة '{cfg['name']}'.
    الموضوع: {cfg['topic']}
    الشروط:
    - لغة عربية فصحى مشوقة، قوية، دون مقدمات ترحيبية ركيكة.
    - الدخول فوراً في قلب الموضوع والحقائق والأرقام.
    - الطول: مقسم إلى 4 فقرات واضحة ومكثفة.
    - أرجع النص فقط بدون علامات تنسيق غريبة.
    """

    if GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            res = requests.post(url, json=payload, timeout=40)
            res.raise_for_status()
            data = res.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            print(f"⚠️ تعذر الاتصال بـ Gemini ({e})، سيتم استخدام نص استقصائي جاهز.")

    return f"في عالم تتشابك فيه المصالح وتتسارع فيه وتيرة التنمية، تمثل شبكات الإمداد والمشاريع العملاقة الشريان الحقيقي للاقتصاد الدولي. من أعماق البحار إلى أعلى قمم الإنشاءات الهندسية، ترسم هذه المسارات ملامح النفوذ العالمي وتعيد صياغة موازين القوى في القرن الحادي والعشرين."

def generate_voiceover(text, voice, output_audio="voiceover.mp3"):
    """توليد تعليق صوتي باللغة العربية عبر Edge TTS"""
    print(f"🎙️ توليد التعليق الصوتي باستخدام الصوت ({voice})...")
    clean_text = text.replace('"', '').replace("'", "").strip()
    cmd = [
        "edge-tts",
        "--voice", voice,
        "--text", clean_text,
        "--write-media", output_audio
    ]
    subprocess.run(cmd, check=True)
    return output_audio

def download_pexels_clips(keywords, max_clips=4, output_dir="clips"):
    """جلب مقاطع فيديو بجودة عالية تناسب الوثائقي من Pexels"""
    os.makedirs(output_dir, exist_ok=True)
    video_files = []

    if not PEXELS_API_KEY:
        print("⚠️ لم يتم تعيين PEXELS_API_KEY، سيتم توليد خلفيات بديلة.")
        return []

    headers = {"Authorization": PEXELS_API_KEY}
    for kw in keywords[:max_clips]:
        try:
            url = f"https://api.pexels.com/videos/search?query={kw}&orientation=landscape&size=medium&per_page=1"
            r = requests.get(url, headers=headers, timeout=20)
            if r.status_code == 200:
                data = r.json()
                videos = data.get("videos", [])
                if videos:
                    files = videos[0].get("video_files", [])
                    # اختيار جودة HD مناسبة
                    mp4_files = [f for f in files if f.get("file_type") == "video/mp4" and (f.get("width", 0) >= 1280)]
                    selected_file = mp4_files[0] if mp4_files else files[0]
                    download_url = selected_file["link"]
                    
                    target_path = os.path.join(output_dir, f"clip_{len(video_files)+1}.mp4")
                    v_res = requests.get(download_url, stream=True, timeout=30)
                    with open(target_path, "wb") as f:
                        for chunk in v_res.iter_content(chunk_size=1024*1024):
                            f.write(chunk)
                    video_files.append(target_path)
                    print(f"📥 تم تنزيل كليب: {kw}")
        except Exception as e:
            print(f"⚠️ خطأ أثناء تنزيل المقطع ({kw}): {e}")

    return video_files

def render_documentary(channel_key, audio_path, video_clips, output_file):
    """دمج الصوت والفيديوهات وضبط المقاسات 16:9 بجودة 1080p عبر FFmpeg"""
    print("🎞️ جاري معالجة ورندر الفيديو النهائي عبر FFmpeg...")

    # الحصول على مدة ملف الصوت
    probe_cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {audio_path}"
    duration_str = subprocess.check_output(probe_cmd, shell=True).decode().strip()
    audio_duration = float(duration_str) if duration_str else 30.0

    if video_clips:
        # توحيد مقاسات كل مقطع لـ 1920x1080 بمعدل 30 إطار
        standardized_clips = []
        for i, clip in enumerate(video_clips):
            norm_path = f"norm_{i}.mp4"
            conv_cmd = f'ffmpeg -y -i {clip} -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1" -r 30 -an {norm_path}'
            subprocess.run(conv_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            standardized_clips.append(norm_path)

        # كتابة قائمة الدمج
        with open("concat_list.txt", "w") as f:
            for sc in standardized_clips:
                f.write(f"file '{sc}'\n")

        # دمج المقاطع في حلقة تتكرر حتى نهاية الصوت
        cmd = (
            f'ffmpeg -y -f concat -safe 0 -stream_loop -1 -i concat_list.txt '
            f'-i {audio_path} -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 192k '
            f'-t {audio_duration} -shortest {output_file}'
        )
    else:
        # خلفية سينمائية احتياطية مع النص إذا تعذر جلب الفيديوهات
        cfg = CHANNEL_TOPICS.get(channel_key, CHANNEL_TOPICS["masar"])
        cmd = (
            f'ffmpeg -y -f lavfi -i color=c=black:s=1920x1080:d={audio_duration} -i {audio_path} '
            f'-vf "drawtext=text=\'{cfg["name"]}\':fontcolor=white:fontsize=72:x=(w-text_w)/2:y=(h-text_h)/2" '
            f'-c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest {output_file}'
        )

    subprocess.run(cmd, shell=True, check=True)
    print(f"✅ تم الانتهاء من رندر الوثائقي: {output_file}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", default="masar", choices=["abaad", "masharee", "masar"], help="معرف القناة")
    args = parser.parse_args()

    channel_key = args.channel
    output_filename = f"documentary_{channel_key}.mp4"

    cfg = CHANNEL_TOPICS[channel_key]
    script_text = generate_script(channel_key)
    audio_file = generate_voiceover(script_text, cfg["voice"])
    clips = download_pexels_clips(cfg["search_keywords"])
    render_documentary(channel_key, audio_file, clips, output_filename)

if __name__ == "__main__":
    main()
