from setuptools import setup, find_packages

setup(
    name="app",
    version="1.0",
    description="Textscopr repogitory",
    author="Lomin",
    author_email="***@lomin.ai",
    install_requires=[],
    packages=find_packages(),
    python_requires=">=3",
    package_data={"app": []},
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
