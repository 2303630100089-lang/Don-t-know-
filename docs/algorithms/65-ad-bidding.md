# 65. Algorithm: Ad Bidding

## Overview

Real-time ad bidding algorithm that receives ad requests, collects advertiser bids, runs a fast auction, selects winners, and delivers ads instantly.

## Algorithm Steps

### Step 1: Ad Request → Bidding System
- User loads a page or content with ad placement.
- Ad request includes: user_id, placement_id, context (page content, device).
- Bidding system receives request with strict latency budget (< 100ms total).
- User profile and targeting data fetched in parallel.

### Step 2: Advertisers Submit Bids
- Eligible advertisers identified based on targeting criteria.
- Bid requests sent to DSPs (Demand-Side Platforms) in parallel.
- Each DSP returns: bid price, creative_id, advertiser_id.
- Timeout: bids not received within 50ms are excluded.
- Floor price enforced: bids below minimum are rejected.

### Step 3: Fast Auction Algorithm
- **Second-Price Auction (Vickrey)**: Winner pays second-highest bid + $0.01.
- **Generalized Second Price (GSP)**: For multiple ad slots.
- Ad rank = bid × quality_score (CTR prediction × relevance).
- Quality score prevents low-quality ads from winning with high bids.
- Auction computation: O(N log N) for N bidders with sorting.

### Step 4: Winner Selected
- Highest ad_rank bidder wins the placement.
- Clearing price calculated: second-highest ad_rank / winner's quality_score + minimum increment.
- Winner's creative retrieved and prepared for delivery.
- Losing bidders notified for analytics.
- Auction result logged for billing and reporting.

### Step 5: Ad Delivered Instantly
- Winning creative URL returned in ad response.
- Creative served from CDN for fast loading.
- Impression pixel tracked asynchronously.
- Viewability tracking via Intersection Observer API.
- Click tracking via redirect or beacon.

## Pseudocode

```
function handleAdRequest(request):
    // Step 1: Parse request
    user_profile = fetchUserProfile(request.user_id)
    placement = getPlacement(request.placement_id)
    
    // Step 2: Collect bids (parallel, with timeout)
    eligible_dsps = getEligibleDSPs(user_profile, placement)
    
    bid_request = {
        user: anonymize(user_profile),
        placement: placement,
        floor_price: placement.floor_price,
        timeout: 50ms
    }
    
    bids = parallelWithTimeout(
        [dsp.requestBid(bid_request) for dsp in eligible_dsps],
        timeout=50ms
    )
    
    // Filter valid bids
    valid_bids = filter(b => b.price >= placement.floor_price, bids)
    
    if valid_bids.isEmpty():
        return serveFallbackAd(placement)
    
    // Step 3: Auction
    for bid in valid_bids:
        bid.quality_score = predictCTR(user_profile, bid.creative) * 
                            computeRelevance(user_profile, bid.targeting)
        bid.ad_rank = bid.price * bid.quality_score
    
    sorted_bids = sortByAdRank(valid_bids, descending=True)
    
    // Step 4: Winner selection
    winner = sorted_bids[0]
    
    if sorted_bids.length > 1:
        second_price = sorted_bids[1].ad_rank / winner.quality_score + 0.01
    else:
        second_price = placement.floor_price
    
    winner.clearing_price = max(second_price, placement.floor_price)
    
    // Log auction
    logAuction({
        placement_id: placement.id,
        winner: winner,
        bids: sorted_bids,
        clearing_price: winner.clearing_price
    })
    
    // Step 5: Deliver
    creative = getCreativeFromCDN(winner.creative_id)
    
    return {
        creative_url: creative.url,
        impression_url: generateImpressionPixel(winner),
        click_url: generateClickTracker(winner)
    }
```

## Performance Targets

| Metric | Target |
|--------|--------|
| End-to-end auction | < 100ms |
| Bid collection | < 50ms |
| Auction computation | < 5ms |
| Ad creative load | < 200ms |
| Fill rate | > 90% |
