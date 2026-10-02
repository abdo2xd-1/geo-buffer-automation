- name: Produce 30-Min Documentary
        timeout-minutes: 360
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          PEXELS_API_KEY: ${{ secrets.PEXELS_API_KEY }}
        run: |
          python long_documentary_publisher.py

      - name: Install Google API Client
        run: |
          pip install google-api-python-client google-auth-oauthlib google-auth-httplib2

      - name: Auto-Upload Directly to YouTube
        env:
          YOUTUBE_CLIENT_ID: ${{ secrets.YOUTUBE_CLIENT_ID }}
          YOUTUBE_CLIENT_SECRET: ${{ secrets.YOUTUBE_CLIENT_SECRET }}
          YOUTUBE_REFRESH_TOKEN: ${{ secrets.YOUTUBE_REFRESH_TOKEN }}
        run: |
          python youtube_uploader.py documentary_30min.mp4
