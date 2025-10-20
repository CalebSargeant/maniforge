"""
Resource profile component generator
"""

import yaml
from pathlib import Path
from typing import Dict, Any


class ProfileGenerator:
    """Generates Kubernetes component structure for resource profiles"""
    
    def __init__(self, profiles_yaml: str = 'resource-profiles.yaml'):
        self.profiles_yaml = Path(profiles_yaml)
        self.profiles = None
        self.profile_types = None
    
    def load_profiles(self):
        """Load resource profiles from YAML"""
        if not self.profiles_yaml.exists():
            raise FileNotFoundError(f"Resource profiles file not found: {self.profiles_yaml}")
        
        with open(self.profiles_yaml) as f:
            data = yaml.safe_load(f)
        
        self.profiles = data.get('profiles', {})
        self.profile_types = data.get('profile_types', {})
    
    def generate_components(self, output_dir: Path):
        """Generate all Kubernetes component files"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate main kustomization.yaml with all patches
        self._generate_main_kustomization(output_dir)
        
        # Generate individual profile directories
        for profile_name, profile_config in self.profiles.items():
            self._generate_profile_component(output_dir, profile_name, profile_config)
        
        # Generate README
        self._generate_readme(output_dir)
        
        print(f"✅ Generated {len(self.profiles)} resource profile components in {output_dir}")
    
    def _generate_main_kustomization(self, output_dir: Path):
        """Generate main kustomization.yaml with inline patches"""
        kustomization = {
            'apiVersion': 'kustomize.config.k8s.io/v1alpha1',
            'kind': 'Component',
            'patches': []
        }
        
        # Group profiles by type for organization
        for type_prefix in ['p', 't', 'c', 'm', 'r']:
            # Add comment header (as a patch comment won't work, so we'll just organize)
            type_profiles = {k: v for k, v in self.profiles.items() if k.startswith(type_prefix + '.')}
            
            if type_profiles:
                for profile_name, profile_config in type_profiles.items():
                    cpu_req = profile_config['cpu']['requests']
                    cpu_lim = profile_config['cpu']['limits']
                    mem_req = profile_config['memory']['requests']
                    mem_lim = profile_config['memory']['limits']
                    
                    patch = {
                        'patch': f"""- op: add
  path: /spec/template/spec/containers/0/resources
  value: {{ requests: {{ cpu: {cpu_req}, memory: {mem_req} }}, limits: {{ cpu: {cpu_lim}, memory: {mem_lim} }} }}""",
                        'target': {
                            'labelSelector': f"resource-profile={profile_name}"
                        }
                    }
                    kustomization['patches'].append(patch)
        
        with open(output_dir / 'kustomization.yaml', 'w') as f:
            yaml.dump(kustomization, f, default_flow_style=False, sort_keys=False)
    
    def _generate_profile_component(self, output_dir: Path, profile_name: str, profile_config: Dict[str, Any]):
        """Generate individual profile component directory"""
        PATCHES_FILE = 'patches.yaml'
        
        profile_dir = output_dir / profile_name
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate kustomization.yaml
        kustomization = {
            'apiVersion': 'kustomize.config.k8s.io/v1alpha1',
            'kind': 'Component',
            'patches': [
                {'path': PATCHES_FILE, 'target': {'kind': 'Deployment'}},
                {'path': PATCHES_FILE, 'target': {'kind': 'StatefulSet'}},
                {'path': PATCHES_FILE, 'target': {'kind': 'DaemonSet'}}
            ]
        }
        
        with open(profile_dir / 'kustomization.yaml', 'w') as f:
            yaml.dump(kustomization, f, default_flow_style=False, sort_keys=False)
        
        # Generate patches.yaml (for regular Kubernetes resources)
        cpu_req = profile_config['cpu']['requests']
        cpu_lim = profile_config['cpu']['limits']
        mem_req = profile_config['memory']['requests']
        mem_lim = profile_config['memory']['limits']
        
        patches = [
            {
                'op': 'add',
                'path': '/spec/template/spec/containers/0/resources',
                'value': {
                    'requests': {
                        'cpu': cpu_req,
                        'memory': mem_req
                    },
                    'limits': {
                        'cpu': cpu_lim,
                        'memory': mem_lim
                    }
                }
            }
        ]
        
        with open(profile_dir / PATCHES_FILE, 'w') as f:
            yaml.dump(patches, f, default_flow_style=False, sort_keys=False)
        
        # Generate helmrelease-patches.yaml (for Flux HelmRelease resources)
        helmrelease_patches = [
            {
                'op': 'add',
                'path': '/spec/values/controllers/main/containers/main/resources',
                'value': {
                    'requests': {
                        'cpu': cpu_req,
                        'memory': mem_req
                    },
                    'limits': {
                        'cpu': cpu_lim,
                        'memory': mem_lim
                    }
                }
            }
        ]
        
        with open(profile_dir / 'helmrelease-patches.yaml', 'w') as f:
            yaml.dump(helmrelease_patches, f, default_flow_style=False, sort_keys=False)
    
    def _generate_readme(self, output_dir: Path):
        """Generate README with profile information"""
        readme_lines = [
            "# Resource Profiles",
            "",
            "AWS-style resource allocation profiles for Kubernetes workloads.",
            "",
            "## Available Profiles"
        ]
        
        # Generate tables for each profile type
        for type_prefix in ['p', 't', 'c', 'm', 'r']:
            type_info = self.profile_types.get(type_prefix, {})
            type_name = type_info.get('name', type_prefix.upper() + '-type')
            ratio = type_info.get('ratio', '')
            use_cases = type_info.get('use_cases', '')
            
            type_profiles = {k: v for k, v in self.profiles.items() if k.startswith(type_prefix + '.')}
            
            if type_profiles:
                readme_lines.extend([
                    f"### {type_name} - {ratio}",
                    f"**Best for:** {use_cases}",
                    "",
                    "| Size | CPU Request | Memory Request | CPU Limit | Memory Limit | Use Case |",
                    "|------|-------------|----------------|-----------|--------------|----------|"
                ])
                
                for profile_name, profile_config in type_profiles.items():
                    cpu_req = profile_config['cpu']['requests']
                    cpu_lim = profile_config['cpu']['limits']
                    mem_req = profile_config['memory']['requests']
                    mem_lim = profile_config['memory']['limits']
                    description = profile_config.get('description', '')
                    
                    readme_lines.append(
                        f"| `{profile_name}` | {cpu_req} | {mem_req} | {cpu_lim} | {mem_lim} | {description} |"
                    )
                
                readme_lines.append("")
        
        # Usage section
        readme_lines.extend([
            "## Usage",
            "",
            "Add the resource profile label to your workload:",
            "",
            "```yaml",
            "metadata:",
            "  labels:",
            "    resource-profile: m.medium",
            "```",
            "",
            "Then include this component in your kustomization:",
            "",
            "```yaml",
            "components:",
            "  - ../../_components/resource-profiles",
            "```",
            ""
        ])
        
        with open(output_dir / 'README.md', 'w') as f:
            f.write('\n'.join(readme_lines))
    
    @staticmethod
    def load_profiles_for_config(profiles_yaml: str = 'resource-profiles.yaml') -> Dict[str, Any]:
        """Load profiles in the format needed for maniforge config"""
        profiles_path = Path(profiles_yaml)
        if not profiles_path.exists():
            return {}
        
        with open(profiles_path) as f:
            data = yaml.safe_load(f)
        
        profiles = data.get('profiles', {})
        
        # Convert to the format expected by maniforge
        resource_profiles = {}
        for profile_name, profile_config in profiles.items():
            resource_profiles[profile_name] = {
                'cpu': {
                    'requests': profile_config['cpu']['requests'],
                    'limits': profile_config['cpu']['limits']
                },
                'memory': {
                    'requests': profile_config['memory']['requests'],
                    'limits': profile_config['memory']['limits']
                }
            }
        
        return resource_profiles
