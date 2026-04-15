# 49. Algorithm: Fraud Detection (Payments)

## Overview

Real-time payment fraud detection pipeline that extracts transaction features, scores risk with ML models, applies rule-based cross-checks, and makes fast accept/flag decisions.

## Algorithm Steps

### Step 1: Transaction Features Extracted
- **Transaction Features**: amount, currency, merchant_category, payment_method.
- **Velocity Features**: transaction count/amount in last 1h, 24h, 7d.
- **Behavioral Features**: deviation from user's typical spending pattern.
- **Device Features**: device_id, IP address, geolocation, browser fingerprint.
- **Contextual Features**: time_of_day, day_of_week, is_holiday.

### Step 2: ML Model Scores Risk
- **Model Type**: Gradient Boosted Trees (XGBoost/LightGBM) for tabular features.
- **Deep Model**: Neural network for sequence-based pattern detection.
- **Ensemble**: Combined prediction from multiple models.
- **Output**: Risk score between 0.0 (safe) and 1.0 (fraudulent).
- **Inference Time**: < 5ms per transaction.

### Step 3: If Score > Threshold → Flag
- **Low Risk** (score < 0.3): Auto-approve.
- **Medium Risk** (0.3 ≤ score < 0.7): Additional verification (3D Secure, OTP).
- **High Risk** (score ≥ 0.7): Flag for manual review or auto-decline.
- **Adaptive Threshold**: Thresholds adjust based on current fraud rates.
- **Merchant-Specific**: Different thresholds per merchant risk category.

### Step 4: Rule Engine Cross-Checks
- **Velocity Rules**: > N transactions in T minutes → flag.
- **Amount Rules**: Unusual amounts (too high, round numbers).
- **Geo Rules**: Transaction location vs. user's home location.
- **Blocklist**: Known fraudulent cards, devices, IPs.
- **Pattern Rules**: Common fraud patterns (card testing, BIN attacks).

### Step 5: Fast Decision Pipeline
- All steps execute in a streaming pipeline.
- Feature extraction + ML scoring + rule checks run in parallel where possible.
- Final decision combines ML score + rule violations.
- Decision logged with full audit trail.
- Feedback loop: analyst decisions improve future model accuracy.

## Pseudocode

```
function detectFraud(transaction):
    // Step 1: Feature extraction
    features = extractFeatures(transaction)
    features.velocity = computeVelocity(transaction.user_id)
    features.behavioral = computeDeviation(transaction, userProfile)
    features.device = extractDeviceFeatures(transaction.request)
    features.context = extractContextFeatures(transaction.timestamp)
    
    // Step 2 + Step 4: Run in parallel
    parallel:
        ml_score = mlModel.predict(features)
        rule_violations = ruleEngine.evaluate(transaction, features)
    
    // Step 3: Decision based on combined score
    combined_score = combineScores(ml_score, rule_violations)
    threshold = getAdaptiveThreshold(
        transaction.merchant_category,
        currentFraudRate()
    )
    
    if combined_score < threshold.low:
        decision = APPROVE
    elif combined_score < threshold.high:
        decision = CHALLENGE  // Request additional verification
    else:
        decision = DECLINE
    
    // Step 5: Log and return
    auditLog.record({
        transaction_id: transaction.id,
        ml_score, rule_violations,
        combined_score, decision,
        features_snapshot: features,
        timestamp: now()
    })
    
    // Async: Update velocity counters
    async:
        velocityStore.increment(transaction.user_id, transaction)
    
    return decision

function feedbackLoop(transaction_id, analyst_decision):
    // Analyst marks transaction as fraud/legitimate
    trainingData.append(transaction_id, analyst_decision)
    if trainingData.size % RETRAIN_THRESHOLD == 0:
        mlModel.retrain(trainingData)
```

## Performance Targets

| Metric | Target |
|--------|--------|
| Feature extraction | < 2ms |
| ML inference | < 5ms |
| Rule engine | < 3ms |
| End-to-end decision | < 15ms |
| Detection rate | > 95% |
| False positive rate | < 0.5% |
