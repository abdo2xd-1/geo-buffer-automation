import os
import sys
import random
import re
import requests

# 1. جلب المفاتيح وتطهير مفتاح Pexels تماماً من أي مسافات داخلية أو حروف غير مدعومة
BUFFER_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN", "").strip()
RAW_PEXELS_KEY = os.getenv("PEXELS_API_KEY", "")

# إزالة أي مسافات أو رموز والاحتفاظ فقط بالأحرف والأرقام الإنجليزية
CLEAN_PEXELS_KEY = re.sub(r'[^a-zA-Z0-9]', '', RAW_PEXELS_KEY).strip()

print(f"🔑 Pexels Key Length: {len(CLEAN_PEXELS_KEY)}")
if len(CLEAN_PEXELS_KEY) > 8:
    print(f"🔑 Key Preview: {CLEAN_PEXELS_KEY[:4]}...{CLEAN_PEXELS_KEY[-4:]}")

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

# روابط فيديوهات مباشرة ومفتوحة من Google Cloud لا تحظر سيرفرات Buffer أبداً
FALLBACK_LANDSCAPE = [
    "https://storage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
    "https://storage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
    "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"
]
FALLBACK_PORTRAIT = [
    "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
    "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
    "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyBlazes.mp4"
]

def get_video_url(query, orientation="landscape"):
    """جلب الفيديو من Pexels أو استخدام الرابط المباشر الموثوق"""
    if len(CLEAN_PEXELS_KEY) >= 50:
        url = f"https://api.pexels.com/videos/search?query={query}&orientation={orientation}&per_page=15"
        headers = {
            "Authorization": CLEAN_PEXELS_KEY,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
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

    print("ℹ️ جاري استخدام رابط فيديو مباشر وموثوق لـ Buffer...")
    return random.choice(FALLBACK_PORTRAIT if orientation == "portrait" else FALLBACK_LANDSCAPE)

def publish_to_buffer_graphql(channel_id, video_title, description_text, video_url):
    """الجدولة عبر Buffer GraphQL API مع كامل المتطلبات"""
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

    variables = {
        "input": {
            "channelId": channel_id,
            "text": description_text,
            "schedulingType": "automatic",
            "mode": "addToQueue",
            "assets": [
                {
                    "video": {
                        "url": video_url
                    }
                }
            ],
            "metadata": {
                "youtube": {
                    "title": video_title[:95],
                    "categoryId": "27",
                    "madeForKids": False
                }
            }
        }
    }

    try:
        response = requests.post(url, headers=headers, json={"query": query, "variables": variables}, timeout=35)
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
            video_title = f"{template['name']} | تفاصيل مذهلة بدقة فائقة"
            description = f"شاهد روعة المشهد وتفاصيل مذهلة بتقنية 4K ⚡\n\n{template['hashtags']} #Shorts #4K"
        else:
            video_title = f"وثائقي حصري: {template['name']} وأسرار المستقبل"
            description = f"وثائقي حصري بجودة فائقة 4K: تحليل شامل وأسرار حصرية 🌍🎬\n\n{template['hashtags']}"
            
        publish_to_buffer_graphql(channel_id, video_title, description, video_url)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "short"
    run_job(target)
