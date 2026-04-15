"""
Algorithm 98: Real-Time Bidding

- Ad request → auction
- Bidders submit price
- Fast winner selection
- Ad delivered
- Logged for analytics
"""

import time
import random
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class AdRequest:
    """An ad placement request."""
    request_id: str
    user_id: str
    page_url: str
    ad_slot: str
    user_segments: list = field(default_factory=list)
    geo: str = ""
    device: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class Bid:
    """A bid from an advertiser."""
    bid_id: str
    bidder_id: str
    request_id: str
    price_cpm: float  # cost per mille (1000 impressions)
    ad_creative_id: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class AuctionResult:
    """Result of an ad auction."""
    request_id: str
    winner_bid: Bid
    clearing_price: float  # second-price
    all_bids: list
    auction_time_ms: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class AdDelivery:
    """Record of ad delivery."""
    request_id: str
    bidder_id: str
    ad_creative_id: str
    price_cpm: float
    delivered_at: float = field(default_factory=time.time)


class Bidder:
    """An ad bidder/advertiser."""

    def __init__(self, bidder_id, budget=1000.0, base_cpm=2.0):
        self.bidder_id = bidder_id
        self.budget = budget
        self.base_cpm = base_cpm
        self.spent = 0.0
        self.impressions = 0
        self.target_segments = set()

    def submit_bid(self, request):
        """Submit a bid for an ad request."""
        if self.budget - self.spent <= 0:
            return None

        # Calculate bid price based on targeting
        price = self.base_cpm

        # Boost for matching segments
        matching = len(self.target_segments & set(request.user_segments))
        if matching > 0:
            price *= 1 + matching * 0.3

        # Add some randomness for competition
        price *= random.uniform(0.8, 1.2)

        return Bid(
            bid_id=f"bid-{self.bidder_id}-{request.request_id}",
            bidder_id=self.bidder_id,
            request_id=request.request_id,
            price_cpm=round(price, 4),
            ad_creative_id=f"creative-{self.bidder_id}",
        )

    def charge(self, amount):
        """Charge the bidder for a won auction."""
        self.spent += amount
        self.impressions += 1


class AuctionEngine:
    """Real-time auction engine for ad bidding."""

    def __init__(self, auction_type="second_price"):
        self.auction_type = auction_type

    def run_auction(self, request, bids):
        """Run auction and select winner."""
        start = time.time()

        if not bids:
            return None

        # Sort bids by price (descending)
        sorted_bids = sorted(bids, key=lambda b: b.price_cpm, reverse=True)

        winner = sorted_bids[0]

        # Second-price auction: winner pays second-highest bid
        if self.auction_type == "second_price" and len(sorted_bids) > 1:
            clearing_price = sorted_bids[1].price_cpm
        else:
            clearing_price = winner.price_cpm

        elapsed_ms = (time.time() - start) * 1000

        return AuctionResult(
            request_id=request.request_id,
            winner_bid=winner,
            clearing_price=clearing_price,
            all_bids=sorted_bids,
            auction_time_ms=elapsed_ms,
        )


class RTBExchange:
    """Real-Time Bidding exchange."""

    def __init__(self, auction_type="second_price"):
        self.auction_engine = AuctionEngine(auction_type)
        self.bidders = {}
        self.delivery_log = []
        self.analytics = defaultdict(lambda: {
            "requests": 0, "impressions": 0, "revenue": 0.0,
        })

    def register_bidder(self, bidder):
        """Register a bidder in the exchange."""
        self.bidders[bidder.bidder_id] = bidder

    def process_request(self, request):
        """Process an ad request through the RTB pipeline."""
        self.analytics["total"]["requests"] += 1

        # Collect bids from all bidders
        bids = []
        for bidder in self.bidders.values():
            bid = bidder.submit_bid(request)
            if bid:
                bids.append(bid)

        if not bids:
            return None

        # Run auction
        result = self.auction_engine.run_auction(request, bids)
        if result is None:
            return None

        # Deliver ad
        delivery = self._deliver_ad(result)

        # Log for analytics
        self._log_analytics(result)

        return delivery

    def _deliver_ad(self, result):
        """Deliver the winning ad."""
        winner_bidder = self.bidders.get(result.winner_bid.bidder_id)
        if winner_bidder:
            winner_bidder.charge(result.clearing_price / 1000)  # CPM to per-impression

        delivery = AdDelivery(
            request_id=result.request_id,
            bidder_id=result.winner_bid.bidder_id,
            ad_creative_id=result.winner_bid.ad_creative_id,
            price_cpm=result.clearing_price,
        )
        self.delivery_log.append(delivery)
        return delivery

    def _log_analytics(self, result):
        """Log auction result for analytics."""
        self.analytics["total"]["impressions"] += 1
        self.analytics["total"]["revenue"] += result.clearing_price / 1000

        bidder_id = result.winner_bid.bidder_id
        self.analytics[bidder_id]["impressions"] += 1
        self.analytics[bidder_id]["revenue"] += result.clearing_price / 1000

    def get_analytics(self):
        """Get exchange analytics."""
        return dict(self.analytics)


if __name__ == "__main__":
    exchange = RTBExchange(auction_type="second_price")

    # Register bidders
    bidders = [
        Bidder("advertiser-A", budget=100, base_cpm=3.0),
        Bidder("advertiser-B", budget=200, base_cpm=2.5),
        Bidder("advertiser-C", budget=150, base_cpm=4.0),
    ]
    bidders[0].target_segments = {"tech", "gaming"}
    bidders[1].target_segments = {"sports", "fitness"}
    bidders[2].target_segments = {"tech", "premium"}

    for bidder in bidders:
        exchange.register_bidder(bidder)

    # Simulate ad requests
    for i in range(20):
        request = AdRequest(
            request_id=f"req-{i}",
            user_id=f"user-{i % 5}",
            page_url=f"https://example.com/page-{i}",
            ad_slot="banner-top",
            user_segments=random.sample(["tech", "sports", "gaming", "premium", "fitness"], 2),
        )
        delivery = exchange.process_request(request)
        if delivery:
            print(f"Request {request.request_id}: winner={delivery.bidder_id}, "
                  f"price=${delivery.price_cpm:.2f} CPM")

    # Analytics
    analytics = exchange.get_analytics()
    print(f"\nTotal impressions: {analytics['total']['impressions']}")
    print(f"Total revenue: ${analytics['total']['revenue']:.2f}")
