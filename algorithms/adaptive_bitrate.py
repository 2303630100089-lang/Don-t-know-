"""
Algorithm 84: Adaptive Bitrate

- Network conditions monitored
- Bitrate adjusted dynamically
- Fast switching
- Smooth playback
- User QoE optimized
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from collections import deque


class QualityLevel(Enum):
    ULTRA_LOW = "144p"
    LOW = "360p"
    MEDIUM = "480p"
    HIGH = "720p"
    FULL_HD = "1080p"
    ULTRA_HD = "4K"


@dataclass
class BitrateProfile:
    """A bitrate profile for a quality level."""
    quality: QualityLevel
    bitrate_kbps: int
    min_bandwidth_kbps: int
    resolution: str
    buffer_target_seconds: float = 5.0


@dataclass
class NetworkMetrics:
    """Current network condition metrics."""
    bandwidth_kbps: float
    latency_ms: float
    packet_loss_ratio: float
    jitter_ms: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class QoEMetrics:
    """Quality of Experience metrics."""
    current_quality: QualityLevel
    buffer_health: float  # seconds of buffer
    rebuffer_count: int
    quality_switches: int
    avg_bitrate_kbps: float
    session_duration: float


BITRATE_PROFILES = [
    BitrateProfile(QualityLevel.ULTRA_LOW, 200, 250, "256x144"),
    BitrateProfile(QualityLevel.LOW, 500, 600, "640x360"),
    BitrateProfile(QualityLevel.MEDIUM, 1000, 1200, "854x480"),
    BitrateProfile(QualityLevel.HIGH, 2500, 3000, "1280x720"),
    BitrateProfile(QualityLevel.FULL_HD, 5000, 6000, "1920x1080"),
    BitrateProfile(QualityLevel.ULTRA_HD, 15000, 18000, "3840x2160"),
]


class NetworkMonitor:
    """Monitor network conditions."""

    def __init__(self, window_size=10):
        self.measurements = deque(maxlen=window_size)

    def record(self, metrics):
        """Record a network measurement."""
        self.measurements.append(metrics)

    def get_average_bandwidth(self):
        """Get smoothed average bandwidth."""
        if not self.measurements:
            return 0
        return sum(m.bandwidth_kbps for m in self.measurements) / len(self.measurements)

    def get_trend(self):
        """Detect bandwidth trend: 'improving', 'stable', or 'degrading'."""
        if len(self.measurements) < 3:
            return "stable"

        recent = list(self.measurements)
        first_half = recent[:len(recent)//2]
        second_half = recent[len(recent)//2:]

        avg_first = sum(m.bandwidth_kbps for m in first_half) / len(first_half)
        avg_second = sum(m.bandwidth_kbps for m in second_half) / len(second_half)

        if avg_second > avg_first * 1.15:
            return "improving"
        elif avg_second < avg_first * 0.85:
            return "degrading"
        return "stable"

    def get_stability(self):
        """Get network stability score (0-1)."""
        if len(self.measurements) < 2:
            return 1.0

        bandwidths = [m.bandwidth_kbps for m in self.measurements]
        avg = sum(bandwidths) / len(bandwidths)
        if avg == 0:
            return 0.0
        variance = sum((b - avg) ** 2 for b in bandwidths) / len(bandwidths)
        std_dev = variance ** 0.5
        cv = std_dev / avg
        return max(0.0, 1.0 - cv)


class AdaptiveBitrateController:
    """
    Adaptive bitrate streaming controller.
    Adjusts quality based on network conditions for optimal QoE.
    """

    def __init__(self, profiles=None):
        self.profiles = profiles or BITRATE_PROFILES
        self.profiles.sort(key=lambda p: p.bitrate_kbps)
        self.network_monitor = NetworkMonitor()
        self.current_profile_idx = 0
        self.buffer_seconds = 0.0
        self.rebuffer_count = 0
        self.quality_switches = 0
        self.bitrate_history = []
        self.session_start = time.time()

        # Thresholds
        self.buffer_panic_threshold = 2.0  # seconds
        self.buffer_low_threshold = 5.0
        self.buffer_high_threshold = 15.0
        self.switch_cooldown = 3.0  # minimum seconds between switches
        self.last_switch_time = 0.0

    @property
    def current_profile(self):
        return self.profiles[self.current_profile_idx]

    def update_network(self, metrics):
        """Update with new network measurements."""
        self.network_monitor.record(metrics)

    def update_buffer(self, buffer_seconds):
        """Update current buffer level."""
        if buffer_seconds <= 0 and self.buffer_seconds > 0:
            self.rebuffer_count += 1
        self.buffer_seconds = max(0, buffer_seconds)

    def select_quality(self):
        """Select optimal quality level based on current conditions."""
        avg_bandwidth = self.network_monitor.get_average_bandwidth()
        trend = self.network_monitor.get_trend()
        stability = self.network_monitor.get_stability()

        now = time.time()
        if now - self.last_switch_time < self.switch_cooldown:
            return self.current_profile

        # Emergency downgrade on buffer panic
        if self.buffer_seconds < self.buffer_panic_threshold:
            target_idx = 0
        # Conservative when buffer is low
        elif self.buffer_seconds < self.buffer_low_threshold:
            effective_bandwidth = avg_bandwidth * 0.7 * stability
            target_idx = self._find_profile_for_bandwidth(effective_bandwidth)
        # Aggressive upgrade when buffer is healthy
        elif self.buffer_seconds > self.buffer_high_threshold and trend == "improving":
            effective_bandwidth = avg_bandwidth * 0.9
            target_idx = self._find_profile_for_bandwidth(effective_bandwidth)
        else:
            safety_factor = 0.8 if trend == "stable" else 0.6
            effective_bandwidth = avg_bandwidth * safety_factor * stability
            target_idx = self._find_profile_for_bandwidth(effective_bandwidth)

        # Apply smooth switching (max one level at a time for upgrades)
        if target_idx > self.current_profile_idx:
            target_idx = min(target_idx, self.current_profile_idx + 1)

        if target_idx != self.current_profile_idx:
            self.current_profile_idx = target_idx
            self.quality_switches += 1
            self.last_switch_time = now

        self.bitrate_history.append(self.current_profile.bitrate_kbps)
        return self.current_profile

    def _find_profile_for_bandwidth(self, bandwidth_kbps):
        """Find the highest quality profile that fits the bandwidth."""
        best_idx = 0
        for i, profile in enumerate(self.profiles):
            if profile.min_bandwidth_kbps <= bandwidth_kbps:
                best_idx = i
        return best_idx

    def get_qoe_metrics(self):
        """Get current QoE metrics."""
        avg_bitrate = (
            sum(self.bitrate_history) / len(self.bitrate_history)
            if self.bitrate_history else 0
        )
        return QoEMetrics(
            current_quality=self.current_profile.quality,
            buffer_health=self.buffer_seconds,
            rebuffer_count=self.rebuffer_count,
            quality_switches=self.quality_switches,
            avg_bitrate_kbps=avg_bitrate,
            session_duration=time.time() - self.session_start,
        )


if __name__ == "__main__":
    controller = AdaptiveBitrateController()

    # Simulate varying network conditions
    scenarios = [
        NetworkMetrics(bandwidth_kbps=8000, latency_ms=20, packet_loss_ratio=0.0, jitter_ms=5),
        NetworkMetrics(bandwidth_kbps=7500, latency_ms=25, packet_loss_ratio=0.01, jitter_ms=8),
        NetworkMetrics(bandwidth_kbps=3000, latency_ms=50, packet_loss_ratio=0.02, jitter_ms=15),
        NetworkMetrics(bandwidth_kbps=1500, latency_ms=80, packet_loss_ratio=0.05, jitter_ms=30),
        NetworkMetrics(bandwidth_kbps=800, latency_ms=100, packet_loss_ratio=0.1, jitter_ms=50),
        NetworkMetrics(bandwidth_kbps=2000, latency_ms=60, packet_loss_ratio=0.02, jitter_ms=20),
        NetworkMetrics(bandwidth_kbps=5000, latency_ms=30, packet_loss_ratio=0.01, jitter_ms=10),
        NetworkMetrics(bandwidth_kbps=9000, latency_ms=15, packet_loss_ratio=0.0, jitter_ms=5),
    ]

    buffer = 10.0  # start with 10 seconds of buffer
    for i, metrics in enumerate(scenarios):
        controller.update_network(metrics)
        controller.update_buffer(buffer)
        profile = controller.select_quality()

        print(f"Step {i+1}: BW={metrics.bandwidth_kbps}kbps, "
              f"Buffer={buffer:.1f}s → {profile.quality.value} "
              f"({profile.bitrate_kbps}kbps)")

        # Simulate buffer dynamics
        buffer += 1.0 - (profile.bitrate_kbps / max(metrics.bandwidth_kbps, 1))
        buffer = max(0, buffer)
        controller.last_switch_time = 0  # disable cooldown for demo

    qoe = controller.get_qoe_metrics()
    print(f"\nQoE: avg_bitrate={qoe.avg_bitrate_kbps:.0f}kbps, "
          f"rebuffers={qoe.rebuffer_count}, switches={qoe.quality_switches}")
