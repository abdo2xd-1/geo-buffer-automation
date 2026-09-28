import os
import sys
import random
import requests

# 1. جلب المفاتيح من متغيرات البيئة
BUFFER_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN", "").strip()
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "").strip()

# تنظيف مفتاح Pexels
CLEAN_PEXELS_KEY = "".join([c for c in PEXELS_API_KEY if ord(c) < 128]).strip()
print(f"🔑 Pexels Key Length: {len(CLEAN_PEXELS_KEY)}")

# 2. معرفات القنوات
DEFAULT_CHANNELS = [
    "6abacd06ea19ca0bde180ef9",
    "6abace11ea19ca0bde181821",
    "6abace7bea19ca0bde181dff"
]

env_channel_str = os.getenv("BUFFER_CHANNEL_IDS", "").strip()
if env_channel_str:
    channels_list = [ch.strip() for ch in env_channel_str.replace("\n", ",").split(",") if ch.strip()]
else:
    channels_list = DEFAULT_CHANNELS

# قوالب القنوات
CHANNEL_TEMPLATES = [
    {
        "name": "أبعاد جغرافية",
        "keywords": ["desert landscape aerial", "canyon mountains nature", "river delta satellite"],
        "hashtags": "#أبعاد_جغرافية #جغرافيا #وثائقي #طبيعة #استكشاف"
    },
    {
        "name": "مشاريع عملاقة",
        "keywords": ["mega construction engineering", "massive bridge architecture", "heavy machinery dam"],
        "hashtags": "#مشاريع_عملاقة #هندسة #بناء #تطوير #مستقبل"
    },
    {
        "name": "مسار",
        "keywords": ["cargo shipping container port", "modern city highway aerial", "solar energy power farm"],
        "hashtags": "#مسار #اقتصاد #تجارة #تحليل #جيوسياسة"
    }
]

# روابط فيديوهات 4K احتياطية صالحة ومباشرة
FALLBACK_4K_LANDSCAPE = [
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4"
]
FALLBACK_4K_PORTRAIT = [
    "https://assets.mixkit.co/videos/preview/mixkit-aerial-view-of-city-traffic-at-night-41546-large.mp4",
    "https://assets.mixkit.co/videos/preview/mixkit-top-aerial-shot-of-a-seashore-with-waves-41551-large.mp4"
]

def get_video_url(query, orientation="landscape"):
    """جلب الفيديو من Pexels أو استخدام الرابط المباشر الاحتياطي"""
    if len(CLEAN_PEXELS_KEY) >= 50:
        url = f"https://api.pexels.com/videos/search?query={query}&orientation={orientation}&per_page=15"
        headers = {"Authorization": CLEAN_PEXELS_KEY}
        try:
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200:
                videos = res.json().get("videos", [])
                if videos:
                    chosen = random.choice(videos)
                    files = chosen.get("video_files", [])
                    best = next((vf for vf in files if vf.get("width", 0) >= 3840 or vf.get("height", 0) >= 2160), None)
                    if not best and files:
                        best = max(files, key=lambda x: (x.get("width", 0) * x.get("height", 0)))
                    if best:
                        print(f"✅ فيديو من Pexels بدقة: {best.get('width')}x{best.get('height')}")
                        return best.get("link")
            else:
                print(f"⚠️ Pexels Status ({res.status_code}): {res.text}")
        except Exception as e:
            print(f"⚠️ استثناء Pexels: {e}")

    print("ℹ️ جاري استخدام رابط فيديو عالي الدقة احتياطي...")
    return random.choice(FALLBACK_4K_PORTRAIT if orientation == "portrait" else FALLBACK_4K_LANDSCAPE)

def publish_to_buffer_graphql(channel_id, text, video_url):
    """الجدولة عبر Buffer GraphQL API وفق المخطط الرسمي المحدث"""
    url = "https://api.buffer.com"
    headers = {
        "Authorization": f"Bearer {BUFFER_TOKEN}",
        "Content-Type": "application/json"
    }

    query = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess {
          post {
            id
            status
          }
        }
        ... on MutationError {
          message
        }
      }
    }
    """

    # الهيكل الصحيح تماماً لحقل الفيديو في Buffer
    variables = {
        "input": {
            "channelId": channel_id,
            "text": text,
            "schedulingType": "automatic",
            "mode": "addToQueue",
            "assets": [
                {
                    "video": {
                        "url": video_url
                    }
                }
            ]
        }
    }

    try:
        response = requests.post(url, headers=headers, json={"query": query, "variables": variables}, timeout=30)
        res_data = response.json()
        
        if "errors" in res_data:
            print(f"❌ خطأ GraphQL للقناة [{channel_id}]: {res_data['errors']}")
        else:
            result = res_data.get("data", {}).get("createPost", {})
            if "post" in result and result["post"]:
                print(f"🚀 تم بنجاح جدولة الفيديو للقناة [{channel_id}] | Post ID: {result['post']['id']}")
            elif "message" in result:
                print(f"⚠️ استجابة Buffer للقناة [{channel_id}]: {result['message']}")
            else:
                print(f"✅ استجابة Buffer: {res_data}")
    except Exception as e:
        print(f"❌ استثناء أثناء الاتصال بـ Buffer: {e}")

def run_job(job_type):
    is_short = (job_type == "short")
    orientation = "portrait" if is_short else "landscape"

    for idx, channel_id in enumerate(channels_list):
        template = CHANNEL_TEMPLATES[idx % len(CHANNEL_TEMPLATES)]
        print(f"\n--- جاري المعالجة: {template['name']} ({channel_id}) [{job_type}] ---")
        
        keyword = random.choice(template["keywords"])
        video_url = get_video_url(keyword, orientation=orientation)
        
        if is_short:
            title = f"شاهد روعة المشهد وتفاصيل مذهلة بتقنية 4K ⚡\n\n{template['hashtags']} #Shorts #4K"
        else:
            title = f"وثائقي حصري بدقة 4K فائقة: تفاصيل وأسرار حصرية 🌍🎬\n\n{template['hashtags']}"
            
        publish_to_buffer_graphql(channel_id, title, video_url)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "short"
    run_job(target)
