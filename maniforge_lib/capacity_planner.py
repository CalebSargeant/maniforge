"""
Capacity planning and resource analysis
"""

from typing import Dict, Any, List, Tuple
from collections import defaultdict
from .models import ResourceAmount, ResourceRequirements, NodeCapacity, AppResources


class CapacityPlanner:
    """Analyzes resource usage and capacity for node groups"""
    
    def __init__(self, platform_config: Dict[str, Any]):
        self.platform_config = platform_config
        self.node_selectors = platform_config.get('nodeSelectors', {})
        self.resource_profiles = platform_config.get('resourceProfiles', {})
    
    def get_node_capacity(self, node_selector: str, apps_config: Dict[str, Any]) -> NodeCapacity:
        """Get capacity for a node type, preferring maniforge.yaml 'nodes' overrides"""
        # Prefer capacities defined in maniforge.yaml under 'nodes'
        nodes_cfg = apps_config.get('nodes', {}) if apps_config else {}
        cfg = nodes_cfg.get(node_selector, {})
        if cfg:
            cpu_val = cfg.get('cpu', cfg.get('cores'))  # allow alias 'cores'
            mem_val = cfg.get('memory', cfg.get('mem'))
            disk_val = cfg.get('disk')
            count = int(cfg.get('count', 1))
            cpu = ResourceAmount.parse_cpu(str(cpu_val)) if cpu_val is not None else ResourceAmount.parse_cpu('4000m')
            memory = ResourceAmount.parse_memory(str(mem_val)) if mem_val is not None else ResourceAmount.parse_memory('8Gi')
            disk = ResourceAmount.parse_memory(str(disk_val)) if disk_val is not None else None
            return NodeCapacity(cpu=cpu, memory=memory, node_type=node_selector, count=count, disk=disk)
        
        # Fallback to platform 'nodeSelectors' capacities
        node_config = self.node_selectors.get(node_selector, {})
        capacity = node_config.get('capacity', {})
        
        if not capacity:
            # Return default capacity if not specified
            return NodeCapacity(
                cpu=ResourceAmount.parse_cpu('4000m'),
                memory=ResourceAmount.parse_memory('8Gi'),
                node_type=node_selector,
                count=1,
            )
        
        return NodeCapacity(
            cpu=ResourceAmount.parse_cpu(capacity.get('cpu', '4000m')),
            memory=ResourceAmount.parse_memory(capacity.get('memory', '8Gi')),
            node_type=node_selector,
            count=int(capacity.get('count', 1))
        )
    
    def get_app_resources(self, app_name: str, app_config: Dict[str, Any], 
                          cluster_config: Dict[str, Any]) -> AppResources:
        """Extract resource requirements for an app"""
        # Determine the profile to use
        profile_name = app_config.get('profile', cluster_config.get('defaults', {}).get('profile'))
        profile = self.resource_profiles.get(profile_name, {})
        
        if not profile:
            # Default minimal resources
            profile = {
                'cpu': {'requests': '100m', 'limits': '500m'},
                'memory': {'requests': '128Mi', 'limits': '512Mi'}
            }
        
        resources = ResourceRequirements(
            cpu_request=ResourceAmount.parse_cpu(profile['cpu']['requests']),
            cpu_limit=ResourceAmount.parse_cpu(profile['cpu']['limits']),
            memory_request=ResourceAmount.parse_memory(profile['memory']['requests']),
            memory_limit=ResourceAmount.parse_memory(profile['memory']['limits'])
        )
        
        # Determine node selector
        node_selector = app_config.get('nodeSelector', cluster_config.get('defaults', {}).get('nodeSelector', 'default'))
        
        # Default assumption: replicas will be set to node count during analysis
        replicas = 1
        
        return AppResources(
            app_name=app_name,
            namespace=app_config.get('namespace', 'default'),
            node_selector=node_selector,
            replicas=replicas,
            resources=resources
        )
    
    def analyze_capacity(self, apps_config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze capacity usage across all node types"""
        apps = apps_config.get('apps', {})
        cluster_config = apps_config.get('cluster', {})
        
        # Group apps by node selector
        apps_by_node = defaultdict(list)
        
        for app_name, app_config in apps.items():
            app_resources = self.get_app_resources(app_name, app_config, cluster_config)
            apps_by_node[app_resources.node_selector].append(app_resources)
        
        # Calculate usage per node type
        analysis = {}
        
        for node_selector, apps_list in apps_by_node.items():
            capacity = self.get_node_capacity(node_selector, apps_config)
            
            # Effective replicas assumption: 1 per node for each app on this node type
            effective_replicas = max(1, capacity.count)
            
            # Calculate total requests and limits across all replicas
            total_cpu_request = sum(app.resources.cpu_request.value for app in apps_list) * effective_replicas
            total_cpu_limit = sum(app.resources.cpu_limit.value for app in apps_list) * effective_replicas
            total_memory_request = sum(app.resources.memory_request.value for app in apps_list) * effective_replicas
            total_memory_limit = sum(app.resources.memory_limit.value for app in apps_list) * effective_replicas
            
            # Total capacity across all nodes in this group
            total_cpu_capacity = capacity.cpu.value * effective_replicas
            total_memory_capacity = capacity.memory.value * effective_replicas
            
            # Calculate percentages based on requests (more important for scheduling)
            cpu_request_pct = (total_cpu_request / total_cpu_capacity) * 100 if total_cpu_capacity else 0
            memory_request_pct = (total_memory_request / total_memory_capacity) * 100 if total_memory_capacity else 0
            
            # Calculate percentages based on limits
            cpu_limit_pct = (total_cpu_limit / total_cpu_capacity) * 100 if total_cpu_capacity else 0
            memory_limit_pct = (total_memory_limit / total_memory_capacity) * 100 if total_memory_capacity else 0
            
            analysis[node_selector] = {
                'capacity': capacity,
                'apps': apps_list,
                'usage': {
                    'cpu_request': ResourceAmount(total_cpu_request, ''),
                    'cpu_limit': ResourceAmount(total_cpu_limit, ''),
                    'memory_request': ResourceAmount(total_memory_request, ''),
                    'memory_limit': ResourceAmount(total_memory_limit, ''),
                    'total_cpu_capacity': ResourceAmount(total_cpu_capacity, ''),
                    'total_memory_capacity': ResourceAmount(total_memory_capacity, ''),
                },
                'percentages': {
                    'cpu_request': cpu_request_pct,
                    'cpu_limit': cpu_limit_pct,
                    'memory_request': memory_request_pct,
                    'memory_limit': memory_limit_pct,
                }
            }
        
        return analysis
    
    def print_capacity_analysis(self, analysis: Dict[str, Any]):
        """Print capacity analysis in a readable format"""
        if not analysis:
            return
        
        print("\n📊 Capacity Planning Analysis")
        print("=" * 80)
        
        for node_selector, data in analysis.items():
            capacity = data['capacity']
            usage = data['usage']
            percentages = data['percentages']
            apps = data['apps']
            
            print(f"\n🖥️  Node Type: {node_selector}")
            print(f"   Nodes: {capacity.count}")
            print(f"   Per-node Capacity: CPU={capacity.cpu.format_cpu()} Memory={capacity.memory.format_memory()}")
            total_cpu_cap = usage['total_cpu_capacity'].format_cpu()
            total_mem_cap = usage['total_memory_capacity'].format_memory()
            print(f"   Total Capacity: CPU={total_cpu_cap} Memory={total_mem_cap}")
            if capacity.disk:
                print(f"   Disk (per node): {capacity.disk.format_memory()}")
            print(f"   Apps: {len(apps)}")
            print()
            
            # CPU Analysis
            print("   CPU Usage:")
            print(f"     Requests: {usage['cpu_request'].format_cpu()} / {total_cpu_cap} ({percentages['cpu_request']:.1f}%)")
            self._print_usage_bar(percentages['cpu_request'])
            print(f"     Limits:   {usage['cpu_limit'].format_cpu()} / {total_cpu_cap} ({percentages['cpu_limit']:.1f}%)")
            self._print_usage_bar(percentages['cpu_limit'])
            print()
            
            # Memory Analysis
            print("   Memory Usage:")
            print(f"     Requests: {usage['memory_request'].format_memory()} / {total_mem_cap} ({percentages['memory_request']:.1f}%)")
            self._print_usage_bar(percentages['memory_request'])
            print(f"     Limits:   {usage['memory_limit'].format_memory()} / {total_mem_cap} ({percentages['memory_limit']:.1f}%)")
            self._print_usage_bar(percentages['memory_limit'])
            print()
            
            # Status indicator
            max_request_pct = max(percentages['cpu_request'], percentages['memory_request'])
            if max_request_pct > 100:
                print(f"   ⚠️  WARNING: Over capacity by {max_request_pct - 100:.1f}% (requests)")
            elif max_request_pct > 80:
                print(f"   ⚡ Near capacity ({max_request_pct:.1f}% used)")
            else:
                print(f"   ✅ Capacity available ({100 - max_request_pct:.1f}% free)")
            
            # List apps
            print("\n   Apps on this node type:")
            for app in apps:
                cpu_req = app.resources.cpu_request.format_cpu()
                mem_req = app.resources.memory_request.format_memory()
                print(f"     • {app.app_name}: CPU={cpu_req} Memory={mem_req}")
        
        print("\n" + "=" * 80)
        print("\n⚠️  Capacity Planning Notes:")
        print("   • Assumes 1 replica per node for each app on a node type (DaemonSets and node-pinned deployments)")
        print("   • Multi-replica deployments on the same node type may under-count resources")
        print("   • Analysis is based on resource requests (used for scheduling decisions)")
        print("   • Use this as a guideline for node sizing and capacity planning\n")
    
    def _print_usage_bar(self, percentage: float):
        """Print a visual usage bar"""
        bar_length = 40
        filled = int((percentage / 100) * bar_length)
        filled = min(filled, bar_length)  # Cap at bar_length
        
        if percentage > 100:
            bar = '█' * bar_length
            symbol = '⚠️ '
        elif percentage > 80:
            bar = '█' * filled + '░' * (bar_length - filled)
            symbol = '⚡'
        else:
            bar = '█' * filled + '░' * (bar_length - filled)
            symbol = '  '
        
        print(f"     {symbol}[{bar}]")
