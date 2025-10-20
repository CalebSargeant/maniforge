"""
Manifest generator
"""

import yaml
from pathlib import Path
from typing import Dict, Any

from .utils import build_helm_release


class ManifestGenerator:
    """Generates Kubernetes manifests"""
    
    def __init__(self, apps_config: Dict[str, Any], platform_config: Dict[str, Any], translator):
        self.apps_config = apps_config
        self.platform_config = platform_config
        self.translator = translator
    
    def generate(self, output_dir: Path):
        """Generate manifests"""
        apps = self.apps_config.get('apps', {})
        cluster_config = self.apps_config.get('cluster', {})
        
        for app_name, app_config in apps.items():
            values = self.translator.translate_app(app_name, app_config, cluster_config)
            
            kustomization = {
                'apiVersion': 'kustomize.config.k8s.io/v1beta1',
                'kind': 'Kustomization',
                'namespace': app_config.get('namespace', 'default'),
                'resources': ['helm-release.yaml']
            }
            
            helm_chart_config = self.platform_config.get('helmChart', {})
            helm_release = build_helm_release(app_name, app_config, values, helm_chart_config)
            
            app_dir = output_dir / app_name
            app_dir.mkdir(parents=True, exist_ok=True)
            
            with open(app_dir / 'kustomization.yaml', 'w') as f:
                yaml.dump(kustomization, f, default_flow_style=False, sort_keys=False)
            
            with open(app_dir / 'helm-release.yaml', 'w') as f:
                yaml.dump(helm_release, f, default_flow_style=False, sort_keys=False)
            
            print(f"  ✅ {app_name}")
