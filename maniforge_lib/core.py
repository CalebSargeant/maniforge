"""
Core Maniforge application
"""

import sys
from pathlib import Path
from typing import Dict, Any

from .config import ConfigLoader, ConfigValidator, ConfigInitializer
from .translator import AppTranslator
from .differ import ManifestDiffer
from .generator import ManifestGenerator
from .capacity_planner import CapacityPlanner
from .profile_generator import ProfileGenerator


class Maniforge:
    """Main Maniforge application"""
    
    def __init__(self, config_file: str = 'maniforge.yaml'):
        self.config_file = Path(config_file)
        self.config_loader = ConfigLoader(config_file)
        self.config = None
        self.platform_config = None
        self.apps_config = None
        self.translator = None
        self.validator = None
        self.capacity_planner = None
    
    def load_config(self):
        """Load configuration"""
        self.config_loader.load()
        self.config = self.config_loader.config
        self.platform_config = self.config_loader.platform_config
        self.apps_config = self.config_loader.apps_config
        
        # Initialize components
        self.translator = AppTranslator(self.platform_config)
        self.validator = ConfigValidator(self.apps_config, self.platform_config)
        self.capacity_planner = CapacityPlanner(self.platform_config)
    
    def validate(self):
        """Validate configuration"""
        return self.validator.validate()
    
    def plan(self):
        """Show what changes would be made (like terraform plan)"""
        print("🔍 Validating configuration...")
        if not self.validate():
            sys.exit(1)
        
        print("✅ Configuration is valid")
        print("\n📋 Generating plan...")
        
        output_dir = Path(self.config.get('output', {}).get('directory', 'apps'))
        
        differ = ManifestDiffer()
        differ.load_current_state(output_dir)
        differ.load_desired_state(self)
        
        changes = differ.get_changes()
        differ.print_changes(changes)
        
        # Add capacity planning analysis
        analysis = self.capacity_planner.analyze_capacity(self.apps_config)
        self.capacity_planner.print_capacity_analysis(analysis)
        
        return len(changes) > 0
    
    def apply(self):
        """Apply changes (like terraform apply)"""
        print("🔍 Validating configuration...")
        if not self.validate():
            sys.exit(1)
        
        print("✅ Configuration is valid")
        print("\n🔧 Applying changes...")
        
        output_dir = Path(self.config.get('output', {}).get('directory', 'apps'))
        
        generator = ManifestGenerator(self.apps_config, self.platform_config, self.translator)
        generator.generate(output_dir)
        
        print("\n✅ Apply complete!")
    
    @staticmethod
    def init(config_file: str, cluster_name: str = 'firefly'):
        """Initialize a new maniforge project"""
        ConfigInitializer.init(Path(config_file), cluster_name)
    
    @staticmethod
    def generate_profiles(output_dir: str = None, profiles_yaml: str = 'resource-profiles.yaml'):
        """Generate Kubernetes resource profile components"""
        print("📦 Generating resource profile components...")
        
        generator = ProfileGenerator(profiles_yaml)
        try:
            generator.load_profiles()
        except FileNotFoundError as e:
            print(f"❌ {e}")
            sys.exit(1)
        
        if output_dir is None:
            output_dir = '_components/resource-profiles'
        
        generator.generate_components(Path(output_dir))
