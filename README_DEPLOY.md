# Deployment & Architecture Guide

This document describes the production serverless inference scoring architecture implemented for the Milliman IntelliScript Machine Learning Engineer assessment.

It covers:

- System architecture
- Container packaging
- Infrastructure and CI/CD workflows
- Deployment procedures
- Operational verification
- Production scaling considerations

---

# System Architecture

The scoring engine uses a decoupled, serverless container architecture designed for:

- Elastic scaling
- Zero idle compute cost
- Secure operational boundaries
- Containerized ML dependency management

## Architecture Overview

```text
Client HTTP POST
        │
        ▼
┌─────────────────────────────┐
│ Amazon API Gateway v2       │
│ POST /predict               │
└─────────────────────────────┘
        │
        │ (VPC Link / Private Routing + JWT Auth [Future State])
        ▼
┌─────────────────────────────┐
│ AWS Lambda Container        │
│ Inference Handler           │
└─────────────────────────────┘
        │
        │ Lazy-loaded global cache
        ▼
┌─────────────────────────────┐
│ Cached Model Artifacts      │
├─────────────────────────────┤
│ scaler.joblib               │
│ linear.joblib               │
│ ridge.joblib                │
│ random_forest.joblib        │
└─────────────────────────────┘
```

## Request Flow Components

### 1. Edge Perimeter

An **AWS API Gateway v2 (HTTP API)** exposes a unified endpoint:

```text
POST /predict
```

Responsibilities:

- HTTP request parsing
- Payload unwrapping
- Request routing
- Ingress monitoring

### 2. Compute Layer

**AWS Lambda** provides isolated serverless execution.

Container packaging avoids traditional ZIP deployment limitations and supports heavier ML dependencies such as:

- `scikit-learn`
- `pandas`
- `mlflow`

### 3. Lazy-Loaded Model Cache

To reduce cold-start penalties while preserving runtime flexibility:

- `scaler.joblib`
- preprocessing assets
- trained model weights

are loaded lazily into Lambda global memory only when required.

This allows warm containers to reuse cached model state across requests.

---

# Container Packaging

The deployment image uses a **multi-stage Docker build** to:

- Reduce image size
- Maximize layer caching
- Improve build performance
- Enforce non-root execution

## Docker Build Stages

### Stage 1 — Base Runtime

Uses the official:

```text
AWS Lambda Python 3.12 base image
```

This stage:

- Installs `uv`
- Updates system packages via `dnf`
- Builds shared production dependencies

### Stage 2 — Test Environment

Adds:

- `awslambdaric`
- local model artifacts
- Lambda Runtime Interface Emulator

Used exclusively for:

- CI validation
- Local Lambda simulation
- Integration testing

without touching cloud infrastructure.

### Stage 3 — Production Runtime

Creates the final hardened runtime by:

- Copying application packages
- Adding model binaries
- Removing build tooling
- Enforcing non-root execution

```dockerfile
USER appuser
```

## Workspace Hygiene (`.dockerignore`)

The runtime image excludes unnecessary artifacts such as:

```text
tests/
log/
prepare/
scripts/
src/ml_engineer_exam/model/
```

This prevents:

- Layer bloat
- Unused training logic
- Temporary file leakage

---

# CI/CD Pipeline

Deployment is automated through progressive **GitHub Actions** workflows.

## Pipeline Flow

```text
lint
  ↓
python_tests
  ↓
security_scans
  ↓
infrastructure
  ↓
build_verify_push
  ↓
deploy
  ↓
smoke_test_production
```

## Workflow Gates

### `lint`

Code quality enforcement using:

- `ruff`
- import ordering
- formatting validation

---

### `python_tests`

Runs:

- unit tests
- integration tests
- model precision verification

Git-LFS smudging is intentionally bypassed to avoid platform billing issues.

Serialized model assets are downloaded directly via:

```bash
curl
```

from Hugging Face storage.

---

### `security_scans`

Performs:

**SAST**

- Semgrep

**Dependency / filesystem scanning**

- Trivy

---

### `infrastructure`

Validates infrastructure and executes:

```bash
tofu plan
```

during Pull Requests.

---

### `build_verify_push`

This stage:

1. Builds the emulator image
2. Downloads model binaries
3. Launches a local container
4. Executes runtime smoke tests
5. Pushes validated images to ECR

---

### `deploy`

Applies infrastructure updates and deploys the production Lambda image.

---

### `smoke_test_production`

Executes live synthetic API requests to confirm:

- endpoint availability
- runtime functionality
- deployment success

---

## Security Scan Failure Policy

> ⚠️ **Assessment Scope Note**
>
> For this assessment repository, selected security scans use:
>
> ```yaml
> continue-on-error: true
> ```
>
> This prevents upstream vulnerability database volatility from blocking reviewer builds.
>
> In production environments, these settings should be removed and replaced with hard-failing gates:
>
> ```text
> exit-code: 1
> ```
>
> so that high or critical vulnerabilities immediately fail the pipeline.

---

# Reviewer Deployment Guide

This repository supports self-contained deployment into a reviewer-owned AWS account.

## Prerequisites

You will need:

- AWS account with administrator access
- Fork of this GitHub repository

---

## Step 1 — Configure AWS Secrets

Navigate to:

```text
Settings → Secrets and variables → Actions
```

Create:

```text
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
```

using your AWS credentials.

---

## Step 2 — Trigger Deployment

The CI/CD pipeline includes a **self-healing bootstrap process**.

On first execution it:

1. Audits AWS backend state
2. Detects missing OpenTofu infrastructure
3. Automatically provisions:

- remote state bucket
- DynamoDB lock table

before continuing deployment.

### Deployment Flow

1. Create a feature branch
2. Commit any change
3. Open a Pull Request into `main`
4. Observe PR checks:

- lint
- tests
- scans
- `tofu plan`

5. Merge into `main`

A merge automatically triggers:

- container build
- Lambda update
- infrastructure rollout
- public endpoint deployment

---

## Step 3 — Full Teardown

A standalone workflow performs complete infrastructure cleanup.

Navigate to:

```text
Actions
→ Infra: Force Teardown (Absolute Decommission)
```

Then:

1. Click **Run workflow**
2. Enter:

```text
DESTROY
```

3. Execute

The workflow removes:

- API Gateway
- Lambda
- ECR images
- S3 state bucket
- DynamoDB locks

leaving zero residual infrastructure.

---

# Deployment Verification

After deployment completes, GitHub Actions generates a deployment summary.

## API Verification

Retrieve the endpoint URL from the:

```text
GitHub Actions Summary
```

and run:

```bash
bash src/ml_engineer_exam/scripts/post_deploy.sh \
https://your-endpoint-id.execute-api.us-east-1.amazonaws.com/predict
```

This validates all three deployed models.

---

# Runtime Performance

Two execution states should be expected.

## Cold Start (~10–15s)

The first request initializes:

- Python runtime
- scaler
- preprocessing artifacts
- all model weights

Expected latency:

```text
10–15 seconds
```

This remains within the configured Lambda timeout.

---

## Warm Runtime (<100ms)

After initialization:

- models remain cached
- disk access is avoided
- prediction latency becomes minimal

Typical response:

```text
<100 ms
```

---

# Production Scaling Roadmap

Future enterprise improvements could include:

## 1. VPC Isolation

Move Lambda execution into:

- private subnets
- isolated networking boundaries

using:

- AWS VPC Link

to prevent public exposure.

---

## 2. Model Endpoint Decoupling

Split the unified handler into dedicated endpoints:

```text
/predict/linear
/predict/ridge
/predict/random-forest
```

Benefits:

- reduced cold starts
- smaller memory footprints
- independent scaling
- improved runtime efficiency