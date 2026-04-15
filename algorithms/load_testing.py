"""
Algorithm 92: Load Testing

- Synthetic traffic generated
- Fast stress simulation
- Metrics collected
- Bottlenecks identified
- Scaling plan updated
"""

import time
import random
import statistics
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class RequestType(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


@dataclass
class LoadTestRequest:
    """A simulated request for load testing."""
    request_id: int
    endpoint: str
    method: RequestType
    timestamp: float = field(default_factory=time.time)
    response_time_ms: float = 0.0
    status_code: int = 200
    success: bool = True


@dataclass
class LoadTestMetrics:
    """Aggregated load test metrics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time_ms: float = 0.0
    p50_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    max_response_time_ms: float = 0.0
    min_response_time_ms: float = 0.0
    requests_per_second: float = 0.0
    error_rate: float = 0.0
    bottlenecks: list = field(default_factory=list)


class TrafficGenerator:
    """Generate synthetic traffic patterns."""

    def __init__(self, endpoints=None):
        self.endpoints = endpoints or [
            ("/api/users", RequestType.GET, 0.4),
            ("/api/users", RequestType.POST, 0.1),
            ("/api/posts", RequestType.GET, 0.3),
            ("/api/posts", RequestType.POST, 0.1),
            ("/api/search", RequestType.GET, 0.1),
        ]

    def generate_request(self, request_id):
        """Generate a single synthetic request."""
        rand = random.random()
        cumulative = 0.0
        endpoint = self.endpoints[0]

        for ep in self.endpoints:
            cumulative += ep[2]
            if rand <= cumulative:
                endpoint = ep
                break

        return LoadTestRequest(
            request_id=request_id,
            endpoint=endpoint[0],
            method=endpoint[1],
        )

    def generate_batch(self, count, start_id=0):
        """Generate a batch of requests."""
        return [self.generate_request(start_id + i) for i in range(count)]


class ServiceSimulator:
    """Simulate a service under load."""

    def __init__(self, base_latency_ms=10, max_capacity=100):
        self.base_latency_ms = base_latency_ms
        self.max_capacity = max_capacity
        self.current_load = 0
        self.error_threshold = 0.8  # 80% capacity triggers errors

    def handle_request(self, request):
        """Simulate handling a request."""
        self.current_load += 1

        load_factor = self.current_load / self.max_capacity
        latency = self.base_latency_ms * (1 + load_factor ** 2 * 10)

        latency += random.gauss(0, self.base_latency_ms * 0.2)
        latency = max(1.0, latency)

        request.response_time_ms = latency

        if load_factor > self.error_threshold:
            error_prob = (load_factor - self.error_threshold) / (1 - self.error_threshold)
            if random.random() < error_prob:
                request.status_code = 503
                request.success = False
        elif random.random() < 0.01:  # 1% baseline error rate
            request.status_code = 500
            request.success = False

        self.current_load = max(0, self.current_load - 1)
        return request


class MetricsCollector:
    """Collect and analyze load test metrics."""

    def __init__(self):
        self.results = []
        self.endpoint_metrics = defaultdict(list)

    def record(self, request):
        """Record a completed request."""
        self.results.append(request)
        self.endpoint_metrics[request.endpoint].append(request)

    def analyze(self):
        """Analyze collected metrics."""
        if not self.results:
            return LoadTestMetrics()

        response_times = [r.response_time_ms for r in self.results]
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]

        sorted_times = sorted(response_times)
        duration = max(r.timestamp for r in self.results) - min(r.timestamp for r in self.results)
        rps = len(self.results) / duration if duration > 0 else 0

        metrics = LoadTestMetrics(
            total_requests=len(self.results),
            successful_requests=len(successful),
            failed_requests=len(failed),
            avg_response_time_ms=statistics.mean(response_times),
            p50_response_time_ms=self._percentile(sorted_times, 50),
            p95_response_time_ms=self._percentile(sorted_times, 95),
            p99_response_time_ms=self._percentile(sorted_times, 99),
            max_response_time_ms=max(response_times),
            min_response_time_ms=min(response_times),
            requests_per_second=rps,
            error_rate=len(failed) / len(self.results),
        )

        metrics.bottlenecks = self._identify_bottlenecks()
        return metrics

    @staticmethod
    def _percentile(sorted_data, p):
        if not sorted_data:
            return 0.0
        k = (len(sorted_data) - 1) * p / 100
        f = int(k)
        c = f + 1
        if c >= len(sorted_data):
            return sorted_data[-1]
        return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])

    def _identify_bottlenecks(self):
        """Identify endpoint bottlenecks."""
        bottlenecks = []

        for endpoint, requests in self.endpoint_metrics.items():
            times = [r.response_time_ms for r in requests]
            errors = [r for r in requests if not r.success]
            avg = statistics.mean(times) if times else 0

            if avg > 100:  # slow endpoint
                bottlenecks.append({
                    "endpoint": endpoint,
                    "issue": "high_latency",
                    "avg_ms": avg,
                })
            if len(errors) / len(requests) > 0.05:
                bottlenecks.append({
                    "endpoint": endpoint,
                    "issue": "high_error_rate",
                    "error_rate": len(errors) / len(requests),
                })

        return bottlenecks


class LoadTester:
    """Orchestrate load tests."""

    def __init__(self, service=None):
        self.traffic_gen = TrafficGenerator()
        self.service = service or ServiceSimulator()
        self.collector = MetricsCollector()

    def run(self, total_requests=1000, concurrency=10):
        """Run a load test."""
        print(f"Starting load test: {total_requests} requests, concurrency={concurrency}")

        requests = self.traffic_gen.generate_batch(total_requests)

        for i in range(0, len(requests), concurrency):
            batch = requests[i:i + concurrency]
            self.service.current_load = len(batch)

            for req in batch:
                result = self.service.handle_request(req)
                self.collector.record(result)

        return self.collector.analyze()

    @staticmethod
    def generate_scaling_plan(metrics):
        """Generate a scaling plan based on test results."""
        plan = {"actions": [], "priority": "normal"}

        if metrics.error_rate > 0.05:
            plan["actions"].append("Scale up: high error rate detected")
            plan["priority"] = "high"

        if metrics.p95_response_time_ms > 500:
            plan["actions"].append("Optimize: P95 latency exceeds 500ms")
            plan["priority"] = "high"

        if metrics.p50_response_time_ms > 100:
            plan["actions"].append("Review: median latency exceeds 100ms")

        for bottleneck in metrics.bottlenecks:
            plan["actions"].append(
                f"Fix bottleneck: {bottleneck['endpoint']} ({bottleneck['issue']})"
            )

        if not plan["actions"]:
            plan["actions"].append("System performing within acceptable limits")

        return plan


if __name__ == "__main__":
    tester = LoadTester()

    # Run load test
    metrics = tester.run(total_requests=500, concurrency=20)

    print(f"\n{'='*50}")
    print(f"Total Requests:    {metrics.total_requests}")
    print(f"Successful:        {metrics.successful_requests}")
    print(f"Failed:            {metrics.failed_requests}")
    print(f"Error Rate:        {metrics.error_rate:.1%}")
    print(f"Avg Latency:       {metrics.avg_response_time_ms:.1f}ms")
    print(f"P50 Latency:       {metrics.p50_response_time_ms:.1f}ms")
    print(f"P95 Latency:       {metrics.p95_response_time_ms:.1f}ms")
    print(f"P99 Latency:       {metrics.p99_response_time_ms:.1f}ms")
    print(f"RPS:               {metrics.requests_per_second:.0f}")

    plan = tester.generate_scaling_plan(metrics)
    print(f"\nScaling Plan (priority={plan['priority']}):")
    for action in plan["actions"]:
        print(f"  - {action}")
