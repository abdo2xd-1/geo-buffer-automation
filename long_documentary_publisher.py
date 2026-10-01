import os
import sys
import random
import asyncio
import json
import re
import subprocess
import requests
import PIL.Image

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

# موسيقى وثائقية سينمائية محيطية طويلة
DOC_BGM_URL = "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3?filename=dark-mystery-trailer-111586.mp3"

def ensure_bgm():
    if not os.path.exists("doc_bgm.mp3"):
        try:
            r = requests.get(DOC_BGM_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=25)
            if r.status_code == 200:
                with open("doc_bgm.mp3", "wb") as f:
                    f.write(r.content)
        except Exception as e:
            print(f"⚠️ تعذر تنزيل الموسيقى: {e}")

def get_best_arabic_font(size=42):
    for p in [
        "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoKufiArabic-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()

def clean_arabic(text):
    return re.sub(r'[^\w\s\d\u0600-\u06FF!؟,\.\:\-\(\)\"\$]+', '', text).strip()

def call_gemini_raw(prompt):
    """استدعاء Gemini مع التبديل التلقائي بين النماذج النشطة"""
    candidate_models = ["gemini-1.5-flash-latest", "gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
    for model in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
            if res.status_code == 200:
                txt = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                txt = txt.strip().replace("```json", "").replace("```", "")
                return txt
        except Exception:
            continue
    raise Exception("فشلت جميع نماذج Gemini في الاستجابة.")

# 2. توليد المخطط العام للوثائقي الكبير (6 فصول كبرى)
def generate_documentary_outline(niche_name):
    print("🧠 جاري بناء المخطط الاستقصائي للفيلم الوثائقي الكبير (30 دقيقة)...")
    prompt = f"""
أنت مخرج ومحقق وثائقي محترف مثل غابرييل عماد و Vox.
المجال: {niche_name}.
المطلوب: بناء مخطط لفيلم وثائقي مطول وشديد الإثارة والعمق مدته 30 دقيقة.
قسّم الفيلم إلى 6 فصول محورية كبرى تعالج القضية من جذورها التاريخية والسياسية والاقتصادية والمستقبلية.

أخرج النتيجة بصيغة JSON حصراً:
{{
  "title": "عنوان وثائقي ملحمي يثير الفضول",
  "desc": "وصف كامل ومفصل للوثائقي مع الهاشتاجات وروابط الفصول",
  "chapters": [
    {{"chapter_idx": 1, "title": "عنوان الفصل 1: اللغز ونقطة الصفر"}},
    {{"chapter_idx": 2, "title": "عنوان الفصل 2: الجذور الجيوسياسية والتاريخية"}},
    {{"chapter_idx": 3, "title": "عنوان الفصل 3: كواليس المعركة والأرقام الخارقة"}},
    {{"chapter_idx": 4, "title": "عنوان الفصل 4: حركة الأموال وتريليونات سلاسل الإمداد"}},
    {{"chapter_idx": 5, "title": "عنوان الفصل 5: الصراع الاستخباراتي والدولي المعاصر"}},
    {{"chapter_idx": 6, "title": "عنوان الفصل 6: سيناريوهات المستقبل والكلمة الأخيرة"}}
  ]
}}
    """
    txt = call_gemini_raw(prompt)
    return json.loads(txt)

# 3. توليد نصوص المشاهد المتعمقة لكل فصل (بمعدل 4 إلى 5 مشاهد دسمة)
def generate_chapter_deep_scenes(niche_name, doc_title, chapter_info):
    print(f"✍️ كتابة السرد الموسع للفصل: {chapter_info['title']}")
    prompt = f"""
أنت محقق وثائقي بارع. الفيلم بعنوان: "{doc_title}" في مجال "{niche_name}".
الفصل المطلوب كتابته بالتفصيل: "{chapter_info['title']}".
المطلوب: كتابة 5 مشاهد وثائقية متتالية ومتصلة لهذا الفصل.
لكل مشهد، اكتب فقرة سردية طويلة ودسمة بالعامية المصرية الراقية والمشوقة (حوالي 85 إلى 110 كلمة لكل مشهد) تسرد تفاصيل وحقائق وأرقام عميقة دون استعجال.

أخرج النتيجة بصيغة JSON حصراً:
{{
  "scenes": [
    {{
      "narration": "نص سردي وثائقي مفصل وطويل بالعامية المصرية يشرح الأحداث بدقة...",
      "query": "cinematic landscape 4k detailed stock footage english query",
      "lower_third": "📍 الموقع أو التوثيق الرقمي المعروض"
    }}
  ]
}}
    """
    txt = call_gemini_raw(prompt)
    return json.loads(txt).get("scenes", [])

# 4. التوليد الصوتي
async def generate_voice(text, output_file):
    import edge_tts
    # وتيرة متزنة ومناسبة للأفلام الطويلة
    communicate = edge_tts.Communicate(text, "ar-EG-ShakirNeural", rate="+4%")
    await communicate.save(output_file)

# 5. جلب الفيديو الأفقي 16:9
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
        except Exception:
            pass
    return False

# 6. لوحة التعريف السفلية (Lower-Third 16:9)
def create_lower_third(text, target_path, size=(1920, 1080)):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = get_best_arabic_font(size=34)

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

# 7. رندر الفصل الواحد كملف مستقل (Chunk)
def render_chapter_chunk(scenes_list, chapter_title, chapter_idx):
    size = (1920, 1080)
    scenes = []
    temp_files = []
    voice_clips = []
    current_time = 0.0

    print(f"\n🎬 معالجة وتصدير الفصل {chapter_idx} ({len(scenes_list)} مشاهد موسعة)...")

    for s_idx, sc in enumerate(scenes_list):
        aud_path = f"aud_c{chapter_idx}_s{s_idx}.mp3"
        asyncio.run(generate_voice(sc["narration"], aud_path))
        aud_clip = AudioFileClip(aud_path)
        duration = aud_clip.duration + 0.35
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
        create_lower_third(sc.get("lower_third", chapter_title), lt_path, size=size)
        temp_files.append(lt_path)
        lt_clip = ImageClip(lt_path).set_duration(min(5.0, duration)).set_start(0.5)

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
        bitrate="3500k",
        preset="ultrafast",
        threads=2
    )

    for f in temp_files:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

    return chunk_filename

# 8. دمج الفصول وإضافة تراك الموسيقى التصويرية الممتد
def stitch_and_finalize_documentary(chunk_files, output_filename="documentary_30min.mp4"):
    print("\n⚡ بدء الدمج الفوري لجميع الفصول عبر FFmpeg...")
    list_path = "chapters_list.txt"
    with open(list_path, "w", encoding="utf-8") as f:
        for chunk in chunk_files:
            f.write(f"file '{chunk}'\n")

    temp_stitched = "temp_raw_stitched.mp4"
    cmd_concat = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_path,
        "-c", "copy",
        temp_stitched
    ]
    subprocess.run(cmd_concat, check=True)

    # دمج الموسيقى التصويرية المحيطية الهادئة تحت الفيديو بالكامل
    ensure_bgm()
    if os.path.exists("doc_bgm.mp3"):
        print("🎵 دمج الموسيقى التصويرية الوثائقية بكامل مدة الفيلم...")
        cmd_audio = [
            "ffmpeg", "-y",
            "-i", temp_stitched,
            "-stream_loop", "-1", "-i", "doc_bgm.mp3",
            "-filter_complex", "[1:a]volume=0.08[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=3[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            output_filename
        ]
        subprocess.run(cmd_audio, check=True)
        if os.path.exists(temp_stitched):
            os.remove(temp_stitched)
    else:
        os.rename(temp_stitched, output_filename)

    if os.path.exists(list_path):
        os.remove(list_path)
    for chunk in chunk_files:
        if os.path.exists(chunk):
            os.remove(chunk)

    print(f"🎉 تم بنجاح إنتاج الفيلم الوثائقي الطويل: {output_filename}")
    return output_filename

def main():
    niche_name = NICHE_NAMES[0] # البدء بـ "أبعاد جغرافية"
    print(f"=======================================================")
    print(f"🚀 بدء إنتاج فيلم وثائقي ضخم (25 - 30 دقيقة): {niche_name}")
    print(f"=======================================================")

    doc_outline = generate_documentary_outline(niche_name)
    print(f"📌 عنوان الوثائقي: {doc_outline['title']}")

    chunk_files = []
    for ch in doc_outline["chapters"]:
        scenes = generate_chapter_deep_scenes(niche_name, doc_outline["title"], ch)
        chunk_file = render_chapter_chunk(scenes, ch["title"], ch["chapter_idx"])
        chunk_files.append(chunk_file)

    final_video_path = stitch_and_finalize_documentary(chunk_files, "documentary_30min.mp4")

    with open("video_metadata.json", "w", encoding="utf-8") as f:
        json.dump({
            "title": doc_outline["title"],
            "desc": doc_outline["desc"]
        }, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
