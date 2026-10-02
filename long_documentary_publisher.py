import os
import sys
import time
import argparse
import requests
import subprocess
from pathlib import Path

# جلب المفاتيح من متغيرات البيئة
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "").strip()

# إعدادات كل قناة: الاسم، الموضوع، الصوت المعتمد، وكلمات البحث
CHANNEL_CONFIGS = {
    "abaad": {
        "name": "أبعاد جغرافية",
        "topic": "الممرات الملاحية والمضائق الاستراتيجية وصراع التجارة البحرية الدولية",
        "voice": "ar-EG-ShakirNeural",
        "search_keywords": ["cargo ship ocean", "panama canal", "shipping containers", "satellite earth"]
    },
    "masharee": {
        "name": "مشاريع عملاقة",
        "topic": "أضخم الإنشاءات الهندسية وناطحات السحاب والأنفاق العالمية المعقدة",
        "voice": "ar-SA-HamedNeural",
        "search_keywords": ["mega construction", "skyscraper build", "bridge engineering", "heavy machinery"]
    },
    "masar": {
        "name": "مسار",
        "topic": "خفايا سلاسل الإمداد العالمية وصعود القوى الاقتصادية وصناعة المستقبل",
        "voice": "ar-SA-HamedNeural",
        "search_keywords": ["global economy", "freight train", "modern factory", "container terminal"]
    }
}

def generate_script(channel_key):
    """توليد النص بالذكاء الاصطناعي مع نصوص احتياطية متكاملة"""
    cfg = CHANNEL_CONFIGS.get(channel_key, CHANNEL_CONFIGS["masar"])
    print(f"🧠 جاري توليد سيناريو لقناة [{cfg['name']}]...")

    prompt = f"""
    اكتب نص تعليق صوتي لوثائقي استقصائي مكثف لقناة '{cfg['name']}'.
    الموضوع: {cfg['topic']}
    الشروط:
    - لغة عربية فصحى مشوقة، قوية وسريعة.
    - الدخول مباشرة في صلب الحقائق والأرقام دون ترحيب أو مقدمات تقليدية.
    - الطول: 4 فقرات مركزة تصف الأهمية الاستراتيجية والتداعيات الاقتصادية.
    - أرجع النص الصافي فقط دون أي عناوين جانبية.
    """

    if GEMINI_API_KEY:
        models = ["gemini-1.5-flash-latest", "gemini-1.5-flash", "gemini-2.0-flash"]
        for model in models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                res = requests.post(url, json=payload, timeout=30)
                if res.status_code == 200:
                    data = res.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            except Exception:
                continue

    fallback_texts = {
        "abaad": "تتحكم مضائق وبحار الكوكب في أكثر من ثمانين بالمئة من حركة التجارة الدولية. نقاط اختناق جغرافية دقيقة تعتمد عليها سلاسل التوريد العالمية، حيث يمكن لأي اضطراب في هذه الممرات أن يشل حركة الاقتصاد الدولي ويعيد رسم خارطة النفوذ الجيوسياسي.",
        "masharee": "على امتداد القارات، تتحدى الهندسة الحديثة تضاريس الطبيعة بمشاريع إنشائية غير مسبوقة. من ناطحات السحاب الشاهقة إلى أطول الأنفاق والجسور البحرية، تمثل هذه المعجزات المعمارية ذروة الابتكار الإنساني والقدرة على إعادة هندسة الكوكب.",
        "masar": "في عمق الاقتصاد الدولي، تقود خطوط الإمداد وشبكات التجارة مسار صعود وهبوط القوى الكبرى. لم تعد المعارك تقتصر على الموارد التقليدية، بل أصبحت صراعاً للهيمنة على حركة السلع، الطاقة، والموانئ الاستراتيجية التي تدير العالم."
    }
    return fallback_texts.get(channel_key, fallback_texts["masar"])

def generate_voiceover(text, voice, output_audio):
    """توليد التعليق الصوتي باستخدام Edge TTS"""
    print(f"🎙️ توليد التعليق الصوتي ({voice})...")
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
    """تنزيل مقاطع الفيديو من Pexels بدقة HD"""
    os.makedirs(output_dir, exist_ok=True)
    video_files = []

    if not PEXELS_API_KEY:
        print("⚠️ PEXELS_API_KEY غير متوفر، سيتم استخدام الخلفية الرسومية.")
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
                    mp4_files = [f for f in files if f.get("file_type") == "video/mp4" and (f.get("width", 0) >= 1280)]
                    selected_file = mp4_files[0] if mp4_files else files[0]
                    
                    target_path = os.path.join(output_dir, f"clip_{len(video_files)+1}.mp4")
                    v_res = requests.get(selected_file["link"], stream=True, timeout=30)
                    with open(target_path, "wb") as f:
                        for chunk in v_res.iter_content(chunk_size=1024*1024):
                            f.write(chunk)
                    video_files.append(target_path)
                    print(f"📥 تم تحميل كليب: {kw}")
        except Exception as e:
            print(f"⚠️ خطأ أثناء تنزيل ({kw}): {e}")

    return video_files

def render_documentary(channel_key, audio_path, video_clips, output_file):
    """دمج المقاطع والصوت وإنتاج الفيديو بمقاس 16:9 بجودة 1080p عبر FFmpeg"""
    print(f"🎞️ بدء رندر الفيديو النهائي: {output_file}...")

    probe_cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {audio_path}"
    duration_str = subprocess.check_output(probe_cmd, shell=True).decode().strip()
    audio_duration = float(duration_str) if duration_str else 30.0

    if video_clips:
        standardized_clips = []
        for i, clip in enumerate(video_clips):
            norm_path = f"norm_{channel_key}_{i}.mp4"
            conv_cmd = f'ffmpeg -y -i {clip} -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1" -r 30 -an {norm_path}'
            subprocess.run(conv_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            standardized_clips.append(norm_path)

        list_file = f"concat_{channel_key}.txt"
        with open(list_file, "w") as f:
            for sc in standardized_clips:
                f.write(f"file '{sc}'\n")

        cmd = (
            f'ffmpeg -y -f concat -safe 0 -stream_loop -1 -i {list_file} '
            f'-i {audio_path} -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 192k '
            f'-t {audio_duration} -shortest {output_file}'
        )
    else:
        cfg = CHANNEL_CONFIGS.get(channel_key, CHANNEL_CONFIGS["masar"])
        cmd = (
            f'ffmpeg -y -f lavfi -i color=c=black:s=1920x1080:d={audio_duration} -i {audio_path} '
            f'-vf "drawtext=text=\'{cfg["name"]}\':fontcolor=white:fontsize=72:x=(w-text_w)/2:y=(h-text_h)/2" '
            f'-c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest {output_file}'
        )

    subprocess.run(cmd, shell=True, check=True)
    print(f"✅ تم إنتاج الفيديو بنجاح: {output_file}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", default="masar", choices=["abaad", "masharee", "masar"])
    args = parser.parse_args()

    channel_key = args.channel
    output_filename = f"documentary_{channel_key}.mp4"
    audio_filename = f"voiceover_{channel_key}.mp3"

    cfg = CHANNEL_CONFIGS[channel_key]
    script_text = generate_script(channel_key)
    audio_file = generate_voiceover(script_text, cfg["voice"], audio_filename)
    clips = download_pexels_clips(cfg["search_keywords"], output_dir=f"clips_{channel_key}")
    render_documentary(channel_key, audio_file, clips, output_filename)

if __name__ == "__main__":
    main()
