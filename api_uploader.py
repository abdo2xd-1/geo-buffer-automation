import os
import sys
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

CHANNELS_MAP = {
    "masharee": "REFRESH_TOKEN_MASHAREE",
    "abaad": "REFRESH_TOKEN_ABAAD",
    "masar": "REFRESH_TOKEN_MASAR"
}

def upload_to_youtube(channel_key, video_file, title, description):
    secret_env = CHANNELS_MAP.get(channel_key.lower().strip())
    client_id = os.getenv("YOUTUBE_CLIENT_ID")
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.getenv(secret_env)

    if not all([client_id, client_secret, refresh_token]):
        raise ValueError(f"بيانات الاعتماد ناقصة للقناة: {channel_key}")

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret
    )

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

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"[{channel_key}] تقدم الرفع: {int(status.progress() * 100)}%")

    print(f"✅ تم الرفع بنجاح! الرابط: https://youtu.be/{response.get('id')}")

if __name__ == "__main__":
    upload_to_youtube(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
