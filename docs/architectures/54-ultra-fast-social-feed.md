# 54. Architecture: Ultra-Fast Social Feed

## Overview

High-performance social feed architecture with a distributed feed service, vector embeddings for personalization, real-time ranking, CDN-accelerated media delivery, and fast push notifications.

## Components

### Distributed Feed Service
- **Fan-Out on Write**: Pre-compute feeds for active users on content creation.
- **Fan-Out on Read**: Compute feeds on demand for less active users.
- **Hybrid Approach**: Fan-out on write for users with < 10K followers, on read for celebrities.
- **Feed Cache**: Redis-backed sorted sets for fast feed retrieval.
- **Pagination**: Cursor-based pagination with consistent ordering.

### Vector Embeddings for Personalization
- **User Embedding**: 128-dim vector capturing user interests and behavior.
- **Content Embedding**: 128-dim vector capturing post topics, media type, creator.
- **Embedding Model**: Two-tower neural network trained on interaction data.
- **Similarity**: Cosine similarity between user and content embeddings.
- **Real-Time Update**: User embedding updated with each interaction.

### Real-Time Ranking
- **Multi-Signal Scoring**: Recency + Engagement + Relevance + Creator affinity.
- **Online Re-Ranking**: Feed re-ranked on each request with latest signals.
- **Diversity**: De-duplication of similar content, source diversity.
- **Freshness Boost**: New content prioritized with time-decay function.
- **A/B Testing**: Continuous experimentation on ranking algorithms.

### CDN for Media
- **Image Optimization**: WebP/AVIF conversion, responsive sizes.
- **Video Streaming**: Adaptive bitrate streaming (HLS/DASH).
- **Edge Caching**: Media cached at 200+ edge locations globally.
- **Lazy Loading**: Below-fold media loaded on scroll.
- **Prefetch**: Next-page media prefetched for smooth scrolling.

### Fast Push Notifications
- **Real-Time Push**: WebSocket for in-app, APNs/FCM for background.
- **Batching**: Aggregate notifications for busy feeds (e.g., "10 new posts").
- **Priority**: Mentions and direct interactions at high priority.
- **Quiet Hours**: Respect user notification preferences.
- **Delivery Tracking**: Track push delivery and open rates.

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                   Content Creation                        │
│  Post Created ──▶ Fan-Out Service ──▶ Feed Cache (Redis) │
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────────────┼───────────────────────────────┐
│                    Feed Request                           │
│  ┌──────────┐    ┌───────┴──────┐    ┌──────────┐       │
│  │  Client  │───▶│  Feed API    │───▶│Feed Cache│       │
│  └──────────┘    └───────┬──────┘    └──────────┘       │
│                          │                               │
│                 ┌────────┼────────┐                      │
│                 ▼        ▼        ▼                      │
│          ┌──────────┐ ┌────────┐ ┌──────────┐           │
│          │Embedding │ │Ranking │ │Diversity │           │
│          │  Lookup  │ │Service │ │ Filter   │           │
│          └──────────┘ └────────┘ └──────────┘           │
│                          │                               │
│                          ▼                               │
│                   Ranked Feed                            │
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────────────┼───────────────────────────────┐
│                    Media Delivery                         │
│  ┌──────────┐    ┌──────┴──────┐    ┌──────────┐        │
│  │  Client  │◀───│    CDN      │◀───│  Origin  │        │
│  └──────────┘    │ (200+ Edge) │    │  Storage │        │
│                  └─────────────┘    └──────────┘        │
└──────────────────────────────────────────────────────────┘
```

## Performance Targets

| Metric | Target |
|--------|--------|
| Feed load (p50) | < 100ms |
| Feed load (p99) | < 300ms |
| Ranking computation | < 30ms |
| Media first byte (CDN) | < 50ms |
| Push notification | < 1 second |
| Feed freshness | < 30 seconds |
