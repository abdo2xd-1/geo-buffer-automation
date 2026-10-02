import os
import re
import sys
import time
from playwright.sync_api import sync_playwright

CHANNELS_MAP = {
    "abaad": "COOKIES_ABAAD",
    "masharee": "COOKIES_MASHAREE",
    "masar": "COOKIES_MASAR"
}

def parse_netscape_cookies(cookies_text):
    """تحويل الكوكيز مع الحفاظ على نطاق .youtube.com ليعمل مع studio.youtube.com"""
    cookies = []
    for line in cookies_text.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # دعم الفصل بعلامة Tab أو المسافات
        parts = line.split("\t")
        if len(parts) < 7:
            parts = re.split(r'\s+', line, maxsplit=6)

        if len(parts) >= 7:
            domain, flag, path, secure, expiration, name, value = parts[:7]
            domain_val = domain.strip()
            # الحفاظ على النقطة في بداية الدومين لتشمل النطاقات الفرعية
            if not domain_val.startswith("."):
                domain_val = "." + domain_val

            cookie_dict = {
                "name": name.strip(),
                "value": value.strip(),
                "domain": domain_val,
                "path": path.strip() if path.strip() else "/",
                "secure": secure.strip().lower() == "true",
            }
            if expiration.strip().isdigit() and float(expiration.strip()) > 0:
                cookie_dict["expires"] = float(expiration.strip())

            cookies.append(cookie_dict)
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
    print(f"🚀 بدء عملية الرفع لقناة: [{channel_key.upper()}]")
    print(f"📁 اسم الملف: {video_file}")
    print(f"📌 عنوان الفيديو: {title}")
    print("=" * 60)

    parsed_cookies = parse_netscape_cookies(cookies_raw)
    print(f"🍪 تم تجهيز {len(parsed_cookies)} كوكي لتوثيق الجلسة.")

    with sync_playwright() as p:
        # تشغيل المتصفح مع إخفاء سمات الأتمتة
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage"
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            locale="ar-EG"
        )
        # إخفاء خاصية webdriver عن نظام الحماية
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        context.add_cookies(parsed_cookies)

        page = context.new_page()
        print("🌐 جاري فتح YouTube Studio...")
        page.goto("https://studio.youtube.com", timeout=60000, wait_until="domcontentloaded")
        time.sleep(6)

        print(f"📍 عنوان الصفحة الحالي: [{page.title()}]")
        print(f"🔗 الرابط الحالي: [{page.url}]")

        # التحقق من تسجيل الدخول
        if "accounts.google.com" in page.url or "signin" in page.url:
            print("❌ تنبيه: لم يتم قبول الجلسة، تم التحويل لصفحة تسجيل الدخول.")
            browser.close()
            sys.exit(1)

        # فتح نافذة التحميل بالضغط على زر إنشاء (Create) أو بالرابط المباشر
        create_btn = page.locator('#create-icon, button[aria-label="Create"], button[aria-label="إنشاء"], ytcp-button-shape#create-icon')
        if create_btn.first.is_visible(timeout=5000):
            print("🔘 الضغط على زر إنشاء...")
            create_btn.first.click()
            time.sleep(2)
            upload_item = page.locator('#text-item-0, tp-yt-paper-item:has-text("Upload videos"), tp-yt-paper-item:has-text("تحميل فيديوهات")')
            if upload_item.first.is_visible(timeout=3000):
                upload_item.first.click()
                time.sleep(3)
        else:
            print("🔄 الانتقال المباشر لنافذة التحميل...")
            page.goto("https://studio.youtube.com/channel/mine/videos/upload?d=ud", timeout=60000)
            time.sleep(6)

        # رفع ملف الفيديو
        print("📤 سحب وإفلات ملف الفيديو في المتصفح...")
        file_input = page.locator('input[type="file"]')
        file_input.wait_for(state="attached", timeout=60000)
        file_input.set_input_files(video_file)

        # ملء العنوان والوصف
        print("✍️ كتابة العنوان وتفاصيل الفيديو...")
        page.wait_for_selector("#textbox", timeout=60000)
        time.sleep(4)

        title_box = page.locator("#textbox").nth(0)
        title_box.click()
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        title_box.fill(title[:95])

        desc_box = page.locator("#textbox").nth(1)
        desc_box.click()
        desc_box.fill(description)

        # تحديد غير مخصص للأطفال
        time.sleep(2)
        not_for_kids = page.locator('tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"], [name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]')
        if not_for_kids.first.is_visible():
            not_for_kids.first.click()

        # تجاوز خطوات الإعدادات (التالي)
        for step in range(1, 4):
            time.sleep(3)
            next_btn = page.locator("#next-button")
            if next_btn.first.is_visible():
                next_btn.first.click()
                print(f"➡ المتابعة عبر خطوات التحقق ({step}/3)...")

        # ضبط الفيديو كـ عام (Public)
        time.sleep(3)
        public_radio = page.locator('tp-yt-paper-radio-button[name="PUBLIC"], [name="PUBLIC"]')
        if public_radio.first.is_visible():
            public_radio.first.click()
            print("👁️ تم ضبط الرؤية: عام (Public)")

        # الضغط على زر النشر
        time.sleep(3)
        done_btn = page.locator("#done-button")
        if done_btn.first.is_visible():
            done_btn.first.click()
            print("✅ تم النقر على زر النشر بنجاح!")
            time.sleep(20)

        browser.close()
        print(f"🎉 تم نشر الفيديو بنجاح تام على قناة [{channel_key.upper()}].")

if __name__ == "__main__":
    ch = sys.argv[1] if len(sys.argv) > 1 else "masar"
    vid = sys.argv[2] if len(sys.argv) > 2 else "video.mp4"
    t = sys.argv[3] if len(sys.argv) > 3 else "وثائقي استقصائي جديد"
    d = sys.argv[4] if len(sys.argv) > 4 else "تحقيق وثائقي شامل يكشف الحقائق والتفاصيل."

    upload_to_youtube(ch, vid, t, d)
