# Maniforge Development Guide

## Architecture

Maniforge follows a modular architecture with clear separation of concerns:

```
maniforge (main entry point)
    ├── maniforge_lib/
    │   ├── __init__.py          # Package initialization
    │   ├── models.py            # Data models and types
    │   ├── utils.py             # Utility functions
    │   ├── config.py            # Configuration loading and validation
    │   ├── translator.py        # App config to Helm values translation
    │   ├── differ.py            # Manifest diffing for plan command
    │   ├── generator.py         # Manifest generation
    │   ├── capacity_planner.py  # Resource capacity analysis
    │   └── core.py              # Main Maniforge class
```

## Module Responsibilities

### models.py
Data models and types used throughout the application:
- `ResourceAmount`: Parse and format CPU/memory values
- `ResourceRequirements`: Store resource requests and limits
- `NodeCapacity`: Store node capacity information
- `AppResources`: Store app resource requirements

### utils.py
Utility functions:
- `deep_merge()`: Deep merge dictionaries (used for config merging)

### config.py
Configuration management:
- `ConfigLoader`: Load and parse maniforge.yaml and platform.yaml
- `ConfigValidator`: Validate configuration
- `ConfigInitializer`: Create new configurations

### translator.py
Translates high-level app configuration to bjw-s-app-template Helm values:
- `AppTranslator`: Main translation class
  - `translate_image()`: Convert image strings
  - `translate_network()`: Configure networking
  - `translate_storage()`: Configure volumes
  - `translate_resources()`: Apply resource profiles
  - `translate_node_selector()`: Apply node selectors
  - `translate_ingress()`: Generate ingress config
  - `translate_app()`: Orchestrate full app translation

### differ.py
Show differences between current and desired state:
- `ManifestDiffer`: Compare manifests
  - `load_current_state()`: Read existing manifests
  - `load_desired_state()`: Generate desired manifests
  - `get_changes()`: Detect changes
  - `print_changes()`: Display changes in Terraform-like format

### generator.py
Generate Kubernetes manifests:
- `ManifestGenerator`: Create HelmRelease and Kustomization files

### capacity_planner.py
Analyze resource usage and capacity:
- `CapacityPlanner`: Resource analysis
  - `get_node_capacity()`: Get capacity for a node type
  - `get_app_resources()`: Extract resource requirements
  - `analyze_capacity()`: Analyze usage across node types
  - `print_capacity_analysis()`: Display capacity report

### core.py
Main application orchestration:
- `Maniforge`: Main class that ties everything together
  - `load_config()`: Initialize all components
  - `validate()`: Validate configuration
  - `plan()`: Show changes and capacity analysis
  - `apply()`: Generate manifests
  - `init()`: Create new project

## Development Workflow

### 1. Setup Development Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Testing Changes

```bash
# Test the Python script directly
python3 maniforge init --cluster test
python3 maniforge plan
python3 maniforge apply

# Build and test the executable
./build.sh
./dist/maniforge plan
```

### 3. Adding New Features

When adding features, follow the modular architecture:

1. **Data models**: Add to `models.py`
2. **Configuration**: Add to `config.py` and validators
3. **Translation logic**: Add to `translator.py`
4. **Analysis**: Add to `capacity_planner.py` or create new analyzer
5. **Orchestration**: Update `core.py` to wire everything together

### 4. Code Style

- Follow PEP 8 style guidelines
- Use type hints for function parameters and returns
- Add docstrings for classes and public methods
- Keep functions focused and single-purpose
- Use clear, descriptive variable names

## Building

The build process uses PyInstaller to create a standalone executable:

```bash
./build.sh
```

This creates a universal executable in `dist/maniforge` that:
- Bundles Python interpreter and all dependencies
- Works on any Linux x64 system without Python installed
- Includes all maniforge_lib modules

## Testing

### Manual Testing

Create a test directory and configuration:

```bash
mkdir /tmp/test-maniforge
cd /tmp/test-maniforge
/path/to/maniforge init --cluster test
# Edit maniforge.yaml
/path/to/maniforge plan
/path/to/maniforge apply
```

### Testing Capacity Planning

Create a configuration with multiple node types and apps:

```yaml
nodeSelectors:
  pi:
    labels:
      type: pi
    capacity:
      cpu: 4000m
      memory: 8Gi
  workers:
    labels:
      type: worker
    capacity:
      cpu: 8000m
      memory: 16Gi

apps:
  app1:
    nodeSelector: pi
    profile: c.small
  app2:
    nodeSelector: workers
    profile: r.large
```

Run `maniforge plan` to see the capacity analysis.

## Release Process

Releases are automated using semantic versioning. Use conventional commits:

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

The CI/CD workflow automatically:
1. Determines version based on commits
2. Creates git tag and GitHub release
3. Builds binaries for all platforms
4. Uploads binaries + SHA256SUMS
5. Generates CHANGELOG.md

## Contributing

1. Follow the modular architecture
2. Add appropriate error handling
3. Update documentation for new features
4. Test both Python script and built executable
5. Use conventional commits for clear release notes
