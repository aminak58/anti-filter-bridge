from setuptools import setup, find_packages
from pathlib import Path

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="anti_filter_bridge",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A secure tunnel to bypass internet restrictions"
              " using WebSockets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/anti-filter-bridge",
    packages=find_packages(include=['anti_filter_bridge*']),
    package_dir={'': '.'},
    install_requires=[
        'websockets>=10.0',
        'click>=8.0.0',
        'python-dotenv>=0.19.0',
        'psutil>=5.9.0',
        'fastapi>=0.75.0',
        'uvicorn>=0.17.0',
        'jinja2>=3.0.0',
        'aiohttp>=3.8.0',
        'aiohttp-socks>=0.8.0',
    ],
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'afb=anti_filter_bridge.cli:main',
            'afb-monitor=scripts.monitor:main',
            'afb-config=scripts.config_generator:main',
        ],
    },
    package_data={
        '': [
            '*.md',
            '*.txt',
            '*.ini'
        ],
    },
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Internet :: Proxy Servers",
        "Topic :: Security",
    ],
    keywords='proxy tunnel websocket socks5 anti-filter',
    project_urls={
        "Bug Reports": "https://github.com/yourusername/anti-filter-bridge/issues",
        "Source": "https://github.com/yourusername/anti-filter-bridge",
    },
)
