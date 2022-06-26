"""Setup file for package."""
from setuptools import find_packages, setup

setup(
    name="watermark",
    version_config=True,
    packages=find_packages(include=["src*"]),
    description="Automating PDF watermarking.",
    entry_points={
        "console_scripts": [
            "watermark=src.main:main",
        ]
    },
    install_requires=["PyPDF2", "reportlab", "tqdm"],
    setuptools_git_versioning={"enabled": True},
)
