import setuptools
from aytool import version

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="aytool",
    version=version,
    author="ayiis",
    author_email="ayiis@126.com",
    description="ayiis's python tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ayiis/aytool",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
