"""
Algorithm 103: Predictive Scaling

- Historical data analyzed
- ML model predicts load
- Fast scaling ahead of demand
- Resources provisioned
- Performance maintained
"""

import math
import time
from dataclasses import dataclass, field
from collections import deque


@dataclass
class LoadDataPoint:
    """A historical load data point."""
    timestamp: float
    request_rate: float
    cpu_utilization: float
    memory_utilization: float
    active_instances: int


@dataclass
class LoadPrediction:
    """A predicted future load."""
    predicted_rate: float
    predicted_cpu: float
    confidence: float
    predicted_instances_needed: int
    forecast_horizon_minutes: int
    timestamp: float = field(default_factory=time.time)


class TimeSeriesPredictor:
    """Simple time series prediction using exponential smoothing and seasonality."""

    def __init__(self, seasonal_period=24):
        self.alpha = 0.3  # smoothing factor
        self.beta = 0.1  # trend factor
        self.gamma = 0.2  # seasonal factor
        self.seasonal_period = seasonal_period
        self.history = []

    def fit(self, data_points):
        """Fit the model to historical data."""
        self.history = [dp.request_rate for dp in data_points]

    def predict(self, steps_ahead=1):
        """Predict future values."""
        if len(self.history) < 3:
            return [self.history[-1] if self.history else 0] * steps_ahead

        # Simple exponential smoothing with trend
        level = self.history[0]
        trend = (self.history[1] - self.history[0]) if len(self.history) > 1 else 0

        for value in self.history:
            new_level = self.alpha * value + (1 - self.alpha) * (level + trend)
            new_trend = self.beta * (new_level - level) + (1 - self.beta) * trend
            level = new_level
            trend = new_trend

        # Handle seasonality
        seasonal_component = 0
        if len(self.history) >= self.seasonal_period:
            period_data = self.history[-self.seasonal_period:]
            avg = sum(period_data) / len(period_data)
            seasonal_component = (period_data[-1] - avg) * self.gamma if avg else 0

        predictions = []
        for i in range(steps_ahead):
            pred = level + trend * (i + 1) + seasonal_component
            predictions.append(max(0, pred))

        return predictions

    def get_confidence(self):
        """Estimate prediction confidence."""
        if len(self.history) < 5:
            return 0.3

        # Based on data stability
        recent = self.history[-10:] if len(self.history) >= 10 else self.history
        avg = sum(recent) / len(recent)
        if avg == 0:
            return 0.5

        variance = sum((v - avg) ** 2 for v in recent) / len(recent)
        cv = math.sqrt(variance) / avg
        return max(0.1, min(0.95, 1.0 - cv))


class CapacityPlanner:
    """Plan capacity based on predictions."""

    def __init__(self, capacity_per_instance=100, target_utilization=0.7):
        self.capacity_per_instance = capacity_per_instance
        self.target_utilization = target_utilization
        self.min_instances = 2
        self.max_instances = 50

    def plan(self, predicted_rate, confidence):
        """Calculate required instances for predicted load."""
        # Add safety margin based on confidence
        safety_factor = 1.0 + (1.0 - confidence) * 0.5
        adjusted_rate = predicted_rate * safety_factor

        effective_capacity = self.capacity_per_instance * self.target_utilization
        required = math.ceil(adjusted_rate / effective_capacity) if effective_capacity > 0 else self.min_instances

        return max(self.min_instances, min(self.max_instances, required))


class PredictiveScaler:
    """Complete predictive scaling system."""

    def __init__(self, forecast_horizon_minutes=30, capacity_per_instance=100):
        self.predictor = TimeSeriesPredictor()
        self.planner = CapacityPlanner(capacity_per_instance)
        self.history = deque(maxlen=1000)
        self.forecast_horizon = forecast_horizon_minutes
        self.scaling_log = []
        self.current_instances = 2

    def record(self, data_point):
        """Record a historical data point."""
        self.history.append(data_point)

    def predict_and_scale(self):
        """Predict future load and pre-provision resources."""
        if len(self.history) < 5:
            return None

        self.predictor.fit(list(self.history))

        steps = self.forecast_horizon
        predictions = self.predictor.predict(steps)
        confidence = self.predictor.get_confidence()

        peak_predicted = max(predictions) if predictions else 0
        avg_predicted = sum(predictions) / len(predictions) if predictions else 0

        # Plan for peak
        needed = self.planner.plan(peak_predicted, confidence)

        prediction = LoadPrediction(
            predicted_rate=avg_predicted,
            predicted_cpu=min(100, avg_predicted / max(self.current_instances * 100, 1) * 100),
            confidence=confidence,
            predicted_instances_needed=needed,
            forecast_horizon_minutes=self.forecast_horizon,
        )

        if needed != self.current_instances:
            action = "scale_out" if needed > self.current_instances else "scale_in"
            self.scaling_log.append({
                "action": action,
                "from": self.current_instances,
                "to": needed,
                "predicted_rate": avg_predicted,
                "confidence": confidence,
                "timestamp": time.time(),
            })
            self.current_instances = needed

        return prediction

    def get_scaling_history(self):
        return list(self.scaling_log)


if __name__ == "__main__":
    scaler = PredictiveScaler(forecast_horizon_minutes=30, capacity_per_instance=100)

    # Simulate historical load pattern (daily cycle)
    base_time = time.time()
    for i in range(48):  # 48 data points (30-min intervals = 24 hours)
        hour = i % 24
        # Simulate daily traffic pattern
        rate = 200 + 300 * math.sin(math.pi * (hour - 6) / 12) if 6 <= hour <= 22 else 100
        rate = max(50, rate)

        dp = LoadDataPoint(
            timestamp=base_time + i * 1800,
            request_rate=rate,
            cpu_utilization=rate / 5,
            memory_utilization=rate / 8,
            active_instances=max(2, int(rate / 100)),
        )
        scaler.record(dp)

    # Predict and scale
    prediction = scaler.predict_and_scale()
    if prediction:
        print(f"Prediction (next {prediction.forecast_horizon_minutes}min):")
        print(f"  Predicted rate: {prediction.predicted_rate:.0f} req/s")
        print(f"  Confidence: {prediction.confidence:.1%}")
        print(f"  Instances needed: {prediction.predicted_instances_needed}")
        print(f"  Current instances: {scaler.current_instances}")

    # Show scaling history
    history = scaler.get_scaling_history()
    for event in history:
        print(f"\nScaling: {event['action']} {event['from']} → {event['to']} "
              f"(predicted={event['predicted_rate']:.0f}, confidence={event['confidence']:.1%})")
