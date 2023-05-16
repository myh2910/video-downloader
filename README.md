# video-downloader

Download videos from the internet.

## Requirements

- `pip install -r requirements.txt`
- Install [FFmpeg](https://ffmpeg.org/).

## Usage

```python
from video_downloader import download_video

if __name__ == "__main__":
    download_video(
        "글래디에이터",
        "https://lqap.vizcloud.ink/simple/EqPFJvgQWADtjDlGha7rC5Au+Vxe+bawA0Z7rqk+wYMnU94US2El/br/H4/v.m3u8",
        subtitle=("https://s1.bunnycdn.ru/sub/cache2/subtitle/9755141.vtt", "vtt")
    )
```

```python
from video_downloader import download_video

if __name__ == "__main__":
    download_video(
        "이상한 변호사 우영우 1화",
        "https://manifest.prod.boltdns.net/manifest/v1/hls/v4/clear/6310593120001/1e516fa1-0474-4edf-9acf-729277180608/390375ec-c9f0-47ab-916f-cd9807a2be83/6s/rendition.m3u8?fastly_token=NjJkOWM1ZDhfNTRhNDE1ODA5MDhlNGYwYjA2ZWMxNmEyMmU3NGRmMTU1NjZiZmU5ODZmMzNhZmQyMWFmN2UzYmU3ZjI5MGZhNw%3D%3D",
        audio_url="https://manifest.prod.boltdns.net/manifest/v1/hls/v4/clear/6310593120001/1e516fa1-0474-4edf-9acf-729277180608/42662b38-ffb5-4b4e-917b-1a1da319ce17/6s/rendition.m3u8?fastly_token=NjJkOWM1ZDhfMTJkOGE1ZGRkMDAzMTVmYzAxZmE4OWIwZGIzNDU1YWFkNjE2NmQ2MjQxMTY4YTBhMDNjMzUxNGM4ODM4NTRmNw%3D%3D"
    )
```
