from setuptools import setup, find_packages

with open("README.md", "r") as readme_file:
    readme = readme_file.read()

requirements = [
    "websockets",
]

setup(
    name="wsgateway",
    version="0.0.1",
    author="leopf",
    author_email="",
    description="",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="",
    packages=[ "wsgateway" ],
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3.9",
    ],
    scripts=[]
)