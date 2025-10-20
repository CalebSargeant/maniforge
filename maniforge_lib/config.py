"""
Configuration loading and validation
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, Any, List
from .profile_generator import ProfileGenerator

# Default profile constants
DEFAULT_PROFILE_C_SMALL = 'c.small'


class ConfigLoader:
    """Loads and manages configuration files"""
    
    def __init__(self, config_file: str = 'maniforge.yaml'):
        self.config_file = Path(config_file)
        self.config = None
        self.platform_config = None
        self.apps_config = None
    
    def load(self):
        """Load maniforge configuration"""
        if not self.config_file.exists():
            print(f"❌ Configuration file not found: {self.config_file}")
            print("Run 'maniforge init' to create a new configuration")
            sys.exit(1)
        
        with open(self.config_file) as f:
            self.config = yaml.safe_load(f)
        
        # Load platform config (could be remote in the future)
        platform_file = Path(self.config.get('platform', {}).get('file', 'platform.yaml'))
        if platform_file.exists():
            with open(platform_file) as f:
                self.platform_config = yaml.safe_load(f)
        else:
            self.platform_config = self._default_platform_config()
        
        self.apps_config = self.config
    
    def _default_platform_config(self):
        """Default platform configuration"""
        # Try to load resource profiles from YAML file
        resource_profiles = ProfileGenerator.load_profiles_for_config('resource-profiles.yaml')
        
        # Fallback to minimal set if file doesn't exist
        if not resource_profiles:
            # Define constants for fallback profiles
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
                'host': {'service': {'type': 'ClusterIP'}, 'podOptions': {'hostNetwork': True, 'dnsPolicy': 'ClusterFirstWithHostNet'}}
            },
            'nodeSelectors': {
                'pi': {'labels': {'type': 'pi'}, 'capacity': {'cpu': '4000m', 'memory': '8Gi'}}
            },
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
        
        for app_name, app_config in apps.items():
            if 'image' not in app_config:
                errors.append(f"App '{app_name}': missing required field 'image'")
            
            profile = app_config.get('profile', cluster_config.get('defaults', {}).get('profile'))
            if profile and profile not in self.platform_config.get('resourceProfiles', {}):
                errors.append(f"App '{app_name}': unknown profile '{profile}'")
            
            network = app_config.get('network', 'clusterip')
            if network not in self.platform_config.get('networkTypes', {}):
                errors.append(f"App '{app_name}': unknown network type '{network}'")
        
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
            'platform': {
                'source': 'built-in',
                'version': 'v1.0.0'
            },
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
            }
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Initialized maniforge project: {config_file}")
        print("Edit the configuration and run 'maniforge plan' to see what will be created")
