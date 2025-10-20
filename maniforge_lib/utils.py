"""
Utility functions for Maniforge
"""

from typing import Dict, Any


def deep_merge(target: Dict, source: Dict):
    """Deep merge source dict into target dict"""
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            deep_merge(target[key], value)
        else:
            target[key] = value


def build_helm_release(app_name: str, app_config: Dict[str, Any], values: Dict[str, Any], helm_chart_config: Dict[str, Any]) -> Dict[str, Any]:
    """Construct a Flux HelmRelease manifest for an app.

    This centralizes the structure so generator and differ produce identical objects.
    """
    return {
        'apiVersion': 'helm.toolkit.fluxcd.io/v2beta2',
        'kind': 'HelmRelease',
        'metadata': {
            'name': app_name,
            'namespace': app_config.get('namespace', 'default')
        },
        'spec': {
            'interval': '1m',
            'chart': {
                'spec': {
                    'chart': helm_chart_config.get('name', 'app-template'),
                    'version': helm_chart_config.get('version', '4.4.0'),
                    'sourceRef': {
                        'kind': 'HelmRepository',
                        'name': helm_chart_config.get('repository', {}).get('name', 'bjw-s'),
                        'namespace': helm_chart_config.get('repository', {}).get('namespace', 'flux-system')
                    }
                }
            },
            'values': values
        }
    }
