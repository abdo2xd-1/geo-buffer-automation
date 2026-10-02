import os
import sys
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

def get_channel_service(channel_key: str):
    client_id = os.getenv("YOUTUBE_CLIENT_ID")
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.getenv(f"REFRESH_TOKEN_{channel_key}")

    creds = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret
    )
    return build("youtube", "v3", credentials=creds)

def upload_documentary(file_path: str, channel_key: str):
    # قراءة العنوان والوصف المولدين تلقائياً
    title = "وثائقي خاص"
    description = "وثائقي شامل يستعرض أهم الحقائق والتحليلات المعمقة."
    
    if os.path.exists("video_meta.json"):
        with open("video_meta.json", "r", encoding="utf-8") as f:
            meta = json.load(f)
            title = meta.get("title", title)
            description = f"{meta.get('topic', '')}\n\n#وثائقي #معلومات #استكشاف #حقائق"

    print(f"🚀 جاري رفع الوثائقي إلى [{channel_key}]: \"{title}\"...")
    youtube = get_channel_service(channel_key)
    
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": ["وثائقي", "حقائق", "أسرار", "تاريخ", "علوم", "استكشاف"],
            "categoryId": "27"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }
    
    media = MediaFileUpload(file_path, chunksize=10*1024*1024, resumable=True)
    request = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  📊 نسبة الرفع: {int(status.progress() * 100)}%")
            
    print(f"🎉 تم النشر بنجاح على يوتيوب: https://youtu.be/{response['id']}")

if __name__ == "__main__":
    ch_key = sys.argv[1]  # ABAAD أو MASHAREE أو MASAR
    upload_documentary("final_documentary.mp4", ch_key)
