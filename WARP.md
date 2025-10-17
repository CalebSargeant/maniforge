# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Overview

Maniforge is a Terraform-like tool for managing Kubernetes applications. It translates simple app definitions (similar to Docker Compose) into production-ready Kubernetes manifests using the bjw-s-app-template Helm chart and Flux HelmRelease format.

## Key Commands

### Development
```bash
./maniforge init --cluster my-cluster   # Initialize new project with example config
./maniforge validate                    # Validate configuration only
./maniforge plan                        # Show changes (like terraform plan)
./maniforge apply                       # Generate manifests (like terraform apply)
```

### Installation
```bash
./install.sh                            # Install globally to /usr/local/bin
```

### Testing
Execute the tool directly on test configurations:
```bash
./maniforge --config test-config.yaml plan
```

## Architecture

### Core Components

**Maniforge class** (`maniforge` script, lines 377-580)
- Main orchestrator handling command execution
- Loads `maniforge.yaml` configuration and platform configuration
- Provides default platform config with resource profiles, network types, and node selectors
- Commands: `init`, `plan`, `apply`, `validate`

**AppTranslator class** (lines 163-375)
- Translates high-level app config to bjw-s-app-template Helm values format
- Key methods:
  - `translate_image()`: Converts image strings to repository:tag format
  - `translate_network()`: Converts network types (clusterip/nodeport/host) to service configuration
  - `translate_storage()`: Converts storage config (pvc/hostPath/nfs) to persistence volumes
  - `translate_resources()`: Applies resource profiles (c.pico, c.small, r.large, etc.)
  - `translate_node_selector()`: Converts node selector names to Kubernetes nodeSelector labels
  - `translate_ingress()`: Generates ingress with automatic subdomain based on app name
  - `translate_app()`: Main orchestrator that deep-merges all configurations

**ManifestDiffer class** (lines 19-161)
- Implements Terraform-like plan functionality
- Compares current state (existing helm-release.yaml files) vs desired state
- Detects create/update/delete operations
- Displays changes in user-friendly format with emoji indicators

### Configuration Flow

1. **Input**: `maniforge.yaml` contains platform settings, cluster config, and app definitions
2. **Translation**: AppTranslator converts high-level configs to bjw-s-app-template values
3. **Generation**: Creates directory structure under `apps/` with:
   - `kustomization.yaml`: Kustomize configuration referencing helm-release
   - `helm-release.yaml`: FluxCD HelmRelease with translated values
4. **GitOps**: Generated manifests are committed and deployed by Flux/ArgoCD

### Key Design Patterns

- **Deep merge**: Configurations are layered (profile + nodeSelector + network + storage + ingress) using recursive dict merge
- **Platform abstraction**: Resource profiles and network types abstract Kubernetes complexity
- **Declarative**: Like Terraform, defines desired state rather than imperative steps
- **GitOps-first**: Generates manifests for version control, not direct kubectl apply

## Configuration Schema

### maniforge.yaml Structure
```yaml
platform:       # Platform source (built-in or future: remote)
cluster:        # Cluster-wide settings (name, domain, defaults)
output:         # Output directory for generated manifests
apps:           # App definitions (the main content)
```

### App Definition Fields
- **Required**: `image`
- **Optional**: `type` (deployment/daemonset/statefulset), `network`, `profile`, `nodeSelector`, `namespace`, `ports`, `storage`, `env`, `ingress`
- Default values come from `cluster.defaults` or platform defaults

## Code Modification Guidelines

### Adding New Resource Profiles
Add to `_default_platform_config()` in the `resourceProfiles` dict with cpu/memory requests/limits.

### Adding New Network Types
Add to `networkTypes` dict with `service.type` and optional `podOptions` (e.g., for hostNetwork).

### Extending Storage Types
Modify `translate_storage()` method to handle new volume types beyond pvc/hostPath/nfs.

### Customizing HelmRelease
The FluxCD HelmRelease structure is generated in `generate()` method (lines 507-530). Modify here to add fields like `install`, `upgrade`, or `dependsOn`.

### Improving Diff Display
Enhance `print_changes()` method in ManifestDiffer to show more detailed field-level changes.

## Exit Codes

Following Terraform conventions:
- `0`: Success, no changes (plan) or apply succeeded
- `1`: Error or validation failed, or changes detected (plan)
