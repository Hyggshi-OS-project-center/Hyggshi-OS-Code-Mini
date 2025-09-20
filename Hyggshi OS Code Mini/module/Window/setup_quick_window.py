
from setuptools import setup
from Cython.Build import cythonize
import os
import sys

# Get the directory where this setup.py file is located
current_dir = os.path.dirname(os.path.abspath(__file__))
pyx_file = os.path.join(current_dir, "quick_window_deployment_cython.pyx")

# Check if the .pyx file exists
if not os.path.exists(pyx_file):
    print(f"Error: {pyx_file} not found!")
    print(f"Current directory: {current_dir}")
    print(f"Files in directory: {os.listdir(current_dir)}")
    exit(1)

# If no command line arguments provided, add the build command
if len(sys.argv) == 1:
    sys.argv.extend(['build_ext', '--inplace'])

setup(
    name="QuickWindowDeployment",
    ext_modules=cythonize(pyx_file),
    zip_safe=False,
)