"""
Configuration loading and validation
"""

import sys
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List
from .profile_generator import ProfileGenerator

# Defaults and constants
DEFAULT_PROFILE_C_SMALL = 'c.small'
RESOURCE_PROFILES_FILE_ENV = 'MANIFORGE_RESOURCE_PROFILES_YAML'
RESOURCE_PROFILES_FILENAME = os.getenv(RESOURCE_PROFILES_FILE_ENV, 'resource-profiles.yaml')


class ConfigLoader:
    """Loads and manages configuration files"""
    
    def __init__(self, config_file: str = 'maniforge.yaml'):
        self.config_file = Path(config_file)
        self.config = None
        self.platform_config = None
        self.apps_config = None
    
    def load(self):
        """Load maniforge configuration (single-file only)"""
        if not self.config_file.exists():
            print(f"❌ Configuration file not found: {self.config_file}")
            print("Run 'maniforge init' to create a new configuration")
            sys.exit(1)
        
        with open(self.config_file) as f:
            self.config = yaml.safe_load(f) or {}
        
        # Always use built-in defaults; do not load external platform files
        self.platform_config = self._default_platform_config()
        
        # Apply optional overrides from maniforge.yaml top-level keys
        overrides_keys = ['resourceProfiles', 'networkTypes', 'ingressDefaults', 'helmChart', 'nodeSelectors']
        for key in overrides_keys:
            if key in self.config:
                # Shallow merge is fine; structures are dicts
                existing = self.platform_config.get(key, {})
                incoming = self.config.get(key, {})
                if isinstance(existing, dict) and isinstance(incoming, dict):
                    existing.update(incoming)
                    self.platform_config[key] = existing
                else:
                    self.platform_config[key] = incoming
        
        # Auto-generate nodeSelectors from top-level 'nodes' for scheduling labels
        nodes_cfg = self.config.get('nodes', {}) or {}
        node_selectors = self.platform_config.setdefault('nodeSelectors', {})
        for node_name in nodes_cfg.keys():
            node_selectors.setdefault(node_name, {'labels': {'type': node_name}})
        
        self.apps_config = self.config
    
    def _default_platform_config(self):
        """Default settings used by maniforge (no external platform file)"""
        # Try to load resource profiles from YAML file (configurable via env)
        resource_profiles = ProfileGenerator.load_profiles_for_config(RESOURCE_PROFILES_FILENAME)
        
        # Fallback to minimal set if file doesn't exist
        if not resource_profiles:
            PROFILE_C_PICO = 'c.pico'
            PROFILE_R_LARGE = 'r.large'
            resource_profiles = {
                PROFILE_C_PICO: {'cpu': {'requests': '100m', 'limits': '250m'}, 'memory': {'requests': '256Mi', 'limits': '512Mi'}},
                DEFAULT_PROFILE_C_SMALL: {'cpu': {'requests': '250m', 'limits': '500m'}, 'memory': {'requests': '512Mi', 'limits': '1Gi'}},
                PROFILE_R_LARGE: {'cpu': {'requests': '500m', 'limits': '1000m'}, 'memory': {'requests': '4Gi', 'limits': '8Gi'}}
            }
        
        return {
            'resourceProfiles': resource_profiles,
            'networkTypes': {
                'clusterip': {'service': {'type': 'ClusterIP'}, 'podOptions': {}},
                'nodeport': {'service': {'type': 'NodePort'}, 'podOptions': {}},
                'loadbalancer': {'service': {'type': 'LoadBalancer'}, 'podOptions': {}},
                'host': {'service': {'type': 'ClusterIP'}, 'podOptions': {'hostNetwork': True, 'dnsPolicy': 'ClusterFirstWithHostNet'}}
            },
            'nodeSelectors': {},
            'ingressDefaults': {
                'className': 'traefik',
                'annotations': {
                    'traefik.ingress.kubernetes.io/router.entrypoints': 'websecure',
                    'traefik.ingress.kubernetes.io/router.tls': 'true',
                    'cert-manager.io/cluster-issuer': 'letsencrypt-dns'
                }
            },
            'helmChart': {'name': 'app-template', 'version': '4.4.0', 'repository': {'name': 'bjw-s', 'namespace': 'flux-system'}}
        }


class ConfigValidator:
    """Validates maniforge configuration"""
    
    def __init__(self, apps_config: Dict[str, Any], platform_config: Dict[str, Any]):
        self.apps_config = apps_config
        self.platform_config = platform_config
    
    def validate(self) -> bool:
        """Validate configuration"""
        errors = []
        apps = self.apps_config.get('apps', {})
        cluster_config = self.apps_config.get('cluster', {})
        nodes_cfg = self.apps_config.get('nodes', {})
        
        for app_name, app_config in apps.items():
            if 'image' not in app_config:
                errors.append(f"App '{app_name}': missing required field 'image'")
            
            profile = app_config.get('profile', cluster_config.get('defaults', {}).get('profile'))
            if profile and profile not in self.platform_config.get('resourceProfiles', {}):
                errors.append(f"App '{app_name}': unknown profile '{profile}'")
            
            network = app_config.get('network', 'clusterip')
            if network not in self.platform_config.get('networkTypes', {}):
                errors.append(f"App '{app_name}': unknown network type '{network}'")
            
            # Validate node selector exists either in platform nodeSelectors or nodes override
            node_selector = app_config.get('nodeSelector', cluster_config.get('defaults', {}).get('nodeSelector'))
            if node_selector:
                if node_selector not in self.platform_config.get('nodeSelectors', {}) and node_selector not in nodes_cfg:
                    errors.append(f"App '{app_name}': unknown nodeSelector '{node_selector}' (define in top-level nodes)")
        
        # Basic nodes config validation (optional)
        for node_name, node_spec in nodes_cfg.items():
            if not isinstance(node_spec, dict):
                errors.append(f"nodes.{node_name}: must be a mapping with keys like count/cpu/memory")
                continue
            # Validate count is int-like if provided
            if 'count' in node_spec:
                try:
                    int(node_spec['count'])
                except Exception:
                    errors.append(f"nodes.{node_name}.count must be an integer")
            # Validate at least one of cpu/memory present
            if not any(k in node_spec for k in ('cpu', 'cores', 'memory', 'mem')):
                errors.append(f"nodes.{node_name}: specify at least 'cpu' and 'memory' (or aliases 'cores'/'mem') for accurate capacity analysis")
        
        if errors:
            print("❌ VALIDATION ERRORS:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True


class ConfigInitializer:
    """Creates new configuration files"""
    
    @staticmethod
    def init(config_file: Path, cluster_name: str = 'firefly'):
        """Initialize a new maniforge project"""
        if config_file.exists():
            print(f"❌ Configuration already exists: {config_file}")
            sys.exit(1)
        
        config = {
            'cluster': {
                'name': cluster_name,
                'domain': 'example.com',
                'defaults': {
                    'profile': DEFAULT_PROFILE_C_SMALL,
                    'nodeSelector': 'pi'
                }
            },
            'output': {
                'directory': 'apps'
            },
            'apps': {
                'nginx-example': {
                    'image': 'nginx:latest',
                    'type': 'deployment',
                    'network': 'clusterip',
                    'profile': DEFAULT_PROFILE_C_SMALL
                }
            },
            'nodes': {
                'pi': {
                    'count': 1,
                    'cpu': 4,
                    'mem': '8Gi'
                }
            }
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Initialized maniforge project: {config_file}")
        print("Edit the configuration and run 'maniforge plan' to see what will be created")
