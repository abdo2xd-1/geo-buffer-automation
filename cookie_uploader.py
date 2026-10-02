import os
import sys
import time
from playwright.sync_api import sync_playwright

CHANNELS_MAP = {
    "abaad": "COOKIES_ABAAD",
    "masharee": "COOKIES_MASHAREE",
    "masar": "COOKIES_MASAR"
}

def parse_netscape_cookies(cookies_text):
    """تحويل الكوكيز من تنسيق Netscape إلى تنسيق Playwright"""
    cookies = []
    for line in cookies_text.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 7:
            domain, flag, path, secure, expiration, name, value = parts[:7]
            clean_domain = domain.lstrip(".")
            cookies.append({
                "name": name,
                "value": value,
                "domain": clean_domain,
                "path": path,
                "secure": secure.lower() == "true",
                "expires": float(expiration) if expiration.isdigit() else -1
            })
    return cookies

def upload_to_youtube(channel_key, video_file, title, description):
    channel_key = channel_key.lower().strip()
    secret_name = CHANNELS_MAP.get(channel_key)

    if not secret_name:
        raise ValueError(f"اسم القناة غير مدعوم: {channel_key}. المتاح: abaad, masharee, masar")

    cookies_raw = os.getenv(secret_name, "").strip()
    if not cookies_raw:
        raise ValueError(f"لم يتم العثور على المتغير {secret_name} داخل GitHub Secrets!")

    if not os.path.exists(video_file):
        raise FileNotFoundError(f"ملف الفيديو غير موجود في المسار: {video_file}")

    print("=" * 60)
    print(f"🚀 بدء عملية الرفع إلى قناة: [{channel_key.upper()}]")
    print(f"📁 اسم الملف: {video_file}")
    print(f"📌 عنوان الفيديو: {title}")
    print("=" * 60)

    parsed_cookies = parse_netscape_cookies(cookies_raw)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        context.add_cookies(parsed_cookies)

        page = context.new_page()
        print("🌐 جاري فتح YouTube Studio...")
        page.goto("https://studio.youtube.com/channel/mine/videos/upload?d=ud", timeout=60000)
        time.sleep(7)

        # رفع الملف
        print("📤 جاري رفع ملف الفيديو...")
        file_input = page.locator('input[type="file"]')
        file_input.wait_for(state="attached", timeout=30000)
        file_input.set_input_files(video_file)

        # انتظار شاشة كتابة البيانات
        page.wait_for_selector("#textbox", timeout=45000)
        time.sleep(5)

        # كتابة العنوان والوصف
        print("✍️ إدخال العنوان والوصف...")
        title_boxes = page.locator("#textbox")
        title_boxes.nth(0).fill(title[:95])
        title_boxes.nth(1).fill(description)

        # غير مخصص للأطفال
        time.sleep(2)
        not_for_kids = page.locator('tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]')
        if not_for_kids.is_visible():
            not_for_kids.click()

        # الضغط على زر التالي للمرور عبر شاشات الإعدادات
        for step in range(1, 4):
            time.sleep(3)
            next_btn = page.locator("#next-button")
            if next_btn.is_visible():
                next_btn.click()
                print(f"➡ تخطي خطوة الإعدادات ({step}/3)...")

        # ضبط الفيديو على الوضع العام (Public)
        time.sleep(3)
        public_radio = page.locator('tp-yt-paper-radio-button[name="PUBLIC"]')
        if public_radio.is_visible():
            public_radio.click()
            print("👁️ تم تحديد حالة الفيديو: عام (Public)")

        # الضغط على زر النشر النهائي
        time.sleep(3)
        done_btn = page.locator("#done-button")
        if done_btn.is_visible():
            done_btn.click()
            print("✅ تم النقر على زر النشر بنجاح!")
            time.sleep(15)

        browser.close()
        print(f"🎉 اكتمل النشر على قناة [{channel_key.upper()}] بنجاح.")

if __name__ == "__main__":
    ch = sys.argv[1] if len(sys.argv) > 1 else "masar"
    vid = sys.argv[2] if len(sys.argv) > 2 else "video.mp4"
    t = sys.argv[3] if len(sys.argv) > 3 else "وثائقي استقصائي"
    d = sys.argv[4] if len(sys.argv) > 4 else "تحقيق وتحليل شامل."

    upload_to_youtube(ch, vid, t, d)
