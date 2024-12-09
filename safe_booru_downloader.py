import time
import requests
import json
from PIL import Image
from io import BytesIO
from tqdm import tqdm
from pathlib import Path


class SafebooruImageDownloader:
    def __init__(self, tags, save_dir, metadata_file, delay=2, max_images=500):
        self.save_dir = Path(save_dir).resolve()
        self.metadata_file = metadata_file
        self.tags = tags
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.delay = delay
        self.max_images = 500

    def fetch_safebooru_images(self, tags, limit=100, page=1):
        """Safebooru APIから画像情報を取得"""
        base_url = "https://safebooru.donmai.us/posts.json"
        params = {"tags": tags, "limit": limit, "page": page}
        response = requests.get(base_url, params=params)

        if response.status_code != 200:
            print(f"Failed to fetch data: {response.status_code}")
            return []
        return response.json()

    def download_image_as_jpeg(self, url, save_path, target_height=1024):
        """画像をダウンロードしてリサイズ、JPEG形式で保存"""
        try:
            response = requests.get(url)
            response.raise_for_status()  # エラーチェック
            image = Image.open(BytesIO(response.content))

            # アスペクト比を保持してリサイズ
            width, height = image.size
            target_width = int((target_height / height) * width)
            image_resized = image.resize((target_width, target_height), Image.LANCZOS)

            # JPEG形式で保存
            jpeg_path = save_path.with_suffix(".jpg")
            image_resized.convert("RGB").save(jpeg_path, "JPEG")
        except Exception as e:
            print(f"Error downloading {url}: {e}")

    def save_metadata(self, metadata, file_path):
        """メタデータをJSONファイルに保存"""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)

    def process_image(self, img):
        """画像をダウンロードしメタデータを更新"""
        file_url = img.get("file_url")
        if not file_url:
            return None

        file_name = Path(file_url).name
        save_path = self.save_dir / file_name

        # 画像ダウンロード・リサイズ
        self.download_image_as_jpeg(file_url, save_path)

        # メタデータ追加
        return {
            "id": img.get("id"),
            "file_name": save_path.with_suffix(".jpg").name,
            "artist": img.get("tag_string_artist", "Unknown"),
            "tags": img.get("tag_string"),
            "source": img.get("source", "N/A"),
            "url": f"https://safebooru.donmai.us/posts/{img.get('id')}"
        }

    def download_safebooru_images(self, tags="", max_images=500):
        """Safebooruから画像をダウンロード"""
        metadata = []
        downloaded_count = 0
        page = 1

        with tqdm(total=max_images, desc="Downloading images") as pbar:
            while downloaded_count < max_images:
                images = self.fetch_safebooru_images(tags=tags, page=page)
                if not images:
                    print("No more images to fetch.")
                    break

                for img in images:
                    if downloaded_count >= max_images:
                        break

                    img_metadata = self.process_image(img)
                    if img_metadata:
                        metadata.append(img_metadata)
                        downloaded_count += 1
                        pbar.update(1)

                    time.sleep(self.delay)  # 指定秒数待機
                page += 1

        self.save_metadata(metadata, self.metadata_file)

    def __call__(self, tags, max_images, delay=3):
        self.download_safebooru_images(tags, max_images)
