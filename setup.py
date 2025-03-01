from setuptools import setup, find_packages

setup(
    name="hwae",
    version="1.0.0",
    packages=find_packages() + ['src.fileio'],
    include_package_data=True,
    install_requires=[
        "altgraph==0.17.4",
        "colorama==0.4.6",
        "iniconfig==2.0.0",
        "numpy==2.2.3",
        "packaging==24.2",
        "pefile==2023.2.7",
        "pluggy==1.5.0",
        "pyinstaller==6.12.0",
        "pyinstaller-hooks-contrib==2025.1",
        "pytest==8.3.4",
        "pywin32-ctypes==0.2.3",
        "setuptools==75.8.0",
        "sv-ttk==2.6.0",
        "wheel==0.45.1",
        "pillow",  
        "perlin-numpy @ git+https://github.com/pvigier/perlin-numpy@5e26837db14042e51166eb6cad4c0df2c1907016"
    ],
)
