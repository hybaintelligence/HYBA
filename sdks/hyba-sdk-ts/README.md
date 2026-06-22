# HYBA TypeScript SDK

TypeScript/JavaScript SDK for HYBA Quantum Intelligence API platform. Provision, manage, and execute computational intelligence services from your Node.js or browser application.

## Installation

```bash
npm install @hyba/sdk
# or
yarn add @hyba/sdk
```

## Quick Start

```typescript
import { HybaClient } from '@hyba/sdk';

// Initialize client
const client = new HybaClient({
  apiKey: 'hyba_live_...',
  apiUrl: 'https://api.hyba.ai'
});

// Provision a service
const service = await client.provisioning.createService({
  name: 'portfolio-optimizer',
  tier: 'production',
  connector: {
    type: 'sql_snowflake',
    host: 'acme.snowflakecomputing.com',
    database: 'finance_dw'
  }
});

console.log(`Service provisioned: ${service.serviceId}`);

// Start the service
await service.start();

// Execute a workload
const result = await service.execute({
  workload: 'explain',
  context: 'Portfolio optimization strategy'
});

console.log(result);
```


## Quantum Intelligence API

HYBA exposes QIaaS as a first-class **Quantum Intelligence API**: beyond AGI/ASI framing, substrate-independent, evidence-sealed, and governed by enterprise auth, tenancy, quota, trace, and audit controls. Responses include execution evidence such as `qi_execution_id`, `evidence_id`, `trace_id`, `claim_boundary`, `substrate_state`, and usage-meter data.

## API Reference

### Client Initialization

```typescript
const client = new HybaClient({
  apiKey: 'hyba_live_...',
  apiUrl: 'https://api.hyba.ai',    // optional
  timeout: 30000,                     // optional, default 30s
  retries: 3                          // optional, default 3
});
```

### Service Provisioning

```typescript
// Create service
const service = await client.provisioning.createService({
  name: 'my-service',
  tier: 'production',
  connector?: ConnectorConfig,
  pulvini?: PulviniConfig
});

// List services
const services = await client.provisioning.listServices();

// Get service details
const service = await client.provisioning.getService('service-id');

// Delete service
await client.provisioning.deleteService('service-id');
```

### Service Operations

```typescript
// Start service
await service.start();

// Stop service
await service.stop();

// Execute workload
const result = await service.execute({
  workload: 'explain',
  context: 'Your context here'
});

// Get service health
const health = await service.health();

// Refresh service state
await service.refresh();
```

### Workload Types

```typescript
// Explain workload
const explanation = await service.explain('Portfolio optimization strategy');

// Orchestrate workload
const orchestration = await service.orchestrate('Market analysis');

// Counterfactual analysis
const counterfactual = await service.counterfactual('What if scenario');

// Governance audit
const audit = await service.governanceAudit('Audit context');
```

### Connector Configuration

```typescript
import { ConnectorType } from '@hyba/sdk';

// Snowflake connector
{
  type: ConnectorType.SQL_SNOWFLAKE,
  host: 'acme.snowflakecomputing.com',
  database: 'finance_dw',
  schema: 'public'
}

// Kafka connector
{
  type: ConnectorType.KAFKA,
  broker: 'kafka.internal:9092',
  topic: 'market_data'
}

// S3 connector
{
  type: ConnectorType.S3,
  bucket: 'my-bucket',
  prefix: 'data/'
}

// PostgreSQL connector
{
  type: ConnectorType.SQL_POSTGRESQL,
  host: 'postgres.internal',
  database: 'analytics',
  port: 5432
}
```

### Error Handling

```typescript
import {
  HybaClient,
  AuthenticationError,
  QuotaExceededError,
  ServiceStateError,
  ValidationError
} from '@hyba/sdk';

try {
  const service = await client.provisioning.createService({...});
} catch (error) {
  if (error instanceof AuthenticationError) {
    console.error('Invalid API key');
  } else if (error instanceof QuotaExceededError) {
    console.error('Quota exceeded');
  } else if (error instanceof ServiceStateError) {
    console.error('Service in invalid state');
  } else if (error instanceof ValidationError) {
    console.error('Invalid parameters:', error.details);
  }
}
```

### Webhook Subscriptions

```typescript
// Create webhook subscription
const webhook = await client.webhooks.createSubscription({
  url: 'https://acme.com/webhooks/hyba',
  events: ['service.provisioned', 'workload.completed'],
  secret: 'whsec_...'
});

// List subscriptions
const subscriptions = await client.webhooks.listSubscriptions();

// Test webhook
const testResult = await client.webhooks.testDelivery(webhook.webhookId);

// Delete subscription
await client.webhooks.deleteSubscription(webhook.webhookId);
```

### Sandbox Environment

```typescript
// Create sandbox service (mock data, no quota)
const sandbox = await client.sandbox.createService({
  name: 'test-service',
  mode: 'mock'
});

// Execute in sandbox (returns mock results)
const result = await sandbox.execute({
  workload: 'explain',
  context: 'Test context'
});

// List available test fixtures
const fixtures = await client.sandbox.listFixtures();

// Download test data
const data = await client.sandbox.downloadFixture('portfolio_100stocks');
```

## Examples

### Real-World: Portfolio Optimization

```typescript
import { HybaClient, ConnectorType } from '@hyba/sdk';

const client = new HybaClient({ apiKey: 'hyba_live_...' });

// 1. Provision service
const service = await client.provisioning.createService({
  name: 'jpmorgan-portfolio-opt',
  tier: 'production',
  connector: {
    type: ConnectorType.SQL_SNOWFLAKE,
    host: 'acme.snowflakecomputing.com',
    database: 'finance_dw'
  }
});

// 2. Start service
await service.start();

// 3. Execute optimization
const result = await service.execute({
  workload: 'orchestrate',
  context: JSON.stringify({
    objective: 'maximize_sharpe_ratio',
    constraints: {
      min_cash_position: 0.05,
      max_sector_weight: 0.25
    },
    lookback_days: 252
  })
});

console.log('Optimized portfolio:', result.data);

// 4. Webhook notification
const webhook = await client.webhooks.createSubscription({
  url: 'https://jpmorgan.com/webhook',
  events: ['workload.completed'],
  secret: 'whsec_...'
});

// 5. Stop when done
await service.stop();
```

### Testing with Sandbox

```typescript
// Create sandbox service for testing
const sandbox = await client.sandbox.createService({
  name: 'portfolio-test',
  mode: 'mock'
});

// Execute without consuming quota or real data
const testResult = await sandbox.execute({
  workload: 'explain',
  context: 'Test'
});

console.log(testResult); // Mock data returned
```

### React Component Example

```typescript
import React, { useState, useEffect } from 'react';
import { HybaClient } from '@hyba/sdk';

export function ServiceDashboard() {
  const [client] = useState(() => new HybaClient({
    apiKey: process.env.REACT_APP_HYBA_API_KEY
  }));
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadServices = async () => {
      const list = await client.provisioning.listServices();
      setServices(list);
      setLoading(false);
    };

    loadServices();
  }, [client]);

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      {services.map(service => (
        <div key={service.serviceId}>
          <h3>{service.name}</h3>
          <p>State: {service.state}</p>
          <p>Tier: {service.serviceTier}</p>
        </div>
      ))}
    </div>
  );
}
```

## Type Safety

Full TypeScript support with complete type definitions:

```typescript
import {
  HybaClient,
  Service,
  ConnectorConfig,
  ExecutionResult,
  WebhookEvent
} from '@hyba/sdk';

const client: HybaClient = new HybaClient({ apiKey: '...' });
const service: Service = await client.provisioning.createService({...});
const result: ExecutionResult = await service.execute({...});
```

## Testing

```bash
# Run tests
npm test

# Run with coverage
npm run test:coverage

# Watch mode
npm run test:watch
```

## License

Apache License 2.0

## Support

- Documentation: https://docs.hyba.ai/typescript-sdk
- GitHub Issues: https://github.com/hyba-ai/hyba-sdk-ts/issues
- Email: support@hyba.ai

### First-class QIaaS methods

```typescript
const qi = await client.quantum_intelligence.query({ query: "Explain portfolio convexity", context: { desk: "rates" } });
const optimized = await client.quantum_intelligence.optimize({ objective: "max_sharpe", constraints: ["leverage <= 2"] });
const repair = await client.quantum_intelligence.heal({ component: "executor", mode: "salamander" });
const qaoa = await client.quantum_finance.portfolio_qaoa({ positions, riskModel: "enterprise" });
```
