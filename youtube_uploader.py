import os
import sys
import json
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "").strip()
CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "").strip()
REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN", "").strip()

def get_authenticated_service():
    """تجديد الصلاحيات التلقائي باستخدام Refresh Token"""
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }
    r = requests.post(token_url, data=payload, timeout=20)
    if r.status_code != 200:
        raise Exception(f"فشل تجديد توكن يوتيوب: {r.text}")
    
    access_token = r.json()["access_token"]
    creds = Credentials(token=access_token)
    return build("youtube", "v3", credentials=creds)

def upload_long_documentary(video_file, metadata_file="video_metadata.json"):
    if not os.path.exists(video_file):
        raise FileNotFoundError(f"ملف الفيديو غير موجود: {video_file}")

    title = "فيلم وثائقي استقصائي جديد"
    desc = "تحقيق وثائقي شامل يكشف كواليس الممرات المائية وأسرار الجغرافيا.\n\n#أبعاد_جغرافية #وثائقي"

    if os.path.exists(metadata_file):
        with open(metadata_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            title = data.get("title", title)
            desc = data.get("desc", desc)

    print(f"🚀 جاري الرفع المباشر لليوتيوب: {title}")
    youtube = get_authenticated_service()

    body = {
        "snippet": {
            "title": title[:95],
            "description": desc,
            "tags": ["وثائقي", "أبعاد جغرافية", "تحقيق", "جغرافيا", "وثائقيات"],
            "categoryId": "27" # فئة التعليم والمعرفة
        },
        "status": {
            "privacyStatus": "public", # أو "unlisted" لو تحب مراجعته قبل أن يراه المتابعون
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(
        video_file,
        chunksize=1024*1024*10, # رفع بأجزاء 10MB لضمان استقرار رفع الأحجام الكبيرة
        resumable=True,
        mimetype="video/mp4"
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"⏳ تقدم الرفع: {int(status.progress() * 100)}%")

    video_id = response.get("id")
    print(f"🎉 تم نشر الفيديو الوثائقي بنجاح! الرابط: https://youtu.be/{video_id}")
    return video_id

if __name__ == "__main__":
    vid_path = sys.argv[1] if len(sys.argv) > 1 else "documentary_30min.mp4"
    upload_long_documentary(vid_path)
