"""
Algorithm 83: Media Compression

- Input → compression service
- Codec selection (Opus/H.265)
- Fast transcoding
- Stored in CDN
- Adaptive playback
"""

import time
import hashlib
from dataclasses import dataclass, field
from enum import Enum


class MediaType(Enum):
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"


class AudioCodec(Enum):
    OPUS = "opus"
    AAC = "aac"
    MP3 = "mp3"


class VideoCodec(Enum):
    H265 = "h265"
    H264 = "h264"
    VP9 = "vp9"
    AV1 = "av1"


class ImageFormat(Enum):
    WEBP = "webp"
    JPEG = "jpeg"
    AVIF = "avif"


@dataclass
class CompressionResult:
    """Result of media compression."""
    media_id: str
    original_size: int
    compressed_size: int
    codec: str
    compression_ratio: float
    cdn_url: str
    variants: list = field(default_factory=list)
    transcode_time: float = 0.0


@dataclass
class PlaybackVariant:
    """A playback variant for adaptive streaming."""
    bitrate: int  # kbps
    resolution: str
    codec: str
    url: str


class CodecSelector:
    """Select optimal codec based on media type and constraints."""

    def select_audio_codec(self, duration_seconds, target_quality="high"):
        """Select audio codec based on constraints."""
        if target_quality == "high" and duration_seconds < 300:
            return AudioCodec.OPUS
        elif target_quality == "medium":
            return AudioCodec.AAC
        else:
            return AudioCodec.OPUS  # Opus is generally best

    def select_video_codec(self, resolution, target_quality="high"):
        """Select video codec based on resolution and quality."""
        height = int(resolution.split("x")[-1]) if "x" in resolution else 720

        if height >= 1080 and target_quality == "high":
            return VideoCodec.H265
        elif height >= 720:
            return VideoCodec.H264
        else:
            return VideoCodec.VP9

    def select_image_format(self, has_transparency=False):
        """Select image format based on properties."""
        if has_transparency:
            return ImageFormat.WEBP
        return ImageFormat.WEBP  # WebP generally best for web


class Transcoder:
    """Simulated fast transcoding engine."""

    def transcode_audio(self, data, codec, bitrate=128):
        """Transcode audio to target codec."""
        start = time.time()

        original_size = len(data) if isinstance(data, bytes) else len(str(data))
        compression_map = {
            AudioCodec.OPUS: 0.15,
            AudioCodec.AAC: 0.20,
            AudioCodec.MP3: 0.25,
        }
        ratio = compression_map.get(codec, 0.20)
        compressed_size = int(original_size * ratio)

        return {
            "codec": codec.value,
            "original_size": original_size,
            "compressed_size": compressed_size,
            "bitrate": bitrate,
            "transcode_time": time.time() - start,
        }

    def transcode_video(self, data, codec, resolution="1920x1080", bitrate=5000):
        """Transcode video to target codec."""
        start = time.time()

        original_size = len(data) if isinstance(data, bytes) else len(str(data))
        compression_map = {
            VideoCodec.H265: 0.10,
            VideoCodec.H264: 0.15,
            VideoCodec.VP9: 0.12,
            VideoCodec.AV1: 0.08,
        }
        ratio = compression_map.get(codec, 0.15)
        compressed_size = int(original_size * ratio)

        return {
            "codec": codec.value,
            "resolution": resolution,
            "original_size": original_size,
            "compressed_size": compressed_size,
            "bitrate": bitrate,
            "transcode_time": time.time() - start,
        }

    def generate_variants(self, data, codec_type="video"):
        """Generate multiple quality variants for adaptive playback."""
        variants = []
        if codec_type == "video":
            configs = [
                {"resolution": "1920x1080", "bitrate": 5000, "codec": VideoCodec.H265},
                {"resolution": "1280x720", "bitrate": 2500, "codec": VideoCodec.H264},
                {"resolution": "854x480", "bitrate": 1000, "codec": VideoCodec.H264},
                {"resolution": "640x360", "bitrate": 500, "codec": VideoCodec.H264},
            ]
            for config in configs:
                result = self.transcode_video(
                    data, config["codec"],
                    config["resolution"], config["bitrate"]
                )
                variants.append(PlaybackVariant(
                    bitrate=config["bitrate"],
                    resolution=config["resolution"],
                    codec=config["codec"].value,
                    url=f"/cdn/video/{config['resolution']}_{config['bitrate']}",
                ))
        return variants


class CDNStorage:
    """Simulated CDN storage."""

    def __init__(self, base_url="https://cdn.example.com"):
        self.base_url = base_url
        self.stored_media = {}

    def store(self, media_id, data, content_type):
        """Store compressed media in CDN."""
        url = f"{self.base_url}/{content_type}/{media_id}"
        self.stored_media[media_id] = {
            "url": url,
            "size": len(data) if isinstance(data, bytes) else len(str(data)),
            "content_type": content_type,
            "stored_at": time.time(),
        }
        return url


class MediaCompressionService:
    """Complete media compression service."""

    def __init__(self):
        self.codec_selector = CodecSelector()
        self.transcoder = Transcoder()
        self.cdn = CDNStorage()

    def compress(self, media_id, data, media_type, **kwargs):
        """Compress media and store in CDN."""
        start = time.time()

        if media_type == MediaType.AUDIO:
            codec = self.codec_selector.select_audio_codec(
                kwargs.get("duration", 60),
                kwargs.get("quality", "high"),
            )
            result = self.transcoder.transcode_audio(
                data, codec, kwargs.get("bitrate", 128)
            )
        elif media_type == MediaType.VIDEO:
            codec = self.codec_selector.select_video_codec(
                kwargs.get("resolution", "1920x1080"),
                kwargs.get("quality", "high"),
            )
            result = self.transcoder.transcode_video(
                data, codec,
                kwargs.get("resolution", "1920x1080"),
                kwargs.get("bitrate", 5000),
            )
        else:
            result = {
                "codec": "webp",
                "original_size": len(data) if isinstance(data, bytes) else len(str(data)),
                "compressed_size": int((len(data) if isinstance(data, bytes) else len(str(data))) * 0.3),
                "transcode_time": 0,
            }

        cdn_url = self.cdn.store(media_id, data, media_type.value)

        variants = []
        if media_type == MediaType.VIDEO:
            variants = self.transcoder.generate_variants(data)

        original_size = result["original_size"]
        compressed_size = result["compressed_size"]
        return CompressionResult(
            media_id=media_id,
            original_size=original_size,
            compressed_size=compressed_size,
            codec=result["codec"],
            compression_ratio=compressed_size / max(original_size, 1),
            cdn_url=cdn_url,
            variants=variants,
            transcode_time=time.time() - start,
        )


if __name__ == "__main__":
    service = MediaCompressionService()

    # Compress audio
    audio_data = b"x" * 1_000_000
    audio_result = service.compress("audio1", audio_data, MediaType.AUDIO, duration=120)
    print(f"Audio: {audio_result.original_size} → {audio_result.compressed_size} "
          f"({audio_result.compression_ratio:.1%} ratio, codec={audio_result.codec})")

    # Compress video
    video_data = b"x" * 10_000_000
    video_result = service.compress("video1", video_data, MediaType.VIDEO, resolution="1920x1080")
    print(f"Video: {video_result.original_size} → {video_result.compressed_size} "
          f"({video_result.compression_ratio:.1%} ratio, codec={video_result.codec})")
    print(f"  Variants: {len(video_result.variants)}")
    for v in video_result.variants:
        print(f"    {v.resolution} @ {v.bitrate}kbps ({v.codec})")
