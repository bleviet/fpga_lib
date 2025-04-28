from setuptools import setup, find_packages

setup(
    name="fpga_lib",
    version="0.1.0",
    description="A library for FPGA IP core modeling and code generation.",
    author="",
    author_email="",
    url="",
    packages=find_packages(),
    install_requires=[
        "dataclasses",
        "jinja2"
    ],
    extras_require={
        "dev": [
            "mypy>=0.910",
            "pytest>=6.0"
        ]
    },
    python_requires=">=3.7",
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)
