# 63. Algorithm: Video Transcoding

## Overview

GPU-accelerated video transcoding algorithm that processes uploaded videos into multiple resolutions, stores them in CDN, and enables fast adaptive streaming.

## Algorithm Steps

### Step 1: Upload → Transcoding Service
- Video uploaded via chunked multipart upload.
- Upload validated: format, size limits, content scan.
- Transcoding job created with priority based on user tier.
- Job enqueued in transcoding queue (priority queue).
- Original file stored in object storage as source.

### Step 2: GPU Acceleration
- Transcoding worker claims job from queue.
- GPU-accelerated encoding via NVIDIA NVENC / Intel QSV.
- Hardware decode → GPU processing → hardware encode pipeline.
- Parallel pipeline: decode and encode run simultaneously.
- Batch scheduling: multiple videos processed per GPU.

### Step 3: Multiple Resolutions Generated
- **Adaptive Bitrate Ladder**:
  - 240p: 400 kbps
  - 360p: 800 kbps
  - 480p: 1.5 Mbps
  - 720p: 3 Mbps
  - 1080p: 6 Mbps
  - 4K: 15 Mbps
- Codec: H.264 for compatibility, H.265/AV1 for efficiency.
- Thumbnail extraction at multiple timestamps.
- Audio normalized and encoded in AAC 128 kbps.

### Step 4: Stored in CDN
- Transcoded segments uploaded to object storage.
- HLS manifest (.m3u8) and DASH manifest (.mpd) generated.
- Segment duration: 6 seconds for balance of latency and caching.
- CDN populates content to edge nodes on first request.
- Pre-warming for anticipated popular content.

### Step 5: Fast Adaptive Streaming
- Client selects quality based on available bandwidth.
- Bandwidth estimation via segment download timing.
- Quality switches between segments (seamless transitions).
- Buffer management: maintain 10-30 seconds of buffered content.
- Start playback at lower quality for fast initial load.

## Pseudocode

```
function transcodeVideo(upload_id):
    source = objectStorage.get(upload_id)
    job_id = generateJobId()
    
    // Resolution ladder
    resolutions = [
        {height: 240,  bitrate: 400_000,  codec: "h264"},
        {height: 360,  bitrate: 800_000,  codec: "h264"},
        {height: 480,  bitrate: 1_500_000, codec: "h264"},
        {height: 720,  bitrate: 3_000_000, codec: "h264"},
        {height: 1080, bitrate: 6_000_000, codec: "h265"},
        {height: 2160, bitrate: 15_000_000, codec: "h265"}
    ]
    
    // Filter resolutions (don't upscale)
    source_height = getVideoHeight(source)
    resolutions = filter(r => r.height <= source_height, resolutions)
    
    // GPU-accelerated transcoding
    outputs = []
    parallel for res in resolutions:
        output = gpuTranscode(
            source,
            width=calculateWidth(source, res.height),
            height=res.height,
            bitrate=res.bitrate,
            codec=res.codec,
            segment_duration=6s,
            gpu_encoder=NVENC
        )
        outputs.append(output)
    
    // Generate thumbnails
    thumbnails = extractThumbnails(source, timestamps=[0s, 25%, 50%, 75%])
    
    // Generate streaming manifests
    hls_manifest = generateHLSManifest(outputs, segment_duration=6s)
    dash_manifest = generateDASHManifest(outputs, segment_duration=6s)
    
    // Upload to CDN-backed storage
    for output in outputs:
        objectStorage.putSegments(job_id, output.resolution, output.segments)
    
    objectStorage.put(f"{job_id}/master.m3u8", hls_manifest)
    objectStorage.put(f"{job_id}/manifest.mpd", dash_manifest)
    objectStorage.put(f"{job_id}/thumbnails/", thumbnails)
    
    // Update metadata
    db.updateVideo(upload_id, {
        status: READY,
        manifest_url: f"https://cdn.example.com/{job_id}/master.m3u8",
        resolutions: outputs.map(o => o.resolution),
        duration: source.duration
    })
```

## Performance Targets

| Metric | Target |
|--------|--------|
| 1 min video transcoding | < 30 seconds |
| 10 min video transcoding | < 3 minutes |
| Playback start time | < 1 second |
| Quality switch time | < 1 segment (6s) |
| CDN cache hit rate | > 95% |
