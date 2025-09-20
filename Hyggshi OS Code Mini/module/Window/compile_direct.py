"""
Direct Cython compilation script
"""
import os
import sys
from Cython.Build import cythonize
from setuptools import setup
from setuptools.extension import Extension

def compile_cython_module():
    """Compile Cython module directly"""
    
    # Define the extension
    pyx_file = "quick_window_deployment_cython.pyx"
    
    if not os.path.exists(pyx_file):
        print(f"❌ Error: {pyx_file} not found!")
        print(f"Current directory: {os.getcwd()}")
        print(f"Files in directory: {os.listdir('.')}")
        return False
    
    # Create extension
    extensions = [
        Extension(
            "quick_window_deployment_cython",
            [pyx_file],
        )
    ]
    
    # Override sys.argv to provide build command
    original_argv = sys.argv[:]
    sys.argv = [sys.argv[0], "build_ext", "--inplace"]
    
    try:
        setup(
            name="QuickWindowDeployment",
            ext_modules=cythonize(extensions),
            zip_safe=False,
        )
        print("✅ Compilation successful!")
        return True
        
    except Exception as e:
        print(f"❌ Compilation failed: {e}")
        return False
        
    finally:
        # Restore original argv
        sys.argv = original_argv

if __name__ == "__main__":
    print("🔧 Direct Cython Compiler")
    print("=" * 30)
    
    if compile_cython_module():
        print("🎉 Module compiled successfully!")
        print("You can now import and use: quick_window_deployment_cython")
    else:
        print("💥 Compilation failed!")