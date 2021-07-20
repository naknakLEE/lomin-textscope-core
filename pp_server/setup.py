from setuptools import setup, find_packages

setup(
    name="pp_server",
    version="1.0",
    description="Textscope post processing",
    author="Lomin",
    author_email="***@lomin.ai",
    install_requires=[],
    packages=find_packages(),
    python_requires=">=3",
    package_data={"pp_server": []},
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
