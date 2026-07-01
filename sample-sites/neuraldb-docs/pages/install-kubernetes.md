---
title: Kubernetes
sort: 110
section-id: installation
keywords: Kubernetes, Helm, StatefulSet, PVC, k8s, cluster, deployment
description: Deploying NeuralDB on Kubernetes using the official Helm chart and StatefulSets
language: en
---

# Kubernetes

The recommended way to run NeuralDB on Kubernetes is via the official Helm chart. The chart deploys NeuralDB as a StatefulSet with persistent volume claims, and supports both standalone and high-availability configurations.

## Prerequisites

- Kubernetes 1.27+
- Helm 3.x
- A storage class that supports `ReadWriteOnce` PVCs (most cloud providers support this)
- At least 4 CPU cores and 8 GB RAM per NeuralDB node

## Installing the Helm Chart

```bash
# Add the NeuralDB Helm repository
helm repo add neuraldb https://charts.neuraldb.io
helm repo update

# Create a namespace
kubectl create namespace neuraldb

# Install the chart
helm install neuraldb neuraldb/neuraldb \
  --namespace neuraldb \
  --set auth.password=mysecretpassword \
  --set persistence.size=100Gi
```

## Chart Configuration

Create a `values.yaml` file for production settings:

```yaml
# values.yaml

image:
  repository: neuraldb/neuraldb
  tag: "1.0"
  pullPolicy: IfNotPresent

auth:
  # Set via --set auth.password=... or a pre-existing secret
  existingSecret: ""
  secretKey: "neuraldb-password"

replicaCount: 1          # primary nodes (use 1 for standalone)
readReplicaCount: 2      # read replicas

resources:
  requests:
    cpu: "2"
    memory: "8Gi"
  limits:
    cpu: "8"
    memory: "32Gi"

persistence:
  enabled: true
  storageClass: "fast-ssd"    # use a fast SSD storage class
  size: 500Gi
  walSize: 50Gi               # separate PVC for WAL

vectorBuffer: "16Gi"          # memory for HNSW index
sharedBuffers: "8Gi"          # row store page cache
maxConnections: 200

service:
  type: ClusterIP
  port: 5432

# High-availability configuration
ha:
  enabled: true
  replication:
    mode: synchronous          # 'synchronous' or 'asynchronous'
    synchronousCommit: "on"

backup:
  enabled: true
  schedule: "0 2 * * *"
  s3:
    bucket: my-neuraldb-backups
    region: us-east-1
    existingSecret: aws-credentials

monitoring:
  enabled: true
  serviceMonitor:
    enabled: true              # requires Prometheus Operator
```

Apply the values:

```bash
helm install neuraldb neuraldb/neuraldb \
  --namespace neuraldb \
  -f values.yaml \
  --set auth.password=$(openssl rand -base64 32)
```

## StatefulSet Details

The chart deploys a `StatefulSet` with:

- One pod per replica (primary + read replicas)
- Two PVCs per pod: data volume and WAL volume
- An init container that configures replication on startup

```yaml
# Example pod spec (simplified)
spec:
  containers:
  - name: neuraldb
    image: neuraldb/neuraldb:1.0
    ports:
    - containerPort: 5432
    resources:
      requests:
        memory: "8Gi"
        cpu: "2"
    volumeMounts:
    - name: data
      mountPath: /var/lib/neuraldb/data
    - name: wal
      mountPath: /var/lib/neuraldb/wal
    livenessProbe:
      exec:
        command: ["pg_isready", "-U", "neuraldb"]
      initialDelaySeconds: 30
      periodSeconds: 10
    readinessProbe:
      exec:
        command: ["pg_isready", "-U", "neuraldb"]
      initialDelaySeconds: 5
      periodSeconds: 5
```

## Services

The chart creates three Kubernetes services:

| Service | Type | Port | Description |
|---------|------|------|-------------|
| `neuraldb-primary` | ClusterIP | 5432 | Primary — reads + writes |
| `neuraldb-replica` | ClusterIP | 5432 | Read replicas — reads only |
| `neuraldb-headless` | Headless | 5432 | For StatefulSet pod discovery |

Connect to the primary:

```bash
kubectl port-forward svc/neuraldb-primary 5432:5432 -n neuraldb
psql -h localhost -U neuraldb
```

## Persistent Volume Claims

Each pod gets two PVCs:

```yaml
volumeClaimTemplates:
- metadata:
    name: data
  spec:
    accessModes: ["ReadWriteOnce"]
    storageClassName: fast-ssd
    resources:
      requests:
        storage: 500Gi
- metadata:
    name: wal
  spec:
    accessModes: ["ReadWriteOnce"]
    storageClassName: fast-ssd
    resources:
      requests:
        storage: 50Gi
```

Use a **fast-ssd** storage class (AWS `gp3`, GCP `pd-ssd`, Azure `Premium_LRS`) for the data and WAL volumes. Spinning disks are not supported in production.

## Secrets Management

Store the NeuralDB password in a Kubernetes secret:

```bash
kubectl create secret generic neuraldb-credentials \
  --namespace neuraldb \
  --from-literal=password=$(openssl rand -base64 32)
```

Reference it in `values.yaml`:

```yaml
auth:
  existingSecret: neuraldb-credentials
  secretKey: password
```

For larger installations, use an external secrets manager (HashiCorp Vault, AWS Secrets Manager) with the External Secrets Operator.

## Scaling Read Replicas

Scale the number of read replicas without downtime:

```bash
helm upgrade neuraldb neuraldb/neuraldb \
  --namespace neuraldb \
  --set readReplicaCount=4
```

The new replica pods will join the replication stream automatically.

## Upgrading

```bash
helm repo update
helm upgrade neuraldb neuraldb/neuraldb \
  --namespace neuraldb \
  -f values.yaml \
  --set auth.existingSecret=neuraldb-credentials
```

The upgrade performs a rolling update — replicas are updated first, then the primary.
