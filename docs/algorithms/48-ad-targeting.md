# 48. Algorithm: Ad Targeting

## Overview

Precision ad targeting algorithm using user profile vectors, ad embedding vectors, cosine similarity scoring, real-time bidding, and fast ad delivery.

## Algorithm Steps

### Step 1: User Profile Vector
- User features aggregated: demographics, interests, browsing history, purchase history.
- Features encoded into dense embedding vector (128-256 dimensions).
- Updated in real-time as user interacts with content.
- Privacy-compliant: anonymized and consent-managed.
- Stored in feature store for fast retrieval.

### Step 2: Ad Embedding Vector
- Ad features encoded: category, keywords, creative type, target audience.
- Same embedding space as user vectors for direct comparison.
- Ad vectors pre-computed and indexed for fast retrieval.
- Refreshed when ad content or targeting criteria change.
- Multiple vectors per ad for different targeting dimensions.

### Step 3: Cosine Similarity Scoring
```
similarity(user, ad) = (user · ad) / (||user|| × ||ad||)
```
- Score ranges from -1 (opposite) to 1 (identical).
- Threshold: ads with similarity > 0.5 considered relevant.
- Top-K candidates selected for bidding phase.
- Efficient computation via SIMD vectorized operations.
- Batch scoring for multiple ads simultaneously.

### Step 4: Real-Time Bidding System
- Relevant ads enter real-time auction.
- Advertisers set maximum bid price per impression/click.
- Second-price auction: winner pays second-highest bid + $0.01.
- Quality score factored in: bid × quality_score = ad_rank.
- Auction completes in < 10ms.

### Step 5: Fast Delivery via Ad Service
- Winning ad delivered to client in the same request cycle.
- Ad creative pre-cached at CDN edge nodes.
- Impression tracked asynchronously.
- Click tracking via redirect URL.
- Conversion tracking via pixel or server-to-server callback.

## Pseudocode

```
function targetAd(user_id, ad_slot, context):
    // Step 1: Get user vector
    user_vector = featureStore.getUserVector(user_id)
    
    // Step 2: Get candidate ads
    eligible_ads = adService.getEligibleAds(ad_slot, context)
    
    // Step 3: Score with cosine similarity
    scored_ads = []
    for ad in eligible_ads:
        similarity = cosineSimilarity(user_vector, ad.embedding)
        if similarity > RELEVANCE_THRESHOLD:
            scored_ads.append({ad, similarity})
    
    // Sort and take top-K for auction
    candidates = topK(scored_ads, K=10)
    
    // Step 4: Real-time bidding
    bids = []
    for candidate in candidates:
        bid = biddingService.getBid(candidate.ad.advertiser_id, ad_slot)
        quality_score = candidate.similarity * candidate.ad.ctr_estimate
        ad_rank = bid.amount * quality_score
        bids.append({candidate.ad, bid, ad_rank})
    
    // Second-price auction
    sorted_bids = sortByAdRank(bids, descending=True)
    winner = sorted_bids[0]
    winner.price = sorted_bids[1].ad_rank / winner.quality_score + 0.01
    
    // Step 5: Deliver
    ad_response = adService.getCreative(winner.ad.id)
    
    // Async tracking
    async:
        trackImpression(user_id, winner.ad.id, ad_slot, winner.price)
    
    return ad_response
```

## Performance Targets

| Metric | Target |
|--------|--------|
| User vector lookup | < 2ms |
| Similarity scoring (1K ads) | < 5ms |
| Auction execution | < 10ms |
| End-to-end ad selection | < 30ms |
| Ad delivery (CDN) | < 50ms |
