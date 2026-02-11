import os
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

class SocialUploader:
    def __init__(self, config):
        self.config = config

    def upload_to_youtube(self, video_path, title, description, tags):
        # OAuth 2.0 setup
        scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        client_secrets_file = self.config.get('YOUTUBE_JSON_PATH')

        if not client_secrets_file or not os.path.exists(client_secrets_file):
            raise Exception("YouTube Client Secrets JSON nicht gefunden oder Pfad ungültig.")

        creds = None
        token_file = 'youtube_token.json'
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, scopes)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
                creds = flow.run_local_server(port=0)
            with open(token_file, 'w') as token:
                token.write(creds.to_json())

        youtube = build("youtube", "v3", credentials=creds)

        body = {
            "snippet": {
                "title": title[:100],
                "description": description,
                "tags": tags,
                "categoryId": "20" # Gaming
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Uploaded {int(status.progress() * 100)}%")

        return response.get('id')

    def upload_to_tiktok(self, video_path, description):
        # TikTok automation is tricky without official API access for individuals.
        # Often libraries like 'tiktok-uploader' use session cookies.
        # For this implementation, we will provide a placeholder or a basic structure.
        print(f"TikTok Upload (Placeholder) for {video_path} with desc: {description}")
        return "tiktok_upload_success_id"
