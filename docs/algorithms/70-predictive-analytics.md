# 70. Algorithm: Predictive Analytics

## Overview

Predictive analytics algorithm that ingests data into ML models, generates trend predictions with fast inference, stores results, and visualizes insights in dashboards.

## Algorithm Steps

### Step 1: Data → ML Model
- Historical data extracted from data warehouse.
- Feature engineering: time-based features, aggregations, lag features.
- Data split: train (70%), validation (15%), test (15%).
- Model selection: ARIMA, Prophet, XGBoost, LSTM based on data pattern.
- Cross-validation for robust model evaluation.

### Step 2: Model Predicts Trends
- **Time Series Forecasting**: Predict future values (revenue, users, load).
- **Classification**: Churn prediction, fraud classification.
- **Regression**: Revenue forecasting, demand prediction.
- **Confidence Intervals**: Prediction with uncertainty bounds.
- **Multi-Horizon**: Short-term (1 day) to long-term (90 days) predictions.

### Step 3: Fast Inference
- Model serialized and deployed to serving infrastructure.
- Batch inference: daily predictions for all entities.
- Online inference: real-time predictions via API (< 50ms).
- Model optimization: ONNX Runtime for cross-framework optimization.
- Caching: prediction results cached for repeated queries.

### Step 4: Results Stored in DB
- Predictions stored in time-series database or relational DB.
- Schema: entity_id, prediction_date, target_date, predicted_value, confidence.
- Historical predictions retained for accuracy tracking.
- Model metadata: version, training date, metrics, features used.
- Automated accuracy comparison: predicted vs. actual.

### Step 5: Visualized in Dashboards
- Prediction charts with confidence bands.
- Actual vs. predicted comparison over time.
- Model performance metrics (MAPE, RMSE, R²).
- Drill-down by segment, region, product.
- Automated alerts when predictions exceed thresholds.

## Pseudocode

```
function trainPredictiveModel(target_metric):
    // Step 1: Prepare data
    data = warehouse.query(f"""
        SELECT date, {target_metric}, features.*
        FROM daily_metrics
        JOIN feature_table features USING (date)
        WHERE date BETWEEN '2023-01-01' AND today()
    """)
    
    features = engineerFeatures(data)
    train, val, test = splitData(features, ratios=[0.7, 0.15, 0.15])
    
    // Model selection
    models = {
        "prophet": ProphetModel(),
        "xgboost": XGBoostRegressor(),
        "lstm": LSTMModel(hidden_size=128)
    }
    
    best_model = None
    best_score = infinity
    
    for name, model in models:
        model.fit(train.X, train.y)
        score = model.evaluate(val.X, val.y, metric="MAPE")
        
        if score < best_score:
            best_model = model
            best_score = score
    
    // Final evaluation
    test_score = best_model.evaluate(test.X, test.y)
    
    // Save model
    mlflow.logModel(best_model, metrics={
        "MAPE": test_score,
        "training_date": today(),
        "features": features.columns
    })
    
    return best_model

function predict(model, horizon_days=30):
    // Step 2: Generate predictions
    predictions = []
    
    for day in range(1, horizon_days + 1):
        target_date = today() + days(day)
        features = getLatestFeatures(target_date)
        
        prediction = model.predict(features)
        confidence = model.predictInterval(features, confidence=0.95)
        
        predictions.append({
            prediction_date: today(),
            target_date: target_date,
            predicted_value: prediction,
            lower_bound: confidence.lower,
            upper_bound: confidence.upper
        })
    
    // Step 4: Store results
    db.bulkInsert("predictions", predictions)
    
    // Check accuracy of past predictions
    evaluatePastPredictions(model.id)
    
    return predictions

function servePrediction(entity_id, target_date):
    // Step 3: Fast inference
    cached = cache.get(f"pred:{entity_id}:{target_date}")
    if cached:
        return cached
    
    features = featureStore.get(entity_id)
    prediction = model.predict(features)
    
    cache.set(f"pred:{entity_id}:{target_date}", prediction, ttl=1h)
    return prediction
```

## Performance Targets

| Metric | Target |
|--------|--------|
| Model training | < 1 hour |
| Batch inference (1M entities) | < 30 minutes |
| Online inference | < 50ms |
| MAPE (accuracy) | < 10% |
| Dashboard visualization | < 5 seconds |
