# 76. Algorithm: Chatbot NLP

## Overview

NLP-powered chatbot algorithm that processes user input through language models, detects intent, generates fast responses, logs securely, and updates analytics.

## Algorithm Steps

### Step 1: User Input → NLP Model
- User sends text message to chatbot interface.
- Input pre-processed: tokenization, normalization, spell correction.
- Context maintained: conversation history (last N turns) included.
- Language detection: auto-detect and route to appropriate model.
- Input sanitized: PII detection and masking before processing.

### Step 2: Model → Intent Detection
- **Intent Classification**: Map user input to predefined intents.
  - Examples: greeting, FAQ, order_status, complaint, transfer_to_agent.
- **Entity Extraction**: Identify key entities (dates, amounts, product names).
- **Slot Filling**: Extract required parameters for each intent.
- **Confidence Score**: Model outputs confidence for each detected intent.
- **Fallback**: Low-confidence inputs routed to human agent or clarification prompt.

### Step 3: Fast Response Generation
- **Rule-Based Responses**: Template responses for high-confidence simple intents.
- **Retrieval-Based**: Search FAQ database for matching answers.
- **Generative**: LLM-based response for complex or open-ended queries.
- **Action Execution**: API calls for transactional intents (check status, make booking).
- **Response Selection**: Best response chosen based on intent, context, and confidence.

### Step 4: Secure Logging
- All conversations logged for quality assurance and improvement.
- PII redacted from logs (replaced with tokens).
- Conversation metadata: session_id, user_id, timestamp, intent, response_type.
- Logs encrypted at rest and in transit.
- Retention policy: configurable per compliance requirements.

### Step 5: Analytics Update
- Intent frequency tracking: which intents are most common.
- Resolution rate: percentage of queries resolved without human handoff.
- User satisfaction: post-conversation feedback scoring.
- Response time metrics: average and percentile latency.
- Model performance: intent detection accuracy over time.

## Pseudocode

```
function processMessage(session_id, user_id, message):
    // Step 1: Pre-process
    cleaned_input = preprocess(message)
    context = conversationStore.getHistory(session_id, last_n=5)
    language = detectLanguage(cleaned_input)
    sanitized_input = redactPII(cleaned_input)
    
    // Step 2: Intent detection
    nlp_result = nlpModel.predict(sanitized_input, context, language)
    intent = nlp_result.intent
    entities = nlp_result.entities
    confidence = nlp_result.confidence
    
    // Low confidence handling
    if confidence < CONFIDENCE_THRESHOLD:
        if context.clarification_attempts < MAX_CLARIFICATIONS:
            response = generateClarificationPrompt(intent, entities)
            conversationStore.addTurn(session_id, message, response, 
                                      intent="clarification")
            return response
        else:
            return handoffToAgent(session_id, user_id, context)
    
    // Step 3: Generate response
    response = null
    
    if intent.type == "FAQ":
        // Retrieval-based
        answer = faqDatabase.search(sanitized_input, intent)
        response = formatFAQResponse(answer)
    
    elif intent.type == "TRANSACTIONAL":
        // Execute action
        slots = fillSlots(intent, entities, context)
        if not slots.complete:
            response = askForMissingSlots(slots)
        else:
            action_result = executeAction(intent.action, slots)
            response = formatActionResponse(action_result)
    
    elif intent.type == "COMPLEX":
        // LLM generation
        response = llm.generate(
            prompt=buildPrompt(sanitized_input, context, intent),
            max_tokens=500,
            temperature=0.7
        )
        response = postProcessResponse(response)
    
    else:
        // Template response
        response = templates.get(intent.name).render(entities)
    
    // Step 4: Secure logging
    conversationLog.record({
        session_id,
        user_id_hash: hash(user_id),
        input: sanitized_input,
        intent: intent.name,
        confidence: confidence,
        response_type: intent.type,
        response: redactPII(response),
        timestamp: now()
    })
    
    // Step 5: Analytics
    async:
        analytics.trackIntent(intent.name, confidence)
        analytics.trackResponseTime(session_id, latency)
        analytics.trackResolution(session_id, 
            resolved=intent.type != "HANDOFF")
    
    // Update conversation store
    conversationStore.addTurn(session_id, message, response, intent)
    
    return response

function handoffToAgent(session_id, user_id, context):
    agent = agentRouter.findAvailable(context.language, context.category)
    agentQueue.enqueue({
        session_id, user_id, context,
        reason: "low_confidence",
        priority: context.sentiment_score
    })
    return "I'm connecting you with a support agent. Please wait a moment."
```

## Performance Targets

| Metric | Target |
|--------|--------|
| Intent detection | < 50ms |
| Template response | < 100ms |
| LLM generation | < 2 seconds |
| Action execution | < 1 second |
| Resolution rate | > 70% |
