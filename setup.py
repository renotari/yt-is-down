#!/usr/bin/env python3
"""
Setup script for YouTube Downloader
A secure, user-friendly YouTube video downloader with GUI and CLI interfaces.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="youtube-downloader-secure",
    version="2.0.0",
    author="YouTube Downloader Team",
    author_email="contact@example.com",
    description="A secure, user-friendly YouTube video downloader with GUI and CLI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/renotari/yt-is-down",
    project_urls={
        "Bug Reports": "https://github.com/renotari/yt-is-down/issues",
        "Source": "https://github.com/renotari/yt-is-down",
        "Documentation": "https://github.com/renotari/yt-is-down/blob/main/README.md",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Video",
        "Topic :: Internet :: WWW/HTTP",
        "Environment :: X11 Applications :: Qt",
        "Environment :: Win32 (MS Windows)",
        "Environment :: MacOS X",
    ],
    python_requires=">=3.7",
    install_requires=[
        "yt-dlp>=2023.12.30",
        "typing-extensions>=4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
    },
    entry_points={
        "console_scripts": [
            "youtube-dl-gui=gui:main",
            "youtube-dl-cli=cli:main",
        ],
        "gui_scripts": [
            "youtube-downloader=gui:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml"],
        "config": ["*.py"],
        "docs": ["*.md"],
    },
    keywords="youtube downloader video audio mp3 mp4 playlist gui cli secure",
    license="MIT",
    zip_safe=False,
)