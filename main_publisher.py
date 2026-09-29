name: Daily Shorts Publisher (Stock Videos & Gabriel Emad Style)

on:
  schedule:
    - cron: '0 11,17 * * *' # ينشر تلقائياً مرتين يومياً (1 ظهراً و 7 مساءً بتوقيت مصر)
  workflow_dispatch: # للنشر الفوري بضغطة زر

jobs:
  publish_shorts:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
          cache: 'pip'

      - name: Install System Dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y ffmpeg fonts-noto-core fonts-noto-extra libraqm-dev

      - name: Install Python Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run Shorts Publisher
        env:
          BUFFER_ACCESS_TOKEN: ${{ secrets.BUFFER_ACCESS_TOKEN }}
          BUFFER_CHANNEL_IDS: ${{ secrets.BUFFER_CHANNEL_IDS }}
          PEXELS_API_KEY: ${{ secrets.PEXELS_API_KEY }}
        run: python main_publisher.py
