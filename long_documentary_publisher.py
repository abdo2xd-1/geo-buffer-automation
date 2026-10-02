name: Produce and Upload Documentaries

on:
  workflow_dispatch:
  schedule:
    - cron: '0 17 * * *'

jobs:
  run_pipeline:
    runs-on: ubuntu-latest
    timeout-minutes: 360

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install System Packages
        run: |
          sudo apt-get update
          sudo apt-get install -y ffmpeg fonts-noto-core fonts-noto-cjk

      - name: Install Python Libraries & Playwright
        run: |
          pip install requests edge-tts playwright
          playwright install chromium --with-deps

      # إنتاج ورندر الفيديو لقناة مسار
      - name: Produce Documentary - Masar
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          PEXELS_API_KEY: ${{ secrets.PEXELS_API_KEY }}
        run: |
          python long_documentary_publisher.py --channel masar

      # رفع الفيديو الناتج مباشرة إلى قناة مسار عبر الكوكيز
      - name: Upload to YouTube - Masar
        env:
          COOKIES_MASAR: ${{ secrets.COOKIES_MASAR }}
        run: |
          python cookie_uploader.py masar documentary_masar.mp4 "مسار: خطوط التجارة ومستقبل الاقتصاد الدولي" "وثائقي تحليلي استقصائي يسلط الضوء على خطوط الإمداد العالمية ومستقبل التجارة الدولية. #مسار"
