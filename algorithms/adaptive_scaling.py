"""
Algorithm 102: Adaptive Scaling

- Metrics monitored
- Fast decision engine
- Scale out/in
- Cloud orchestration
- Cost optimized
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from collections import deque


class ScalingAction(Enum):
    SCALE_OUT = "scale_out"
    SCALE_IN = "scale_in"
    NO_ACTION = "no_action"


@dataclass
class SystemMetrics:
    """Current system metrics."""
    cpu_utilization: float  # 0-100
    memory_utilization: float  # 0-100
    request_rate: float  # req/s
    response_time_ms: float
    error_rate: float  # 0-1
    active_instances: int
    timestamp: float = field(default_factory=time.time)


@dataclass
class ScalingDecision:
    """A scaling decision with rationale."""
    action: ScalingAction
    current_instances: int
    target_instances: int
    reason: str
    estimated_cost_delta: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class Instance:
    """A cloud instance."""
    instance_id: str
    instance_type: str
    cost_per_hour: float
    launched_at: float = field(default_factory=time.time)
    healthy: bool = True


class MetricsMonitor:
    """Monitor system metrics over time."""

    def __init__(self, window_size=10):
        self.history = deque(maxlen=window_size)

    def record(self, metrics):
        self.history.append(metrics)

    def get_average(self):
        if not self.history:
            return None
        n = len(self.history)
        return SystemMetrics(
            cpu_utilization=sum(m.cpu_utilization for m in self.history) / n,
            memory_utilization=sum(m.memory_utilization for m in self.history) / n,
            request_rate=sum(m.request_rate for m in self.history) / n,
            response_time_ms=sum(m.response_time_ms for m in self.history) / n,
            error_rate=sum(m.error_rate for m in self.history) / n,
            active_instances=self.history[-1].active_instances,
        )

    def get_trend(self, metric_name):
        """Get trend for a metric: 'increasing', 'stable', 'decreasing'."""
        if len(self.history) < 3:
            return "stable"

        values = [getattr(m, metric_name) for m in self.history]
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]

        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)

        if avg_second > avg_first * 1.1:
            return "increasing"
        elif avg_second < avg_first * 0.9:
            return "decreasing"
        return "stable"


class DecisionEngine:
    """Fast scaling decision engine."""

    def __init__(self, config=None):
        self.config = config or {
            "cpu_scale_out_threshold": 70,
            "cpu_scale_in_threshold": 30,
            "memory_scale_out_threshold": 80,
            "response_time_scale_out_ms": 500,
            "error_rate_scale_out": 0.05,
            "min_instances": 2,
            "max_instances": 20,
            "cooldown_seconds": 300,
            "scale_out_step": 2,
            "scale_in_step": 1,
        }
        self.last_scale_time = 0

    def decide(self, avg_metrics, trends):
        """Make a scaling decision based on metrics and trends."""
        if avg_metrics is None:
            return ScalingDecision(
                action=ScalingAction.NO_ACTION,
                current_instances=0,
                target_instances=0,
                reason="Insufficient metrics",
            )

        now = time.time()
        if now - self.last_scale_time < self.config["cooldown_seconds"]:
            return ScalingDecision(
                action=ScalingAction.NO_ACTION,
                current_instances=avg_metrics.active_instances,
                target_instances=avg_metrics.active_instances,
                reason="Cooldown period active",
            )

        current = avg_metrics.active_instances
        reasons = []

        # Check for scale out conditions
        scale_out = False
        if avg_metrics.cpu_utilization > self.config["cpu_scale_out_threshold"]:
            scale_out = True
            reasons.append(f"CPU={avg_metrics.cpu_utilization:.1f}%")
        if avg_metrics.memory_utilization > self.config["memory_scale_out_threshold"]:
            scale_out = True
            reasons.append(f"Memory={avg_metrics.memory_utilization:.1f}%")
        if avg_metrics.response_time_ms > self.config["response_time_scale_out_ms"]:
            scale_out = True
            reasons.append(f"Latency={avg_metrics.response_time_ms:.0f}ms")
        if avg_metrics.error_rate > self.config["error_rate_scale_out"]:
            scale_out = True
            reasons.append(f"Errors={avg_metrics.error_rate:.1%}")

        if scale_out:
            target = min(
                current + self.config["scale_out_step"],
                self.config["max_instances"],
            )
            if target > current:
                self.last_scale_time = now
                return ScalingDecision(
                    action=ScalingAction.SCALE_OUT,
                    current_instances=current,
                    target_instances=target,
                    reason=f"Scale out: {', '.join(reasons)}",
                )

        # Check for scale in conditions
        if (avg_metrics.cpu_utilization < self.config["cpu_scale_in_threshold"] and
                avg_metrics.memory_utilization < self.config["cpu_scale_in_threshold"] and
                trends.get("cpu_utilization") != "increasing"):
            target = max(
                current - self.config["scale_in_step"],
                self.config["min_instances"],
            )
            if target < current:
                self.last_scale_time = now
                return ScalingDecision(
                    action=ScalingAction.SCALE_IN,
                    current_instances=current,
                    target_instances=target,
                    reason=f"Scale in: CPU={avg_metrics.cpu_utilization:.1f}%, low utilization",
                )

        return ScalingDecision(
            action=ScalingAction.NO_ACTION,
            current_instances=current,
            target_instances=current,
            reason="Metrics within acceptable range",
        )


class CloudOrchestrator:
    """Orchestrate cloud instances for adaptive scaling."""

    def __init__(self, instance_type="standard", cost_per_hour=0.10):
        self.instances = {}
        self.instance_type = instance_type
        self.cost_per_hour = cost_per_hour
        self._counter = 0
        self.scaling_history = []

    def launch_instance(self):
        """Launch a new instance."""
        self._counter += 1
        instance = Instance(
            instance_id=f"i-{self._counter:04d}",
            instance_type=self.instance_type,
            cost_per_hour=self.cost_per_hour,
        )
        self.instances[instance.instance_id] = instance
        return instance

    def terminate_instance(self, instance_id=None):
        """Terminate an instance (oldest by default)."""
        if instance_id:
            return self.instances.pop(instance_id, None)

        if self.instances:
            oldest_id = min(
                self.instances, key=lambda k: self.instances[k].launched_at
            )
            return self.instances.pop(oldest_id)
        return None

    def apply_decision(self, decision):
        """Apply a scaling decision."""
        self.scaling_history.append(decision)

        if decision.action == ScalingAction.SCALE_OUT:
            diff = decision.target_instances - decision.current_instances
            launched = []
            for _ in range(diff):
                instance = self.launch_instance()
                launched.append(instance.instance_id)
            return launched

        elif decision.action == ScalingAction.SCALE_IN:
            diff = decision.current_instances - decision.target_instances
            terminated = []
            for _ in range(diff):
                instance = self.terminate_instance()
                if instance:
                    terminated.append(instance.instance_id)
            return terminated

        return []

    @property
    def active_count(self):
        return len(self.instances)

    @property
    def hourly_cost(self):
        return sum(i.cost_per_hour for i in self.instances.values())


class AdaptiveScaler:
    """Complete adaptive scaling system."""

    def __init__(self):
        self.monitor = MetricsMonitor()
        self.engine = DecisionEngine()
        self.orchestrator = CloudOrchestrator()

        # Start with minimum instances
        for _ in range(self.engine.config["min_instances"]):
            self.orchestrator.launch_instance()

    def process_metrics(self, metrics):
        """Process new metrics and potentially scale."""
        metrics.active_instances = self.orchestrator.active_count
        self.monitor.record(metrics)

        avg = self.monitor.get_average()
        trends = {
            "cpu_utilization": self.monitor.get_trend("cpu_utilization"),
            "request_rate": self.monitor.get_trend("request_rate"),
        }

        decision = self.engine.decide(avg, trends)

        if decision.action != ScalingAction.NO_ACTION:
            result = self.orchestrator.apply_decision(decision)
            return decision, result

        return decision, []


if __name__ == "__main__":
    scaler = AdaptiveScaler()
    # Disable cooldown for demo
    scaler.engine.config["cooldown_seconds"] = 0

    scenarios = [
        SystemMetrics(cpu_utilization=40, memory_utilization=30, request_rate=100,
                      response_time_ms=50, error_rate=0.01, active_instances=2),
        SystemMetrics(cpu_utilization=75, memory_utilization=60, request_rate=500,
                      response_time_ms=200, error_rate=0.02, active_instances=2),
        SystemMetrics(cpu_utilization=85, memory_utilization=70, request_rate=800,
                      response_time_ms=400, error_rate=0.04, active_instances=4),
        SystemMetrics(cpu_utilization=25, memory_utilization=20, request_rate=50,
                      response_time_ms=30, error_rate=0.0, active_instances=4),
    ]

    for i, metrics in enumerate(scenarios):
        decision, result = scaler.process_metrics(metrics)
        print(f"Step {i+1}: CPU={metrics.cpu_utilization}%, "
              f"instances={scaler.orchestrator.active_count} → "
              f"{decision.action.value} ({decision.reason})")
        if result:
            print(f"  Changed: {result}")

    print(f"\nFinal: {scaler.orchestrator.active_count} instances, "
          f"${scaler.orchestrator.hourly_cost:.2f}/hr")
