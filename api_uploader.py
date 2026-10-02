import os
import sys
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

CHANNELS_MAP = {
    "masharee": "REFRESH_TOKEN_MASHAREE",
    "abaad": "REFRESH_TOKEN_ABAAD",
    "masar": "REFRESH_TOKEN_MASAR"
}

CLIENT_ID = "814988815489-i0gen64eparrgsm67gp9mapqahf0or9p.apps.googleusercontent.com"
CLIENT_SECRET = "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"

def upload_to_youtube(channel_key, video_file, title, description):
    channel_key = channel_key.lower().strip()
    secret_env = CHANNELS_MAP.get(channel_key)
    
    refresh_token = (os.getenv(secret_env) or "").strip().strip('"\'')

    if not refresh_token:
        sys.exit(f"❌ خطأ: التوكن غير معرّف للقناة {channel_key} ({secret_env})!")

    print(f"🔑 جاري تفويض الصلاحيات للقناة [{channel_key}]...")
    
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )

    creds.refresh(Request())
    print("✅ تم التحقق من الصلاحيات وتجديد الجلسة بنجاح!")

    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title[:95],
            "description": description,
            "categoryId": "27"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(video_file, chunksize=1024*1024*10, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    print(f"🚀 بدء الرفع الفعلي لملف {video_file} إلى يوتيوب...")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"[{channel_key}] تقدم الرفع: {int(status.progress() * 100)}%")

    print(f"🎉 تم النشر بنجاح على يوتيوب! الرابط: https://youtu.be/{response.get('id')}")

if __name__ == "__main__":
    upload_to_youtube(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
