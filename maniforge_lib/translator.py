"""
Application configuration translator
Translates high-level app config to bjw-s-app-template values
"""

from typing import Dict, Any, List
from .utils import deep_merge


class AppTranslator:
    """Translates high-level app config to bjw-s-app-template values"""
    
    def __init__(self, platform_config: Dict[str, Any]):
        self.platform = platform_config
        self.resource_profiles = platform_config.get('resourceProfiles', {})
        self.network_types = platform_config.get('networkTypes', {})
        self.storage_types = platform_config.get('storageTypes', {})
        self.ingress_defaults = platform_config.get('ingressDefaults', {})
        self.node_selectors = platform_config.get('nodeSelectors', {})
    
    def translate_image(self, image_str: str) -> Dict[str, Any]:
        """Convert image string to repository:tag format"""
        if ':' in image_str:
            repo, tag = image_str.rsplit(':', 1)
        else:
            repo, tag = image_str, 'latest'
        
        return {
            'repository': repo,
            'tag': tag
        }
    
    def translate_network(self, network_type: str, ports: List[Dict] = None) -> Dict[str, Any]:
        """Convert network type to service and pod configuration"""
        network_config = self.network_types.get(network_type, {})
        
        result = {
            'service': {
                'main': {
                    'controller': 'main',
                    'type': network_config.get('service', {}).get('type', 'ClusterIP'),
                    'ports': {}
                }
            }
        }
        
        # Add pod options if specified
        pod_options = network_config.get('podOptions', {})
        if pod_options:
            result['defaultPodOptions'] = pod_options
        
        # Configure ports
        if ports:
            for i, port_config in enumerate(ports):
                port_name = port_config.get('name', f'port-{i}')
                result['service']['main']['ports'][port_name] = {
                    'enabled': True,
                    'port': port_config['port'],
                    'targetPort': port_config.get('targetPort', port_config['port']),
                    'protocol': port_config.get('protocol', 'TCP')
                }
                
                if network_config.get('service', {}).get('type') == 'NodePort' and 'nodePort' in port_config:
                    result['service']['main']['ports'][port_name]['nodePort'] = port_config['nodePort']
        else:
            result['service']['main']['ports']['http'] = {
                'enabled': True,
                'port': 80,
                'targetPort': 8080,
                'protocol': 'TCP'
            }
        
        return result
    
    def translate_storage(self, storage_config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert storage configuration to persistence"""
        persistence = {}
        
        for volume_name, volume_config in storage_config.items():
            volume_type = volume_config['type']
            
            persistence_volume = {
                'enabled': True,
                'type': volume_type,
                'globalMounts': [{
                    'path': volume_config['mount'],
                    'readOnly': volume_config.get('readonly', False)
                }]
            }
            
            if volume_type == 'hostPath':
                persistence_volume['hostPath'] = volume_config['path']
            elif volume_type == 'persistentVolumeClaim':
                persistence_volume['size'] = volume_config['size']
                if 'storageClass' in volume_config:
                    persistence_volume['storageClass'] = volume_config['storageClass']
                persistence_volume['accessMode'] = volume_config.get('accessMode', 'ReadWriteOnce')
            elif volume_type == 'nfs':
                persistence_volume['server'] = volume_config['server']
                persistence_volume['path'] = volume_config['path']
            
            persistence[volume_name] = persistence_volume
        
        return {'persistence': persistence} if persistence else {}
    
    def translate_resources(self, profile_name: str) -> Dict[str, Any]:
        """Convert resource profile to resources configuration"""
        profile = self.resource_profiles.get(profile_name, {})
        if not profile:
            return {}
        
        return {
            'controllers': {
                'main': {
                    'containers': {
                        'main': {
                            'resources': {
                                'requests': {
                                    'cpu': profile.get('cpu', {}).get('requests', '100m'),
                                    'memory': profile.get('memory', {}).get('requests', '128Mi')
                                },
                                'limits': {
                                    'cpu': profile.get('cpu', {}).get('limits', '500m'),
                                    'memory': profile.get('memory', {}).get('limits', '512Mi')
                                }
                            }
                        }
                    }
                }
            }
        }
    
    def translate_node_selector(self, node_selector: str) -> Dict[str, Any]:
        """Convert node selector to pod options"""
        node_config = self.node_selectors.get(node_selector, {})
        labels = node_config.get('labels', {})
        
        if labels:
            return {
                'defaultPodOptions': {
                    'nodeSelector': labels
                }
            }
        return {}
    
    def translate_ingress(self, app_name: str, domain: str, enabled: bool = True) -> Dict[str, Any]:
        """Generate ingress configuration"""
        if not enabled:
            return {}
        
        return {
            'ingress': {
                'main': {
                    'enabled': True,
                    'className': self.ingress_defaults.get('className', 'traefik'),
                    'annotations': self.ingress_defaults.get('annotations', {}),
                    'hosts': [
                        {
                            'host': f"{app_name}.{domain}",
                            'paths': [
                                {
                                    'path': '/',
                                    'pathType': 'Prefix',
                                    'service': {
                                        'identifier': 'main',
                                        'port': 'http'
                                    }
                                }
                            ]
                        }
                    ],
                    'tls': [
                        {
                            'hosts': [f"{app_name}.{domain}"],
                            'secretName': f"{app_name}-tls"
                        }
                    ]
                }
            }
        }
    
    def translate_app(self, app_name: str, app_config: Dict[str, Any], cluster_config: Dict[str, Any]) -> Dict[str, Any]:
        """Translate a complete app configuration"""
        values = {
            'controllers': {
                'main': {
                    'type': app_config.get('type', 'deployment'),
                    'containers': {
                        'main': {
                            'image': self.translate_image(app_config['image']),
                            'env': app_config.get('env', {})
                        }
                    }
                }
            },
            'defaultPodOptions': {}
        }
        
        # Apply configurations with deep merge
        configurations = [
            ('profile', lambda: self.translate_resources(app_config.get('profile', cluster_config.get('defaults', {}).get('profile')))),
            ('nodeSelector', lambda: self.translate_node_selector(app_config.get('nodeSelector', cluster_config.get('defaults', {}).get('nodeSelector')))),
            ('network', lambda: self.translate_network(app_config.get('network', 'clusterip'), app_config.get('ports', []))),
            ('storage', lambda: self.translate_storage(app_config['storage']) if 'storage' in app_config else {}),
            ('ingress', lambda: self.translate_ingress(app_name, cluster_config.get('domain')) if cluster_config.get('domain') and app_config.get('ingress', True) else {})
        ]
        
        for name, func in configurations:
            config = func()
            if config:
                deep_merge(values, config)
        
        return values
