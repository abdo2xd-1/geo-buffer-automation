import os
import sys
import requests

CLIENT_ID = (os.getenv("YOUTUBE_CLIENT_ID") or "").strip().strip('"\'')
CLIENT_SECRET = (os.getenv("YOUTUBE_CLIENT_SECRET") or "").strip().strip('"\'')

TOKENS = {
    "أبعاد جغرافية (ABAAD)": (os.getenv("REFRESH_TOKEN_ABAAD") or "").strip().strip('"\''),
    "مشاريع عملاقة (MASHAREE)": (os.getenv("REFRESH_TOKEN_MASHAREE") or "").strip().strip('"\''),
    "مسار (MASAR)": (os.getenv("REFRESH_TOKEN_MASAR") or "").strip().strip('"\'')
}

print("=" * 60)
print("🔍 جاري فحص صلاحية التوكنات للقنوات الثلاث مع سيرفرات جوجل...")
print("=" * 60)

all_valid = True

for channel_label, token in TOKENS.items():
    if not token:
        print(f"❌ {channel_label}: التوكن غير موجود أو فارغ في GitHub Secrets!")
        all_valid = False
        continue

    masked = f"{token[:7]}...{token[-5:]}" if len(token) > 12 else token
    print(f"\n📡 فحص [{channel_label}] (طول التوكن: {len(token)} | المعاينة: {masked}):")

    # إرسال طلب تجديد مباشر إلى Google OAuth
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
        # التحقق من اسم القناة الفعلي من YouTube Data API
        ch_res = requests.get(
            "https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if ch_res.status_code == 200 and ch_res.json().get("items"):
            title = ch_res.json()["items"][0]["snippet"]["title"]
            print(f"  ✅ التوكن صالح 100%! مربوط فعلياً بقناة: [{title}]")
        else:
            print(f"  ✅ التوكن صالح وتم تجديده بنجاح!")
    else:
        print(f"  ❌ رفضته جوجل! كود الخطأ: {res.status_code}")
        print(f"  ⚠️ استجابة جوجل: {res.text}")
        all_valid = False

print("\n" + "=" * 60)
if not all_valid:
    print("❌ توجد توكنات بحاجة لتصحيح في GitHub Secrets قبل بدء الإنتاج.")
    sys.exit(1)
else:
    print("🎉 جميع التوكنات ممتازة ومطابقة للقنوات! بدء الرندر والنشر...")
    print("=" * 60)
