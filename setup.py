from setuptools import setup, find_packages

with open("README_PUBLICATION.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="dms-document-management",
    version="1.0.0",
    author="DMS Contributors",
    author_email="support@dms-project.com",
    description="Production-ready Document Management System with FastAPI and MySQL",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/dms",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/dms/issues",
        "Documentation": "https://github.com/yourusername/dms/blob/main/README_PUBLICATION.md",
        "Source Code": "https://github.com/yourusername/dms",
    },
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Office/Business",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.0",
            "flake8>=6.0",
            "pylint>=2.17",
            "mypy>=1.0",
        ],
        "docker": [
            "docker>=6.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "dms=main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
