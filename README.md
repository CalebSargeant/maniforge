# Maniforge

**A Terraform-like tool for Kubernetes applications**

Transform simple app definitions into production-ready Kubernetes manifests using the power of bjw-s-app-template.

## 📦 Installation

### Quick Install (macOS/Linux)

```bash
curl -L https://github.com/calebsargeant/maniforge/releases/latest/download/maniforge-$(uname -s | tr '[:upper:]' '[:lower:]')-$(uname -m) -o maniforge
chmod +x maniforge
sudo mv maniforge /usr/local/bin/
```

### Homebrew

```bash
brew tap calebsargeant/tap
brew install maniforge
```

### Build from Source

```bash
git clone https://github.com/calebsargeant/maniforge.git
cd maniforge
./build.sh
sudo cp dist/maniforge /usr/local/bin/
```

## 🎯 Philosophy

Instead of writing complex Kubernetes YAML, define apps like Docker Compose and let Maniforge handle the Kubernetes complexity.

**No Python required** - maniforge is distributed as a universal executable!

## 🚀 Quick Start

### 1. Initialize a New Project

```bash
./maniforge init --cluster my-cluster
```

This creates a `maniforge.yaml` with an example app.

### 2. Plan Your Changes

```bash
./maniforge plan
```

See what Maniforge will create (like `terraform plan`):

```
📋 Plan: 1 changes

  🟢 nginx-example
      App will be created
      Image: nginx:latest
      Namespace: default
```

### 3. Apply Changes

```bash
./maniforge apply
```

Generates Kubernetes manifests in the `apps/` directory.

### 4. Deploy with GitOps

```bash
git add apps/
git commit -m "Deploy apps with Maniforge"
git push  # Flux/ArgoCD picks up changes
```

## 📋 Configuration Format

**`maniforge.yaml`** - Your infrastructure as code (single file):

```yaml
cluster:
  name: homelab
  domain: sargeant.co
  defaults:
    profile: c.small
    nodeSelector: pi

output:
  directory: apps

nodes:
  pi:
    count: 2
    cpu: 4
    mem: 16Gi

apps:
  homebridge:
    image: ghcr.io/homebridge/homebridge:latest
    type: daemonset
    network: host
    profile: c.pico
    storage:
      config:
        type: hostPath
        path: /mnt/nvme/homebridge-config
        mount: /homebridge
    env:
      TZ: Europe/Amsterdam
  
  plex:
    image: plexinc/pms-docker:latest
    type: deployment
    network: nodeport
    profile: r.large
    ports:
      - name: plex
        port: 32400
        nodePort: 32400
    storage:
      config:
        type: hostPath
        path: /mnt/raid/plex-config
        mount: /config
      media:
        type: hostPath
        path: /mnt/raid/media
        mount: /data
        readonly: true
    env:
      PLEX_CLAIM: token-123456789

  postgres:
    image: postgres:15
    type: deployment
    network: clusterip
    profile: m.small
    storage:
      data:
        type: pvc
        size: 20Gi
        mount: /var/lib/postgresql/data
        storageClass: fast-ssd
    env:
      POSTGRES_DB: myapp
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: secret
```

## 🔧 Commands

### Initialize
```bash
./maniforge init [--cluster name]
```
Create a new project with example configuration.

### Plan
```bash
./maniforge plan
```
Show what changes would be made (like `terraform plan`).

### Apply
```bash
./maniforge apply
```
Generate/update Kubernetes manifests.

### Validate
```bash
./maniforge validate
```
Check configuration for errors.

## 📖 App Configuration Reference

### Required Fields
```yaml
apps:
  myapp:
    image: nginx:latest          # Docker image (required)
```

### Optional Fields
```yaml
    # Workload type
    type: deployment             # deployment|daemonset|statefulset (default: deployment)
    
    # Networking
    network: clusterip           # clusterip|nodeport|loadbalancer|host (default: clusterip)
    ports:                       # Custom ports (for nodeport/loadbalancer)
      - name: web
        port: 80
        targetPort: 8080
        nodePort: 30080          # Only for nodeport
    
    # Resources & Placement
    profile: c.small             # Resource profile (default: from cluster.defaults)
    nodeSelector: pi             # Node selector (default: from cluster.defaults)
    namespace: default           # Kubernetes namespace (default: default)
    
    # Storage
    storage:
      data:
        type: pvc                # pvc|hostPath|nfs
        size: 10Gi              # PVC size (required for pvc)
        mount: /data            # Container mount path
        storageClass: fast      # Storage class (optional)
        readonly: false         # Read-only mount (default: false)
      
      config:
        type: hostPath
        path: /host/path/to/config
        mount: /config
    
    # Environment
    env:
      TZ: Europe/Amsterdam
      DEBUG: "true"
    
    # Ingress (automatic if cluster.domain is set)
    ingress: false               # Disable ingress (default: true if domain set)
```

## 🏗️ Resource Profiles

Maniforge uses `resource-profiles.yaml` as the master definition for all AWS-style resource allocation profiles. It defines CPU and memory requests/limits for different workload types.

### Profile Types

- **P-type** (2:1 CPU:Memory) - Video transcoding, image processing, ML inference
- **T-type** (1:1 CPU:Memory) - Web servers, APIs, general-purpose applications
- **C-type** (1:2 CPU:Memory) - Compute-optimized, load balancers
- **M-type** (1:4 CPU:Memory) - Memory-optimized, balanced workloads
- **R-type** (1:8 CPU:Memory) - In-memory databases, caches, large datasets

### Profile Sizes

Each type has 8 sizes: `pico`, `nano`, `micro`, `small`, `medium`, `large`, `xlarge`, `2xlarge`

### Built-in Profiles

| Profile | CPU Requests | CPU Limits | Memory Requests | Memory Limits | Use Case |
|---------|-------------|------------|-----------------|---------------|----------|
| `c.pico` | 100m | 250m | 256Mi | 512Mi | Tiny apps |
| `c.small` | 250m | 500m | 512Mi | 1Gi | Small apps |
| `c.medium` | 500m | 1000m | 1Gi | 2Gi | Medium apps |
| `r.large` | 500m | 1000m | 4Gi | 8Gi | Memory-intensive |

### Master Definition File

The `resource-profiles.yaml` file:
- Defines all available resource profiles with CPU/memory requests and limits
- Can be used to generate Kubernetes component structures
- Is automatically loaded by maniforge for app configuration
- Can be customized by users for their own profile definitions

### Generating Kubernetes Components

```bash
./maniforge generate-profiles --output /path/to/output
```

This generates:
- Main `kustomization.yaml` with all profile patches
- Individual profile directories (e.g., `c.small/`, `r.large/`) containing:
  - `kustomization.yaml`: Component definition
  - `patches.yaml`: Resource patches for Deployments/StatefulSets/DaemonSets
  - `helmrelease-patches.yaml`: Patches for Flux HelmRelease resources
- `README.md`: Documentation of all available profiles

### Using Custom Resource Profiles

Users can create their own `resource-profiles.yaml` and generate components:

```bash
./maniforge generate-profiles --profiles-yaml custom-profiles.yaml --output my-components/
```

### Using Generated Components

**Label-based Selection** (Main Component):
```yaml
components:
  - /path/to/components/resource-profiles
```
Then add profile labels to your resources:
```yaml
labels:
  resource-profile: c.small
```

**Direct Component Reference**:
```yaml
components:
  - /path/to/components/resource-profiles/c.small
```

## 🌐 Network Types

| Type | Description | Use Case |
|------|-------------|----------|
| `clusterip` | Cluster-internal access only | Internal services, databases |
| `nodeport` | External access via node ports | Development, specific port requirements |
| `loadbalancer` | External LoadBalancer service | Production external services |
| `host` | Host networking | HomeAssistant, network-sensitive apps |

## 📁 Storage Types

| Type | Configuration | Use Case |
|------|---------------|----------|
| `pvc` | `size`, `storageClass`, `accessMode` | Persistent data, databases |
| `hostPath` | `path` | Host directory mounts |
| `nfs` | `server`, `path` | Shared storage |

## 🔄 Generated Structure

Maniforge creates a clean structure:

```
apps/
├── homebridge/
│   ├── kustomization.yaml      # Kustomize config
│   └── helm-release.yaml       # HelmRelease with bjw-s-app-template
└── plex/
    ├── kustomization.yaml
    └── helm-release.yaml
```

Each app gets its own directory with:
- **`kustomization.yaml`** - Kustomize configuration
- **`helm-release.yaml`** - Complete HelmRelease using bjw-s-app-template

## 🎨 Benefits

✅ **Terraform-like Workflow** - Plan, apply, version control  
✅ **Simple Configuration** - Docker Compose-like syntax  
✅ **Powerful Output** - Full Kubernetes capabilities via bjw-s-app-template  
✅ **GitOps Ready** - Generated manifests work with Flux/ArgoCD  
✅ **Validation** - Catch errors before deployment  
✅ **Diff-Aware** - Shows exactly what changed  

## 🚦 Workflow

1. **Edit** `maniforge.yaml` (your infrastructure as code)
2. **Plan** with `./maniforge plan` (see what will change)
3. **Apply** with `./maniforge apply` (generate manifests)
4. **Commit** generated files to git
5. **Deploy** automatically via GitOps

## 📊 Example Workflow

```bash
# Initialize new project
./maniforge init --cluster homelab

# Edit maniforge.yaml to add your apps
vim maniforge.yaml

# See what will be created
./maniforge plan

# Generate manifests
./maniforge apply

# Deploy via GitOps
git add apps/ maniforge.yaml
git commit -m "Add homebridge and plex"
git push
```

## 🔄 GitHub Action

Use maniforge in CI/CD workflows:

```yaml
name: Validate Manifests
on: [pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Validate maniforge config
        uses: calebsargeant/maniforge@v1
        with:
          command: validate
          config: maniforge.yaml
      
      - name: Plan changes
        uses: calebsargeant/maniforge@v1
        with:
          command: plan
          config: maniforge.yaml
```

**Inputs:**
- `command` - Command to run: `plan`, `apply`, `validate`, `init` (default: `plan`)
- `config` - Path to config file (default: `maniforge.yaml`)
- `version` - Version to use (default: `latest`)

**Outputs:**
- `exit-code` - Command exit code
- `changes-detected` - Whether changes were detected (plan only)

## 🛠️ Development

### Building

```bash
./build.sh  # Creates dist/maniforge executable
```

### Releasing

Releases are automatic using semantic versioning. Use conventional commits:

```bash
# Features (bumps minor version)
git commit -m "feat: add new storage type support"

# Fixes (bumps patch version)
git commit -m "fix: resolve port mapping issue"

# Breaking changes (bumps major version)
git commit -m "feat!: redesign configuration format"

# Push to main - automatic release triggers
git push origin main
```

The workflow automatically:
1. Determines version based on commits
2. Creates git tag and GitHub release
3. Builds binaries for all platforms
4. Uploads binaries + SHA256SUMS
5. Generates CHANGELOG.md

Download SHA256SUMS from release and update `maniforge.rb` checksums.

### Homebrew Tap Setup

```bash
# Create homebrew-tap repo
mkdir homebrew-tap && cd homebrew-tap
mkdir Formula
cp ../maniforge.rb Formula/maniforge.rb
git init && git add . && git commit -m "Add maniforge"
git remote add origin git@github.com:calebsargeant/homebrew-tap.git
git push -u origin main
```

## 📊 Capacity Planning

Maniforge now includes built-in capacity planning that analyzes resource usage across your node groups!

When you run `maniforge plan`, you'll see:
- **CPU and Memory usage** per node type
- **Visual progress bars** showing capacity utilization
- **Requests vs Limits** analysis
- **Over-capacity warnings** when limits exceed node capacity
- **Per-app resource breakdown**

### Node Capacity Configuration

Define capacity at the top level in `maniforge.yaml`:

```yaml
nodes:
  pi:
    count: 2      # number of nodes of this type
    cpu: 4        # per-node CPU (cores or millicores, e.g. 4000m)
    mem: 16Gi     # per-node memory (alias: memory)
    disk: 100Gi   # optional, informational
```

### Example Output

```
📊 Capacity Planning Analysis
================================================================================

🖥️  Node Type: pi
   Apps: 3
   Node Capacity: CPU=4.00 Memory=8.00Gi

   CPU Usage:
     Requests: 850m / 4.00 (21.2%)
       [████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]
     Limits:   1.75 / 4.00 (43.8%)
       [█████████████████░░░░░░░░░░░░░░░░░░░░░░░]

   Memory Usage:
     Requests: 4.75Gi / 8.00Gi (59.4%)
       [███████████████████████░░░░░░░░░░░░░░░░░]
     Limits:   9.50Gi / 8.00Gi (118.8%)
     ⚠️ [████████████████████████████████████████]

   ✅ Capacity available (40.6% free)

   Apps on this node type:
     • homebridge: CPU=100m Memory=256.00Mi
     • plex: CPU=500m Memory=4.00Gi
     • nginx: CPU=250m Memory=512.00Mi
```

### Capacity Assumptions

**Important:** Maniforge currently assumes 1 replica per node for capacity planning calculations. This is the typical pattern for:
- **DaemonSets** - Run exactly one pod per node
- **Node-pinned deployments** - Deployments with specific node selectors that spread across nodes

**Limitations:**
- If you have multi-replica deployments targeting the same node type, the capacity analysis will undercount resource usage
- Future versions may support configurable replica counts or cluster state inspection

**Best Practice:** Use capacity planning as a guideline for node sizing and to identify potential over-allocation. Always monitor actual cluster resource usage in production.

## 🔮 Future Features

- 🌍 **Remote Platforms** - Load profiles from GitHub repos
- 🔄 **Live Diffing** - Compare with running cluster state
- 📦 **App Templates** - Pre-built app configurations
- 🎛️ **Advanced Networking** - Service mesh, network policies

---

**Maniforge** - Because Kubernetes apps should be as easy as `docker run`.
