# Resource Profiles

AWS-style resource allocation profiles for Kubernetes workloads.

## Available Profiles
### Processing Intensive - 2:1 CPU:Memory
**Best for:** Video transcoding, image processing, mathematical computations, ML inference

| Size | CPU Request | Memory Request | CPU Limit | Memory Limit | Use Case |
|------|-------------|----------------|-----------|--------------|----------|
| `p.pico` | 100m | 64Mi | 250m | 128Mi | Tiny processing tasks |
| `p.nano` | 200m | 128Mi | 500m | 256Mi | Minimal processing |
| `p.micro` | 300m | 192Mi | 1 | 512Mi | Light computations |
| `p.small` | 500m | 256Mi | 2 | 1Gi | Light media processing |
| `p.medium` | 1 | 512Mi | 4 | 2Gi | Video processing |
| `p.large` | 2 | 1Gi | 8 | 4Gi | Heavy computational tasks |
| `p.xlarge` | 4 | 2Gi | 16 | 8Gi | Batch processing |
| `p.2xlarge` | 8 | 4Gi | 32 | 16Gi | Large-scale processing |

### Burstable - 1:1 CPU:Memory
**Best for:** Web servers, APIs, general-purpose applications

| Size | CPU Request | Memory Request | CPU Limit | Memory Limit | Use Case |
|------|-------------|----------------|-----------|--------------|----------|
| `t.pico` | 25m | 32Mi | 100m | 128Mi | Tiny services |
| `t.nano` | 50m | 64Mi | 200m | 256Mi | Micro services |
| `t.micro` | 100m | 128Mi | 500m | 512Mi | Small utilities |
| `t.small` | 250m | 256Mi | 1 | 1Gi | Web frontends |
| `t.medium` | 500m | 512Mi | 2 | 2Gi | API services |
| `t.large` | 1 | 1Gi | 4 | 4Gi | Medium applications |
| `t.xlarge` | 2 | 2Gi | 8 | 8Gi | Large applications |
| `t.2xlarge` | 4 | 4Gi | 16 | 16Gi | High-scale services |

### Compute Optimized - 1:2 CPU:Memory
**Best for:** CPU-intensive applications, web servers with moderate memory needs

| Size | CPU Request | Memory Request | CPU Limit | Memory Limit | Use Case |
|------|-------------|----------------|-----------|--------------|----------|
| `c.pico` | 100m | 256Mi | 250m | 512Mi | Tiny compute tasks |
| `c.nano` | 150m | 384Mi | 500m | 1Gi | Small compute jobs |
| `c.micro` | 200m | 512Mi | 750m | 1.5Gi | Light compute workloads |
| `c.small` | 250m | 512Mi | 1 | 2Gi | Load balancers |
| `c.medium` | 500m | 1Gi | 2 | 4Gi | Application servers |
| `c.large` | 1 | 2Gi | 4 | 8Gi | High-traffic APIs |
| `c.xlarge` | 2 | 4Gi | 8 | 16Gi | Compute clusters |
| `c.2xlarge` | 4 | 8Gi | 16 | 32Gi | Heavy compute workloads |

### Memory Optimized - 1:4 CPU:Memory
**Best for:** Applications with moderate memory requirements

| Size | CPU Request | Memory Request | CPU Limit | Memory Limit | Use Case |
|------|-------------|----------------|-----------|--------------|----------|
| `m.pico` | 100m | 512Mi | 250m | 1Gi | Tiny memory apps |
| `m.nano` | 150m | 768Mi | 500m | 2Gi | Small memory workloads |
| `m.micro` | 200m | 1Gi | 750m | 3Gi | Light memory apps |
| `m.small` | 250m | 1Gi | 1 | 4Gi | Small databases |
| `m.medium` | 500m | 2Gi | 2 | 8Gi | Application caches |
| `m.large` | 1 | 4Gi | 4 | 16Gi | Medium databases |
| `m.xlarge` | 2 | 8Gi | 8 | 32Gi | Large applications |
| `m.2xlarge` | 4 | 16Gi | 16 | 64Gi | High-memory applications |

### Memory Intensive - 1:8 CPU:Memory
**Best for:** In-memory databases, caches, analytics, large datasets

| Size | CPU Request | Memory Request | CPU Limit | Memory Limit | Use Case |
|------|-------------|----------------|-----------|--------------|----------|
| `r.pico` | 100m | 1Gi | 250m | 2Gi | Tiny cache instances |
| `r.nano` | 150m | 1536Mi | 500m | 4Gi | Small memory stores |
| `r.micro` | 200m | 2Gi | 750m | 6Gi | Light memory-intensive apps |
| `r.small` | 250m | 2Gi | 1 | 8Gi | Cache instances |
| `r.medium` | 500m | 4Gi | 2 | 16Gi | Search engines |
| `r.large` | 1 | 8Gi | 4 | 32Gi | Large databases |
| `r.xlarge` | 2 | 16Gi | 8 | 64Gi | Big data analytics |
| `r.2xlarge` | 4 | 32Gi | 16 | 128Gi | Massive memory workloads |

## Usage

Add the resource profile label to your workload:

```yaml
metadata:
  labels:
    resource-profile: m.medium
```

Then include this component in your kustomization:

```yaml
components:
  - ../../_components/resource-profiles
```
