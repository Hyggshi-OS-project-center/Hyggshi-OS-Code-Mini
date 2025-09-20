#!/usr/bin/env python3
"""
Build script for Cython modules
"""
import os
import sys
import subprocess
from pathlib import Path

def build_cython_module():
    """Build the Cython module"""
    current_dir = Path(__file__).parent
    pyx_file = current_dir / "quick_window_deployment_cython.pyx"
    setup_file = current_dir / "setup_quick_window.py"
    
    # Check if files exist
    if not pyx_file.exists():
        print(f"❌ Error: {pyx_file} not found!")
        return False
        
    if not setup_file.exists():
        print(f"❌ Error: {setup_file} not found!")
        return False
    
    print(f"📁 Working directory: {current_dir}")
    print(f"🔧 Building Cython module from: {pyx_file.name}")
    
    try:
        # Run the setup command
        cmd = [sys.executable, str(setup_file), "build_ext", "--inplace"]
        print(f"🚀 Running: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, cwd=current_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Build successful!")
            print("Generated files:")
            for file in current_dir.glob("*.so"):  # Unix/Linux/Mac
                print(f"  📦 {file.name}")
            for file in current_dir.glob("*.pyd"):  # Windows
                print(f"  📦 {file.name}")
            for file in current_dir.glob("*.c"):  # Generated C files
                print(f"  🗂️  {file.name}")
            return True
        else:
            print("❌ Build failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error during build: {e}")
        return False

def test_module():
    """Test the compiled module"""
    try:
        print("\n🧪 Testing the compiled module...")
        # Ensure current directory is in sys.path
        import sys
        from pathlib import Path
        current_dir = Path(__file__).parent
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))
        # Import and test the module
        import importlib
        import sys
        import os

        # Try to import the compiled module (.pyd on Windows, .so on Unix)
        module_name = "quick_window_deployment_cython"
        try:
            mod = importlib.import_module(module_name)
        except ImportError:
            # Try to load from file if direct import fails
            import glob
            files = glob.glob(str(current_dir / (module_name + ".*")))
            ext_file = next((f for f in files if f.endswith((".pyd", ".so"))), None)
            if ext_file:
                import importlib.util
                spec = importlib.util.spec_from_file_location(module_name, ext_file)
                mod = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = mod
                spec.loader.exec_module(mod)
            else:
                raise ImportError(f"Compiled module file for {module_name} not found.")

        print("✅ Module imported successfully!")
        
        # You can add a test call here if needed
        # mod.show_quick_window("Test", "Module works!")
        
    except ImportError as e:
        print(f"❌ Failed to import module: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing module: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔨 Cython Module Builder")
    print("=" * 40)
    
    success = build_cython_module()
    
    if success:
        test_module()
        print("\n🎉 All done! Your Cython module is ready to use.")
    else:
        print("\n💥 Build process failed. Please check the errors above.")
        sys.exit(1)