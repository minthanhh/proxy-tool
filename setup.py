from setuptools import setup, find_packages

setup(
    name="easyproxy",
    version="0.1.0",
    description="Proxy IP desktop app for rate limit bypass",
    packages=find_packages(include=["easyproxy", "easyproxy.*"]),
    python_requires=">=3.11",
)
