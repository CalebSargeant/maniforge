"""
Manifest differ for showing changes
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple
from collections.abc import Mapping

from .utils import build_helm_release


class ManifestDiffer:
    """Compare and show differences between manifests"""
    
    def __init__(self):
        self.current_state = {}
        self.desired_state = {}
    
    def load_current_state(self, output_dir: Path):
        """Load currently generated manifests"""
        if not output_dir.exists():
            return
        
        for app_dir in output_dir.iterdir():
            if app_dir.is_dir():
                app_name = app_dir.name
                manifest_file = app_dir / 'helm-release.yaml'
                if manifest_file.exists():
                    with open(manifest_file) as f:
                        self.current_state[app_name] = yaml.safe_load(f)
    
    def load_desired_state(self, generator):
        """Generate desired state in memory"""
        apps = generator.apps_config.get('apps', {})
        cluster_config = generator.apps_config.get('cluster', {})
        
        for app_name, app_config in apps.items():
            values = generator.translator.translate_app(app_name, app_config, cluster_config)
            
            helm_chart_config = generator.platform_config.get('helmChart', {})
            helm_release = build_helm_release(app_name, app_config, values, helm_chart_config)
            self.desired_state[app_name] = helm_release
    
    def get_changes(self):
        """Get list of changes"""
        changes = []
        
        # New apps
        for app_name in self.desired_state:
            if app_name not in self.current_state:
                changes.append(('create', app_name, None, self.desired_state[app_name]))
        
        # Removed apps
        for app_name in self.current_state:
            if app_name not in self.desired_state:
                changes.append(('delete', app_name, self.current_state[app_name], None))
        
        # Modified apps
        for app_name in self.desired_state:
            if app_name in self.current_state:
                current = self._normalize_manifest(self.current_state[app_name])
                desired = self._normalize_manifest(self.desired_state[app_name])
                
                if current != desired:
                    changes.append(('update', app_name, self.current_state[app_name], self.desired_state[app_name]))
        
        return changes
    
    def _normalize_manifest(self, manifest):
        """Remove fields that change between runs"""
        normalized = manifest.copy()
        # Remove any fields that might change due to generation timestamps etc.
        return normalized
    
    def print_changes(self, changes):
        """Print changes in Terraform-like format"""
        if not changes:
            print("🟢 No changes. Infrastructure is up-to-date.")
            return
        
        print(f"\n📋 Plan: {len(changes)} changes\n")
        
        for action, app_name, current, desired in changes:
            if action == 'create':
                print(f"  🟢 {app_name}")
                print("      App will be created")
                print(f"      Image: {self._get_image_from_values(desired.get('spec', {}).get('values', {}))}")
                print(f"      Namespace: {desired.get('metadata', {}).get('namespace', 'default')}")
                
            elif action == 'delete':
                print(f"  🔴 {app_name}")
                print("      App will be deleted")
                
            elif action == 'update':
                print(f"  🟡 {app_name}")
                print("      App will be modified")
                
                # Show specific changes
                current_image = self._get_image_from_values(current.get('spec', {}).get('values', {}))
                desired_image = self._get_image_from_values(desired.get('spec', {}).get('values', {}))
                
                if current_image != desired_image:
                    print(f"      Image: {current_image} → {desired_image}")
                
                # Check for resource changes
                current_resources = self._get_resources_from_values(current.get('spec', {}).get('values', {}))
                desired_resources = self._get_resources_from_values(desired.get('spec', {}).get('values', {}))
                
                if current_resources != desired_resources:
                    print("      Resources will be updated")
            
            print()
    
    def _get_nested(self, obj: Any, keys: List[str]):
        """Safely traverse nested dict-like structures.
        Returns the final value if all keys exist and each level is mapping-like; otherwise returns None.
        """
        cur = obj
        for k in keys:
            if not isinstance(cur, Mapping):
                return None
            cur = cur.get(k)
            if cur is None:
                return None
        return cur
    
    def _get_image_from_values(self, values):
        """Extract image from helm values"""
        image_config = self._get_nested(values, ['controllers', 'main', 'containers', 'main', 'image'])
        if not isinstance(image_config, Mapping):
            return "unknown"
        repo = image_config.get('repository', '') or ''
        tag = image_config.get('tag', 'latest') or 'latest'
        return f"{repo}:{tag}" if repo else "unknown"
    
    def _get_resources_from_values(self, values):
        """Extract resources from helm values"""
        container = self._get_nested(values, ['controllers', 'main', 'containers', 'main'])
        if not isinstance(container, Mapping):
            return {}
        resources = container.get('resources', {})
        return resources if isinstance(resources, Mapping) else {}
