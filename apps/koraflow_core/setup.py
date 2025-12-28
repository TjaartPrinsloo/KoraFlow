from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="koraflow_core",
    version="1.0.0",
    description="KoraFlow Core - White-label modular enterprise platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="KoraFlow Team",
    author_email="team@koraflow.io",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=[],
)

