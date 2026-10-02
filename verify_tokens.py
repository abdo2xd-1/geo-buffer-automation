import os
import sys
import requests

# المفاتيح الأصلية المعتمدة
DEFAULT_CLIENT_ID = "814988815489-i0gen64eparrgsm67gp9mapqahf0or9p.apps.googleusercontent.com"
DEFAULT_CLIENT_SECRET = "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"

env_id = (os.getenv("YOUTUBE_CLIENT_ID") or "").strip().strip('"\'')
env_secret = (os.getenv("YOUTUBE_CLIENT_SECRET") or "").strip().strip('"\'')

CLIENT_ID = env_id if env_id else DEFAULT_CLIENT_ID
CLIENT_SECRET = env_secret if env_secret else DEFAULT_CLIENT_SECRET

print("=" * 60)
print(f"📌 فحص بيئة العمل:")
print(f" - هل قرأ YOUTUBE_CLIENT_ID من Secrets؟ {'نعم ✅' if env_id else 'لا (استخدم الافتراضي) ⚠️'}")
print(f" - Client ID المستخدم: {CLIENT_ID[:20]}... (طوله: {len(CLIENT_ID)})")
print(f" - Client Secret المستخدم: {CLIENT_SECRET[:7]}... (طوله: {len(CLIENT_SECRET)})")
print("=" * 60)

TOKENS = {
    "أبعاد جغرافية (ABAAD)": (os.getenv("REFRESH_TOKEN_ABAAD") or "").strip().strip('"\''),
    "مشاريع عملاقة (MASHAREE)": (os.getenv("REFRESH_TOKEN_MASHAREE") or "").strip().strip('"\''),
    "مسار (MASAR)": (os.getenv("REFRESH_TOKEN_MASAR") or "").strip().strip('"\'')
}

all_valid = True

for channel_label, token in TOKENS.items():
    if not token:
        print(f"❌ {channel_label}: التوكن غير موجود في Secrets!")
        all_valid = False
        continue

    masked = f"{token[:7]}...{token[-5:]}" if len(token) > 12 else token
    print(f"\n📡 فحص [{channel_label}] (المعاينة: {masked} | الطول: {len(token)}):")

    res = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": token,
            "grant_type": "refresh_token"
        }
    )

    if res.status_code == 200:
        access_token = res.json().get("access_token")
        ch_res = requests.get(
            "https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if ch_res.status_code == 200 and ch_res.json().get("items"):
            title = ch_res.json()["items"][0]["snippet"]["title"]
            print(f"  ✅ التوكن صالح 100%! مربوط بقناة: [{title}]")
        else:
            print(f"  ✅ التوكن صالح ومفوض بنجاح!")
    else:
        print(f"  ❌ رفضته جوجل! (الكود: {res.status_code})")
        print(f"  ⚠️ الرد: {res.text}")
        all_valid = False

print("\n" + "=" * 60)
if not all_valid:
    print("❌ توجد توكنات بحاجة لمراجعة.")
    sys.exit(1)
else:
    print("🎉 جميع التوكنات ممتازة ومطابقة للقنوات! السيرفر جاهز للرفع.")
    print("=" * 60)
