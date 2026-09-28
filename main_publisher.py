import os
import sys
import random
import requests

# 1. مفاتيح الـ API من أسرار GitHub
BUFFER_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

# 2. إعدادات القنوات والكلمات المفتاحية المخصصة لكل قناة لضمان اختلاف المحتوى
CHANNELS = {
    "abaad_geo": {
        "name": "أبعاد جغرافية",
        "id": os.getenv("BUFFER_CHANNEL_ABAAD", "6abace7bea19ca0bde181dff"),
        "keywords": ["desert landscape", "canyon river", "aerial earth", "mountain range", "geographic map"],
        "hashtags": "#أبعاد_جغرافية #جغرافيا #وثائقي #طبيعة #استكشاف"
    },
    "megabuilds": {
        "name": "مشاريع عملاقة",
        "id": os.getenv("BUFFER_CHANNEL_MEGABUILDS", "6abace11ea19ca0bde181821"),
        "keywords": ["mega construction", "dam engineering", "futuristic bridge", "skyscraper architecture", "heavy machinery"],
        "hashtags": "#مشاريع_عملاقة #هندسة #بناء #تطوير #مستقبل"
    },
    "masar": {
        "name": "مسار",
        "id": os.getenv("BUFFER_CHANNEL_MASAR", "6abacd06ea19ca0bde180ef9"),
        "keywords": ["cargo port shipping", "global economy trade", "modern metropolis", "energy solar power", "highway transport"],
        "hashtags": "#مسار #اقتصاد #تجارة #تحليل #جيوسياسة"
    }
}

def get_pexels_4k_video(query, orientation="landscape"):
    """
    سحب فيديو بجودة 4K أو أعلى دقة متاحة من Pexels
    orientation: 'landscape' للفيديوهات الطويلة، 'portrait' للشورتس
    """
    url = f"https://api.pexels.com/videos/search?query={query}&orientation={orientation}&per_page=15"
    headers = {"Authorization": PEXELS_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"❌ خطأ Pexels ({response.status_code}): {response.text}")
            return None
        
        data = response.json()
        videos = data.get("videos", [])
        if not videos:
            print(f"⚠️ لم يتم العثور على فيديوهات للكلمة: {query}")
            return None
        
        # اختيار فيديو عشوائي من النتائج لضمان التجديد
        chosen_video = random.choice(videos)
        video_files = chosen_video.get("video_files", [])
        
        # البحث عن جودة 4K (عرض أو ارتفاع لا يقل عن 2160 أو 3840)
        best_file = None
        for vf in video_files:
            width = vf.get("width", 0)
            height = vf.get("height", 0)
            if width >= 3840 or height >= 2160:
                best_file = vf
                break
        
        # إذا لم يتوفر ملف صريح 4K نأخذ أعلى دقة متوفرة (UHD / HD)
        if not best_file and video_files:
            best_file = max(video_files, key=lambda x: (x.get("width", 0) * x.get("height", 0)))
            
        if best_file:
            print(f"✅ تم اختيار فيديو بجودة: {best_file.get('width')}x{best_file.get('height')}")
            return best_file.get("link")
        
    except Exception as e:
        print(f"❌ استثناء أثناء جلب الفيديو: {e}")
        
    return None

def publish_to_buffer(channel_id, text, video_url):
    """جدولة الفيديو على منصة Buffer"""
    url = "https://api.bufferapp.com/1/updates/create.json"
    headers = {
        "Authorization": f"Bearer {BUFFER_TOKEN}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    payload = {
        "profile_ids[]": channel_id,
        "text": text,
        "now": False,  # للإدراج التلقائي في الجدول (Schedule)
        "media[video]": video_url
    }
    
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        print(f"🚀 تم بنجاح إرسال التحديث للقناة: {channel_id}")
    else:
        print(f"❌ فشل الإرسال ({response.status_code}): {response.text}")

def run_job(job_type):
    """
    job_type: 'short' للنشر اليومي الرأسي، أو 'long' للنشر الأسبوعي الأفقي
    """
    is_short = (job_type == "short")
    orientation = "portrait" if is_short else "landscape"
    
    for key, config in CHANNELS.items():
        print(f"\n--- جاري المعالجة لقناة: {config['name']} ({job_type}) ---")
        keyword = random.choice(config["keywords"])
        
        video_url = get_pexels_4k_video(keyword, orientation=orientation)
        if not video_url:
            continue
            
        if is_short:
            title = f"شاهد قوة وتفاصيل مذهلة! دقيقة لا تفوتك ⚡\n\n{config['hashtags']} #Shorts #4K"
        else:
            title = f"وثائقي حصري بجودة فائقة 4K: تحليل شامل لأهم التطورات العالمية 🌍🎬\n\n{config['hashtags']}"
            
        publish_to_buffer(config["id"], title, video_url)

if __name__ == "__main__":
    # تمرير نوع المهمة من الـ Workflow: short أو long
    target_job = sys.argv[1] if len(sys.argv) > 1 else "short"
    run_job(target_job)
