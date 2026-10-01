import os
import sys
import random
import asyncio
import json
import re
import subprocess
import requests
import PIL.Image

# ترقيع التوافق بين Pillow و MoviePy
if not hasattr(PIL.Image, 'ANTIALIAS'):
    setattr(PIL.Image, 'ANTIALIAS', PIL.Image.Resampling.LANCZOS)

from PIL import Image, ImageDraw, ImageFont, features
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    ImageClip,
    ColorClip,
    CompositeVideoClip,
    CompositeAudioClip,
    concatenate_videoclips,
    vfx
)

# 1. المفاتيح والمجالات
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

NICHE_NAMES = ["أبعاد جغرافية", "مشاريع عملاقة", "مسار"]

# 2. إعداد الخط العربي للأبعاد العريضة (1920x1080)
def get_best_arabic_font(size=44):
    for p in [
        "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoKufiArabic-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

def clean_arabic(text):
    return re.sub(r'[^\w\s\d\u0600-\u06FF!؟,\.\:\-\(\)\"\$]+', '', text).strip()

# 3. محرك توليد سيناريو الـ 8 دقائق (نظام الفصول بأسلوب غابرييل عماد)
def generate_8min_documentary(niche_name):
    if not GEMINI_API_KEY:
        raise Exception("مفتاح GEMINI_API_KEY غير موجود في الـ Secrets.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    prompt = f"""
أنت مخرج ومحقق وثائقي محترف تصنع أفلاماً استقصائية مشوقة بالعامية المصرية بأسلوب "غابرييل عماد" و "Vox".
المجال المستهدف: {niche_name}.
المطلوب: إنتاج سيناريو فيلم وثائقي استقصائي متكامل مدته 8 دقائق (حوالي 1100 كلمة).

قسّم الفيلم إلى 5 فصول رئيسية:
- الفصل 1: اللغز والكارثة الافتتاحية (The Mystery Hook).
- الفصل 2: البعد الجغرافي والجذور التاريخية (Geopolitical Context).
- الفصل 3: صلب المعركة والأرقام الخارقة (The Core Conflict / Engineering Feat).
- الفصل 4: مليارات الدولارات وسلاسل الإمداد (Economic Fallout).
- الفصل 5: الخاتمة وسؤال المستقبل المفتوح (The Conclusion & Debate).

في كل فصل، ضع 3 مشاهد تفصيلية. في كل مشهد اكتب:
- "narration": نص سردي مشوق وطويل نسبياً بالعامية المصرية الراقية (حوالي 70 إلى 80 كلمة لكل مشهد).
- "query": كلمة بحث سينمائية بالإنجليزية لجلب لقطات عريضة من Pexels (Landscape).
- "lower_third": عنوان توثيقي يظهر أسفل الشاشة (مثل: "📍 مضيق هرمز - الخليج العربي" أو "🏗️ تكلفة المشروع: 24 مليار $").

أخرج النتيجة بتنسيق JSON خالص وبدون أي علامات Markdown:
{{
  "title": "عنوان وثائقي ناري وجذاب جداً",
  "desc": "وصف مفصل للوثائقي مع روابط الفصول والهاشتاجات",
  "chapters": [
    {{
      "chapter_title": "عنوان الفصل الأول",
      "scenes": [
        {{
          "narration": "النص السردي الكامل بالعامية المصرية...",
          "query": "cinematic landscape cargo ship aerial 4k",
          "lower_third": "📍 بورسعيد - مدخل قناة السويس"
        }}
      ]
    }}
  ]
}}
    """
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    res = requests.post(url, json=payload, timeout=60)
    if res.status_code == 200:
        raw_text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
        raw_text = raw_text.strip().replace("```json", "").replace("```", "")
        return json.loads(raw_text)
    raise Exception(f"فشل الاتصال بـ Gemini: {res.text}")

# 4. التوليد الصوتي بالعامية المصرية الهادئة
async def generate_voice(text, output_file):
    import edge_tts
    communicate = edge_tts.Communicate(text, "ar-EG-ShakirNeural", rate="+6%")
    await communicate.save(output_file)

# 5. سحب لقطات أفقية (Landscape 16:9) بجودة Full HD
def fetch_landscape_video(query, target_filename):
    if PEXELS_API_KEY:
        try:
            url = f"https://api.pexels.com/videos/search?query={query}&per_page=5&orientation=landscape"
            headers = {"Authorization": PEXELS_API_KEY, "User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=20)
            if r.status_code == 200:
                vids = r.json().get("videos", [])
                if vids:
                    video_files = vids[0].get("video_files", [])
                    selected_link = None
                    for vf in video_files:
                        if vf.get("width") == 1920 and vf.get("height") == 1080:
                            selected_link = vf.get("link")
                            break
                    if not selected_link and video_files:
                        selected_link = video_files[0].get("link")

                    if selected_link:
                        v_resp = requests.get(selected_link, stream=True, timeout=40)
                        if v_resp.status_code == 200:
                            with open(target_filename, "wb") as f:
                                for chunk in v_resp.iter_content(chunk_size=1024*1024):
                                    if chunk: f.write(chunk)
                            return True
        except Exception as e:
            print(f"⚠️ خطأ في سحب لقطة {query}: {e}")
    return False

# 6. تصميم لوحة التعريف السفلية (Lower-Third 16:9)
def create_lower_third(text, target_path, size=(1920, 1080)):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = get_best_arabic_font(size=36)

    clean_txt = clean_arabic(text)
    has_raqm = features.check("raqm")
    if not has_raqm:
        import arabic_reshaper
        from bidi.algorithm import get_display
        clean_txt = get_display(arabic_reshaper.reshape(clean_txt))

    bbox = draw.textbbox((0, 0), clean_txt, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    bx2 = 1920 - 100
    bx1 = bx2 - tw - 50
    by1 = 1080 - 180
    by2 = by1 + th + 24

    draw.rounded_rectangle([bx1, by1, bx2, by2], radius=14, fill=(10, 15, 25, 220), outline=(0, 230, 255, 200), width=2)
    draw.text(((bx1 + bx2) // 2, by1 + 10), clean_txt, font=font, fill=(255, 255, 255, 255), anchor="mt", direction="rtl" if has_raqm else None)
    img.save(target_path)

# 7. بناء رندر الفصل الواحد وتصديره كملف مستقل
def render_chapter_chunk(chapter_data, chapter_idx):
    size = (1920, 1080)
    scenes = []
    temp_files = []
    voice_clips = []
    current_time = 0.0

    print(f"\n🎬 معالجة الفصل {chapter_idx + 1}: {chapter_data['chapter_title']}")

    for s_idx, sc in enumerate(chapter_data["scenes"]):
        aud_path = f"aud_c{chapter_idx}_s{s_idx}.mp3"
        asyncio.run(generate_voice(sc["narration"], aud_path))
        aud_clip = AudioFileClip(aud_path)
        duration = aud_clip.duration + 0.3
        temp_files.append(aud_path)

        voice_clips.append(aud_clip.set_start(current_time))

        vid_path = f"vid_c{chapter_idx}_s{s_idx}.mp4"
        success = fetch_landscape_video(sc["query"], vid_path)

        if success:
            try:
                clip = VideoFileClip(vid_path).without_audio()
                if clip.duration < duration:
                    clip = clip.fx(vfx.loop, duration=duration)
                else:
                    clip = clip.subclip(0, duration)
                clip = clip.resize(size)
                temp_files.append(vid_path)
            except Exception:
                clip = ColorClip(size=size, color=(15, 23, 42)).set_duration(duration)
        else:
            clip = ColorClip(size=size, color=(15, 23, 42)).set_duration(duration)

        lt_path = f"lt_c{chapter_idx}_s{s_idx}.png"
        create_lower_third(sc.get("lower_third", "وثائقي استقصائي"), lt_path, size=size)
        temp_files.append(lt_path)
        lt_clip = ImageClip(lt_path).set_duration(min(4.0, duration)).set_start(0.5)

        composed_scene = CompositeVideoClip([clip, lt_clip], size=size).set_duration(duration)
        scenes.append(composed_scene)
        current_time += duration

    chapter_video = concatenate_videoclips(scenes, method="compose")
    chapter_audio = CompositeAudioClip(voice_clips).set_duration(chapter_video.duration)
    chapter_video = chapter_video.set_audio(chapter_audio)

    chunk_filename = f"chunk_chapter_{chapter_idx}.mp4"
    chapter_video.write_videofile(
        chunk_filename,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        bitrate="4000k",
        preset="ultrafast",
        threads=2
    )

    for f in temp_files:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

    return chunk_filename

# 8. دمج الفصول نهائياً بـ FFmpeg في ثوانٍ
def stitch_chapters_with_ffmpeg(chunk_files, output_filename="documentary_8min.mp4"):
    print("\n⚡ بدء الدمج الفوري للفصول عبر FFmpeg Concat...")
    list_path = "chapters_list.txt"
    with open(list_path, "w", encoding="utf-8") as f:
        for chunk in chunk_files:
            f.write(f"file '{chunk}'\n")

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_path,
        "-c", "copy",
        output_filename
    ]
    subprocess.run(cmd, check=True)

    if os.path.exists(list_path):
        os.remove(list_path)
    for chunk in chunk_files:
        if os.path.exists(chunk):
            os.remove(chunk)

    print(f"🎉 تم إنتاج الفيلم الوثائقي الكامل بنجاح: {output_filename}")
    return output_filename

# 9. نقطة التشغيل الرئيسية
def main():
    niche_name = NICHE_NAMES[0] # البدء بـ "أبعاد جغرافية"
    print(f"=======================================================")
    print(f"🚀 بدء إنتاج فيلم وثائقي طويل (8 دقائق): {niche_name}")
    print(f"=======================================================")

    doc_data = generate_8min_documentary(niche_name)
    print(f"📌 عنوان الوثائقي: {doc_data['title']}")

    chunk_files = []
    for idx, chapter in enumerate(doc_data["chapters"]):
        chunk_path = render_chapter_chunk(chapter, idx)
        chunk_files.append(chunk_path)

    final_video_path = stitch_chapters_with_ffmpeg(chunk_files, "documentary_8min.mp4")

    with open("video_metadata.json", "w", encoding="utf-8") as f:
        json.dump({
            "title": doc_data["title"],
            "desc": doc_data["desc"]
        }, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
