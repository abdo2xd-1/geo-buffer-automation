name: Produce and Upload Documentaries

on:
  workflow_dispatch:
  schedule:
    - cron: '0 17 * * *' # يعمل يومياً الساعة 7 مساءً بتوقيت مصر

jobs:
  build_and_upload:
    runs-on: ubuntu-latest
    timeout-minutes: 360

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install System Dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y ffmpeg fonts-noto-core fonts-noto-cjk

      - name: Install Python Dependencies & Playwright Browser
        run: |
          pip install -r requirements.txt
          playwright install chromium --with-deps

      # 1. إنتاج ونشر وثائقي قناة أبعاد جغرافية
      - name: Upload to أبعاد جغرافية
        env:
          COOKIES_ABAAD: ${{ secrets.COOKIES_ABAAD }}
        run: |
          python cookie_uploader.py abaad documentary_abaad.mp4 "أبعاد جغرافية: الممرات العالمية والتجارة" "تحقيق شامل يكشف أسرار المضائق والممرات الاستراتيجية. #أبعاد_جغرافية"

      # 2. إنتاج ونشر وثائقي قناة مشاريع عملاقة
      - name: Upload to مشاريع عملاقة
        env:
          COOKIES_MASHAREE: ${{ secrets.COOKIES_MASHAREE }}
        run: |
          python cookie_uploader.py masharee documentary_masharee.mp4 "مشاريع عملاقة: أضخم الإنشاءات الهندسية" "وثائقي هندسي يستعرض تفاصيل المشاريع الأكثر تعقيداً في العالم. #مشاريع_عملاقة"

      # 3. إنتاج ونشر وثائقي قناة مسار
      - name: Upload to مسار
        env:
          COOKIES_MASAR: ${{ secrets.COOKIES_MASAR }}
        run: |
          python cookie_uploader.py masar documentary_masar.mp4 "مسار: خفايا صعود القوى الاقتصادية" "وثائقي تحليلي استقصائي يسلط الضوء على خطوط الإمداد ومستقبل الاقتصاد. #مسار"
