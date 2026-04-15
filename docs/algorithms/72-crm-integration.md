# 72. Algorithm: CRM Integration

## Overview

Enterprise CRM integration algorithm that handles API-based data exchange, bidirectional sync, fast updates, secure data transfer, and comprehensive audit logging.

## Algorithm Steps

### Step 1: Enterprise Request → CRM API
- Enterprise application initiates data request or update.
- Request types: create, read, update, delete (CRUD) operations.
- API authentication via OAuth 2.0 with service account credentials.
- Request validated against API schema and rate limits.
- Supported CRM platforms: Salesforce, HubSpot, Microsoft Dynamics.

### Step 2: API → Sync Data
- Bidirectional data mapping between internal schema and CRM schema.
- Field mapping configured per CRM platform and entity type.
- Conflict resolution: last-write-wins or custom merge strategy.
- Webhook listeners for real-time change notifications from CRM.
- Polling fallback for CRMs without webhook support.

### Step 3: Fast Updates
- Delta sync: only changed records transferred.
- Change detection via timestamps, version numbers, or change feeds.
- Batch operations: bulk API calls for high-volume updates.
- Parallel processing: multiple entity types synced simultaneously.
- Queue-based processing for reliability during CRM API outages.

### Step 4: Secure Transfer
- All API calls over HTTPS (TLS 1.3).
- OAuth 2.0 tokens with minimum required scopes.
- PII fields encrypted at the application level before transfer.
- IP whitelisting where supported by CRM platform.
- API key rotation on configurable schedule.

### Step 5: Logged for Audit
- Every sync operation logged with full context.
- Log fields: timestamp, direction, entity_type, record_count, status, duration.
- Error details logged for failed operations.
- Compliance reports: data access and transfer history.
- Retention: audit logs retained per enterprise compliance policy.

## Pseudocode

```
function syncCRM(enterprise_id, crm_config):
    crm_client = createCRMClient(crm_config)
    
    // Step 1: Authenticate
    token = crm_client.authenticate(
        client_id=crm_config.client_id,
        client_secret=decrypt(crm_config.encrypted_secret)
    )
    
    // Step 2: Determine sync scope
    last_sync = db.getLastSyncTimestamp(enterprise_id, crm_config.id)
    
    // Outbound: internal → CRM
    internal_changes = db.getChangedRecords(
        enterprise_id, since=last_sync, entities=crm_config.entities
    )
    
    for entity_type in crm_config.entities:
        records = internal_changes[entity_type]
        
        if records.isEmpty():
            continue
        
        // Step 3: Map and push
        mapped_records = records.map(r => 
            fieldMapper.toExternal(r, crm_config.field_mapping[entity_type])
        )
        
        // Step 4: Secure batch update
        result = crm_client.bulkUpsert(
            entity=entity_type,
            records=mapped_records,
            batch_size=200
        )
        
        // Step 5: Audit log
        auditLog.record({
            enterprise_id,
            direction: "outbound",
            entity_type,
            record_count: records.length,
            success_count: result.success,
            error_count: result.errors.length,
            duration_ms: result.duration,
            timestamp: now()
        })
    
    // Inbound: CRM → internal
    crm_changes = crm_client.getChangedRecords(since=last_sync)
    
    for entity_type, records in crm_changes:
        mapped_records = records.map(r =>
            fieldMapper.toInternal(r, crm_config.field_mapping[entity_type])
        )
        
        // Conflict resolution
        for record in mapped_records:
            existing = db.getRecord(entity_type, record.id)
            if existing and existing.updated_at > record.updated_at:
                conflictResolver.resolve(existing, record, strategy=crm_config.conflict_strategy)
            else:
                db.upsert(entity_type, record)
        
        auditLog.record({
            enterprise_id,
            direction: "inbound",
            entity_type,
            record_count: records.length,
            timestamp: now()
        })
    
    db.updateLastSyncTimestamp(enterprise_id, crm_config.id, now())

// Webhook handler for real-time sync
function onCRMWebhook(webhook_event):
    enterprise_id = lookupEnterprise(webhook_event.org_id)
    record = fieldMapper.toInternal(webhook_event.data)
    db.upsert(webhook_event.entity_type, record)
    auditLog.record({enterprise_id, direction: "inbound-webhook", ...})
```

## Performance Targets

| Metric | Target |
|--------|--------|
| Single record sync | < 500ms |
| Bulk sync (1K records) | < 10 seconds |
| Webhook processing | < 1 second |
| Field mapping | < 1ms per record |
| Full sync (initial) | < 1 hour |
