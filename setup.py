from setuptools import setup, find_packages
import os

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Define default requirements in case requirements.txt is not found
default_requirements = [
    "click>=8.0.0",
    "requests>=2.25.0",
    "tabulate>=0.8.0",
    "pyyaml>=5.4.0",
    "colorama>=0.4.4",
    "cryptography>=3.4.0",
    "jsonschema>=4.0.0"
]

# Try to read requirements from file, use default if file not found
requirements = default_requirements
if os.path.exists("requirements.txt"):
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="porkbun-cli",
    version="0.3.0",
    author="ragelink",
    author_email="ragelink@ragelink.com",
    description="A command-line interface for Porkbun domain management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ragelink/porkbun-cli",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: Name Service (DNS)",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "porkbun=porkbun.cli:cli",
        ],
    },
)
