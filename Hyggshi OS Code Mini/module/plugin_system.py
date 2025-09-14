"""
Plugin System for Hyggshi OS Code Mini
Allows dynamic loading and management of plugins
"""

import os
import sys
import importlib
import inspect
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import json
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget, QMenu, QAction

class PluginInterface(ABC):
    """Base interface for all plugins"""
    
    def __init__(self):
        self.name = "Unknown Plugin"
        self.version = "1.0.0"
        self.description = "No description"
        self.author = "Unknown"
        self.enabled = True
        
    @abstractmethod
    def initialize(self, main_window):
        """Initialize the plugin with main window reference"""
        pass
        
    @abstractmethod
    def cleanup(self):
        """Cleanup when plugin is disabled/unloaded"""
        pass
        
    def get_menu_items(self) -> List[QAction]:
        """Return menu items for this plugin"""
        return []
        
    def get_toolbar_items(self) -> List[QWidget]:
        """Return toolbar items for this plugin"""
        return []
        
    def get_settings_widget(self) -> Optional[QWidget]:
        """Return settings widget for this plugin"""
        return None
        
    def get_supported_languages(self) -> Dict[str, Dict[str, Any]]:
        """Return supported languages for this plugin"""
        return {}

class PluginManager(QObject):
    """Manages plugin loading, unloading, and communication"""
    
    # Signals
    plugin_loaded = pyqtSignal(str)  # plugin_name
    plugin_unloaded = pyqtSignal(str)  # plugin_name
    plugin_error = pyqtSignal(str, str)  # plugin_name, error_message
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.plugins: Dict[str, PluginInterface] = {}
        self.plugin_configs = {}
        # Python plugins directory
        self.python_plugin_dir = os.path.join(os.path.dirname(__file__), "plugins")
        # Hyggshi plugin files directory (at root level)
        self.hsi_plugin_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")
        self.config_file = os.path.join(self.python_plugin_dir, "plugin_config.json")
        print(f"Python plugin directory: {self.python_plugin_dir}")
        print(f"Python plugin directory exists: {os.path.exists(self.python_plugin_dir)}")
        print(f"HSI plugin directory: {self.hsi_plugin_dir}")
        print(f"HSI plugin directory exists: {os.path.exists(self.hsi_plugin_dir)}")
        
        # Ensure plugin directories exist
        os.makedirs(self.python_plugin_dir, exist_ok=True)
        os.makedirs(self.hsi_plugin_dir, exist_ok=True)
        
        # Load plugin configurations
        self.load_plugin_configs()
        
    def load_plugin_configs(self):
        """Load plugin configurations from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.plugin_configs = json.load(f)
        except Exception as e:
            print(f"Error loading plugin configs: {e}")
            self.plugin_configs = {}
            
    def save_plugin_configs(self):
        """Save plugin configurations to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.plugin_configs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving plugin configs: {e}")
            
    def discover_plugins(self) -> List[str]:
        """Discover available plugins in both Python and HSI plugin directories"""
        plugins = []
        
        # Discover Python plugins
        if os.path.exists(self.python_plugin_dir):
            print(f"Scanning Python plugin directory: {self.python_plugin_dir}")
            for item in os.listdir(self.python_plugin_dir):
                if item.endswith('.py') and not item.startswith('__'):
                    plugin_name = item[:-3]  # Remove .py extension
                    plugins.append(plugin_name)
                    print(f"Found Python plugin: {plugin_name}")
        else:
            print(f"Python plugin directory does not exist: {self.python_plugin_dir}")
            
        # Discover HSI plugins
        if os.path.exists(self.hsi_plugin_dir):
            print(f"Scanning HSI plugin directory: {self.hsi_plugin_dir}")
            for item in os.listdir(self.hsi_plugin_dir):
                if item.endswith('.hsi') and not item.startswith('__'):
                    plugin_name = item[:-4]  # Remove .hsi extension
                    plugins.append(plugin_name)
                    print(f"Found HSI plugin: {plugin_name}")
        else:
            print(f"HSI plugin directory does not exist: {self.hsi_plugin_dir}")
                
        print(f"Total plugins found: {len(plugins)}")
        return plugins
        
    def load_plugin(self, plugin_name: str) -> bool:
        """Load a specific plugin"""
        try:
            print(f"Loading plugin: {plugin_name}")
            # Check if plugin is already loaded
            if plugin_name in self.plugins:
                print(f"Plugin {plugin_name} already loaded")
                return True
                
            # Check if plugin is disabled
            if not self.plugin_configs.get(plugin_name, {}).get('enabled', True):
                print(f"Plugin {plugin_name} is disabled")
                return False
                
            # Check if it's a Python plugin or HSI plugin
            python_plugin_path = os.path.join(self.python_plugin_dir, f"{plugin_name}.py")
            hsi_plugin_path = os.path.join(self.hsi_plugin_dir, f"{plugin_name}.hsi")
            
            if os.path.exists(python_plugin_path):
                # Load Python plugin
                print(f"Loading Python plugin: {plugin_name}")
                return self._load_python_plugin(plugin_name, python_plugin_path)
            elif os.path.exists(hsi_plugin_path):
                # Load HSI plugin
                print(f"Loading HSI plugin: {plugin_name}")
                return self._load_hsi_plugin(plugin_name, hsi_plugin_path)
            else:
                error_msg = f"Plugin file not found: {python_plugin_path} or {hsi_plugin_path}"
                print(error_msg)
                self.plugin_error.emit(plugin_name, error_msg)
                return False
                
        except Exception as e:
            error_msg = f"Error loading plugin: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            self.plugin_error.emit(plugin_name, error_msg)
            return False
                
    def _load_python_plugin(self, plugin_name: str, plugin_path: str) -> bool:
        """Load a Python plugin"""
        try:
            # Add plugin directory to Python path
            if self.python_plugin_dir not in sys.path:
                sys.path.insert(0, self.python_plugin_dir)
                
            # Import the module
            print(f"Importing Python module: {plugin_name}")
            module = importlib.import_module(plugin_name)
            
            # Find plugin class (should be named Plugin)
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, PluginInterface) and 
                    obj != PluginInterface):
                    plugin_class = obj
                    print(f"Found plugin class: {name}")
                    break
                    
            if not plugin_class:
                error_msg = "No valid plugin class found"
                print(error_msg)
                self.plugin_error.emit(plugin_name, error_msg)
                return False
                
            # Create plugin instance
            print(f"Creating plugin instance: {plugin_name}")
            plugin_instance = plugin_class()
            plugin_instance.initialize(self.main_window)
            
            # Store plugin
            self.plugins[plugin_name] = plugin_instance
            print(f"Python plugin {plugin_name} loaded successfully")
            
            # Emit signal
            self.plugin_loaded.emit(plugin_name)
            
            return True
            
        except Exception as e:
            error_msg = f"Error loading Python plugin: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            self.plugin_error.emit(plugin_name, error_msg)
            return False
            
    def _load_hsi_plugin(self, plugin_name: str, plugin_path: str) -> bool:
        """Load an HSI plugin file"""
        try:
            # Read HSI plugin file
            with open(plugin_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # Parse HSI plugin content (simple format)
            lines = content.split('\n')
            plugin_info = {
                'name': plugin_name.title(),
                'version': '1.0.0',
                'description': f'Language support for {plugin_name.upper()}',
                'author': 'Hyggshi OS',
                'enabled': True
            }
            
            # Create a simple plugin instance for HSI files
            class HSIPlugin(PluginInterface):
                def __init__(self, info):
                    super().__init__()
                    self.name = info['name']
                    self.version = info['version']
                    self.description = info['description']
                    self.author = info['author']
                    self.enabled = info['enabled']
                    self.language = plugin_name.lower()
                    
                def initialize(self, main_window):
                    self.main_window = main_window
                    
                def cleanup(self):
                    pass
                    
                def get_supported_languages(self):
                    return {
                        self.language.title(): {
                            'extension': f'.{self.language}',
                            'plugin': 'hsi_plugin'
                        }
                    }
            
            # Create plugin instance
            plugin_instance = HSIPlugin(plugin_info)
            plugin_instance.initialize(self.main_window)
            
            # Store plugin
            self.plugins[plugin_name] = plugin_instance
            print(f"HSI plugin {plugin_name} loaded successfully")
            
            # Emit signal
            self.plugin_loaded.emit(plugin_name)
            
            return True
            
        except Exception as e:
            error_msg = f"Error loading HSI plugin: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            self.plugin_error.emit(plugin_name, error_msg)
            return False
            
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a specific plugin"""
        try:
            if plugin_name not in self.plugins:
                return False
                
            # Cleanup plugin
            plugin = self.plugins[plugin_name]
            plugin.cleanup()
            
            # Remove from plugins dict
            del self.plugins[plugin_name]
            
            # Emit signal
            self.plugin_unloaded.emit(plugin_name)
            
            return True
            
        except Exception as e:
            self.plugin_error.emit(plugin_name, f"Error unloading plugin: {str(e)}")
            return False
            
    def load_all_plugins(self):
        """Load all available plugins"""
        plugins = self.discover_plugins()
        for plugin_name in plugins:
            self.load_plugin(plugin_name)
            
    def get_plugin(self, plugin_name: str) -> Optional[PluginInterface]:
        """Get a specific plugin instance"""
        return self.plugins.get(plugin_name)
        
    def get_all_plugins(self) -> Dict[str, PluginInterface]:
        """Get all loaded plugins"""
        return self.plugins.copy()
        
    def enable_plugin(self, plugin_name: str):
        """Enable a plugin"""
        if plugin_name not in self.plugin_configs:
            self.plugin_configs[plugin_name] = {}
        self.plugin_configs[plugin_name]['enabled'] = True
        self.save_plugin_configs()
        
    def disable_plugin(self, plugin_name: str):
        """Disable a plugin"""
        if plugin_name not in self.plugin_configs:
            self.plugin_configs[plugin_name] = {}
        self.plugin_configs[plugin_name]['enabled'] = False
        self.save_plugin_configs()
        
        # Unload if currently loaded
        if plugin_name in self.plugins:
            self.unload_plugin(plugin_name)
            
    def get_plugin_menu_items(self) -> List[QAction]:
        """Get all menu items from loaded plugins"""
        menu_items = []
        for plugin in self.plugins.values():
            try:
                items = plugin.get_menu_items()
                menu_items.extend(items)
            except Exception as e:
                print(f"Error getting menu items from plugin: {e}")
        return menu_items
        
    def get_plugin_toolbar_items(self) -> List[QWidget]:
        """Get all toolbar items from loaded plugins"""
        toolbar_items = []
        for plugin in self.plugins.values():
            try:
                items = plugin.get_toolbar_items()
                toolbar_items.extend(items)
            except Exception as e:
                print(f"Error getting toolbar items from plugin: {e}")
        return toolbar_items
        
    def get_supported_languages(self) -> Dict[str, Dict[str, Any]]:
        """Get supported languages from all plugins"""
        languages = {}
        for plugin_name, plugin in self.plugins.items():
            try:
                if hasattr(plugin, 'get_supported_languages'):
                    plugin_langs = plugin.get_supported_languages()
                    if isinstance(plugin_langs, dict):
                        languages.update(plugin_langs)
                    elif isinstance(plugin_langs, list):
                        # Convert list to dict format
                        for lang in plugin_langs:
                            if isinstance(lang, str):
                                languages[lang] = {
                                    'extension': f'.{lang.lower()}',
                                    'plugin': plugin_name
                                }
            except Exception as e:
                print(f"Error getting languages from plugin {plugin_name}: {e}")
        return languages

class PluginRegistry:
    """Registry for plugin metadata and dependencies"""
    
    def __init__(self):
        self.registry = {}
        
    def register_plugin(self, name: str, metadata: Dict[str, Any]):
        """Register plugin metadata"""
        self.registry[name] = metadata
        
    def get_plugin_info(self, name: str) -> Dict[str, Any]:
        """Get plugin information"""
        return self.registry.get(name, {})
        
    def check_dependencies(self, plugin_name: str) -> List[str]:
        """Check if plugin dependencies are met"""
        plugin_info = self.get_plugin_info(plugin_name)
        dependencies = plugin_info.get('dependencies', [])
        missing = []
        
        for dep in dependencies:
            if dep not in self.registry:
                missing.append(dep)
                
        return missing

# Global plugin manager instance
plugin_manager = None

def get_plugin_manager() -> Optional[PluginManager]:
    """Get the global plugin manager instance"""
    return plugin_manager

def set_plugin_manager(manager: PluginManager):
    """Set the global plugin manager instance"""
    global plugin_manager
    plugin_manager = manager
