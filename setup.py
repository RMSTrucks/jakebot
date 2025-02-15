from setuptools import setup, find_packages

setup(
    name="jakebot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'aiohttp>=3.8.0',
        'requests>=2.28.0',
        'pytest>=7.0.0',
        'pytest-asyncio>=0.18.0',
        'pytest-cov>=3.0.0',
        'psutil>=5.9.0',
        'python-dotenv>=0.19.0',
        'pydantic>=1.9.0',
        'structlog>=21.5.0',
    ],
    python_requires='>=3.9',
) 