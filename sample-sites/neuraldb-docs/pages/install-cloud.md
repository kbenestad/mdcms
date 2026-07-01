---
title: Cloud Managed
sort: 120
section-id: installation
keywords: cloud, managed, NeuralDB Cloud, regions, tiers, SaaS
description: Setting up NeuralDB Cloud — the fully managed service with global regions and flexible tiers
language: en
---

# Cloud Managed

NeuralDB Cloud is the fully managed version of NeuralDB. It handles provisioning, patching, backups, monitoring, and scaling — so you can focus on building your application rather than managing database infrastructure.

## Getting Started

### 1. Create an Account

Sign up at [cloud.neuraldb.io](https://cloud.neuraldb.io). You can authenticate with Google, GitHub, or an email address.

### 2. Create a Cluster

Click **New Cluster** and configure:

- **Region**: choose the cloud region closest to your application servers
- **Tier**: select based on your workload requirements (see tier comparison below)
- **Storage**: initial storage allocation (can be scaled later)
- **High Availability**: enable for production workloads

### 3. Connect

Once the cluster is provisioned (typically under 3 minutes), your connection string appears in the dashboard:

```
postgresql://neuraldb:[password]@[cluster-id].cloud.neuraldb.io:5432/[database]?sslmode=require
```

Use this with any PostgreSQL-compatible driver or psql:

```bash
psql "postgresql://neuraldb:mypassword@abc123.cloud.neuraldb.io:5432/mydb?sslmode=require"
```

## Available Regions

NeuralDB Cloud is available in the following regions:

| Region | Cloud Provider | Availability |
|--------|---------------|-------------|
| us-east-1 (N. Virginia) | AWS | GA |
| us-west-2 (Oregon) | AWS | GA |
| eu-west-1 (Ireland) | AWS | GA |
| eu-central-1 (Frankfurt) | AWS | GA |
| ap-northeast-1 (Tokyo) | AWS | GA |
| ap-southeast-1 (Singapore) | AWS | GA |
| us-central1 (Iowa) | GCP | Beta |
| europe-west4 (Netherlands) | GCP | Beta |
| eastus (Virginia) | Azure | Beta |

Multi-region replication (primary in one region, read replicas in others) is available on Business and Enterprise tiers.

## Pricing Tiers

### Starter

Free tier for development and experimentation.

| Resource | Limit |
|---------|-------|
| Storage | 5 GB |
| Vector dimensions | Up to 1536 |
| Max connections | 10 |
| PITR | No |
| HA | No |
| SLA | No |

The Starter tier automatically suspends after 7 days of inactivity and resumes on the next connection (cold start: ~30 seconds).

### Developer

$29/month — for side projects and pre-production environments.

| Resource | Limit |
|---------|-------|
| vCPU | 2 dedicated |
| RAM | 8 GB |
| Storage | 100 GB NVMe SSD |
| Connections | 100 |
| PITR | 7 days |
| HA | No |

### Business

$199/month — for production workloads.

| Resource | Limit |
|---------|-------|
| vCPU | 8 dedicated |
| RAM | 32 GB |
| Storage | 500 GB NVMe SSD (expandable) |
| Connections | 500 |
| PITR | 30 days |
| HA | Yes (1 standby) |
| Read replicas | Up to 3 |
| SLA | 99.95% |

### Business Plus

$599/month — for large-scale production workloads.

| Resource | Limit |
|---------|-------|
| vCPU | 32 dedicated |
| RAM | 128 GB |
| Storage | 2 TB NVMe SSD (expandable) |
| Connections | 2,000 |
| PITR | 30 days |
| HA | Yes (2 standbys) |
| Read replicas | Up to 10 |
| Multi-region replicas | Yes |
| SLA | 99.99% |

### Enterprise

Custom pricing — for mission-critical applications with specific compliance requirements.

- Dedicated infrastructure (no multi-tenancy)
- Custom SLAs
- Private endpoints (AWS PrivateLink, GCP Private Service Connect)
- SOC 2 Type II, HIPAA, and ISO 27001 compliance
- Dedicated support with SLA

## Connecting from Your Application

### Connection Pooling

NeuralDB Cloud includes PgBouncer-based connection pooling. Use the pooler endpoint for serverless and short-lived connections:

```
postgresql://neuraldb:[password]@[cluster-id]-pooler.cloud.neuraldb.io:5432/[database]
```

| Connection type | Endpoint suffix | Use for |
|----------------|----------------|---------|
| Direct | (none) | Long-lived connections, COPY operations |
| Transaction pooling | `-pooler` | Serverless, short-lived connections |
| Session pooling | `-session-pooler` | Prepared statements |

### IP Allow-listing

Restrict access to specific IP ranges in the **Security** tab of your cluster dashboard. Enter your application servers' CIDR ranges (e.g., `10.0.0.0/8` for private VPC, or specific public IPs).

### SSL/TLS

All connections require TLS. Download the cluster CA certificate from the dashboard and verify it in your connection string:

```
sslmode=verify-full&sslrootcert=/path/to/ca.pem
```

## Monitoring and Alerting

NeuralDB Cloud includes a built-in monitoring dashboard with:

- Query throughput and latency percentiles (p50, p95, p99)
- Connection count
- Storage usage
- Vector index size
- Replication lag

Configure alerts for:
- Storage > 80% full
- Average query latency > 500ms
- Replication lag > 30s
- Failed connections

Metrics are also available via the NeuralDB Cloud API for ingestion into your own monitoring stack (Datadog, Grafana Cloud, New Relic).

## Branching (Database Branches)

NeuralDB Cloud supports **branching** — create an instant copy-on-write clone of your production database for development, testing, or migrations:

```bash
neuraldb-cloud branch create staging --from production
```

Branches share storage pages with the parent until they diverge (copy-on-write). A branch of a 100 GB database costs storage only for the pages that change.
