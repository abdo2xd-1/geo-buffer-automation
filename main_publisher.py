import os
import sys
import random
import requests

# 1. جلب المفاتيح وتطهيرها برمجياً من أي محارف Unicode غريبة
RAW_BUFFER_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN", "").strip()
RAW_PEXELS_KEY = os.getenv("PEXELS_API_KEY", "").strip()

BUFFER_TOKEN = RAW_BUFFER_TOKEN

# تصفية المفتاح ليكون فقط أحرف وأرقام إنجليزية صالحة (ASCII)
CLEAN_PEXELS_KEY = "".join([c for c in RAW_PEXELS_KEY if ord(c) < 128]).strip()

print(f"🔑 Pexels Raw Key Length: {len(RAW_PEXELS_KEY)}")
print(f"🔑 Pexels Clean Key Length: {len(CLEAN_PEXELS_KEY)}")

# 2. إعدادات القنوات والكلمات المفتاحية
CHANNELS = {
    "abaad_geo": {
        "name": "أبعاد جغرافية",
        "id": os.getenv("BUFFER_CHANNEL_ABAAD", "6abace7bea19ca0bde181dff").strip(),
        "keywords": ["desert landscape aerial", "canyon mountains", "earth geographic nature", "river delta"],
        "hashtags": "#أبعاد_جغرافية #جغرافيا #وثائقي #طبيعة #استكشاف"
    },
    "megabuilds": {
        "name": "مشاريع عملاقة",
        "id": os.getenv("BUFFER_CHANNEL_MEGABUILDS", "6abace11ea19ca0bde181821").strip(),
        "keywords": ["construction engineering", "massive bridge architecture", "skyscraper construction", "heavy machinery"],
        "hashtags": "#مشاريع_عملاقة #هندسة #بناء #تطوير #مستقبل"
    },
    "masar": {
        "name": "مسار",
        "id": os.getenv("BUFFER_CHANNEL_MASAR", "6abacd06ea19ca0bde180ef9").strip(),
        "keywords": ["cargo shipping container port", "modern city highway", "solar power farm", "global trade logistic"],
        "hashtags": "#مسار #اقتصاد #تجارة #تحليل #جيوسياسة"
    }
}

def get_pexels_4k_video(query, orientation="landscape"):
    url = f"https://api.pexels.com/videos/search?query={query}&orientation={orientation}&per_page=15"
    headers = {
        "Authorization": CLEAN_PEXELS_KEY
    }
    
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
        
        chosen_video = random.choice(videos)
        video_files = chosen_video.get("video_files", [])
        
        best_file = None
        # البحث عن أعلى جودة (4K أو UHD)
        for vf in video_files:
            width = vf.get("width", 0)
            height = vf.get("height", 0)
            if width >= 3840 or height >= 2160:
                best_file = vf
                break
        
        if not best_file and video_files:
            best_file = max(video_files, key=lambda x: (x.get("width", 0) * x.get("height", 0)))
            
        if best_file:
            print(f"✅ تم اختيار فيديو بجودة: {best_file.get('width')}x{best_file.get('height')}")
            return best_file.get("link")
        
    except Exception as e:
        print(f"❌ استثناء أثناء جلب الفيديو: {e}")
        
    return None

def publish_to_buffer(channel_id, text, video_url):
    url = "https://api.bufferapp.com/1/updates/create.json"
    headers = {
        "Authorization": f"Bearer {BUFFER_TOKEN}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    payload = {
        "profile_ids[]": channel_id,
        "text": text,
        "now": False,
        "media[video]": video_url
    }
    
    try:
        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == 200:
            print(f"🚀 تم بنجاح جدولة الفيديو للقناة: {channel_id}")
        else:
            print(f"❌ فشل الإرسال إلى Buffer ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"❌ استثناء في Buffer: {e}")

def run_job(job_type):
    is_short = (job_type == "short")
    orientation = "portrait" if is_short else "landscape"
    
    for key, config in CHANNELS.items():
        print(f"\n--- جاري المعالجة لقناة: {config['name']} ({job_type}) ---")
        keyword = random.choice(config["keywords"])
        
        video_url = get_pexels_4k_video(keyword, orientation=orientation)
        if not video_url:
            continue
            
        if is_short:
            title = f"شاهد روعة المشهد وتفاصيل مذهلة بتقنية 4K ⚡\n\n{config['hashtags']} #Shorts #4K"
        else:
            title = f"وثائقي حصري بدقة 4K فائقة: تفاصيل وأسرار حصرية 🌍🎬\n\n{config['hashtags']}"
            
        publish_to_buffer(config["id"], title, video_url)

if __name__ == "__main__":
    target_job = sys.argv[1] if len(sys.argv) > 1 else "short"
    run_job(target_job)
