from setuptools import setup, find_packages

with open("README.md", "r") as readme_file:
    readme = readme_file.read()

requirements = [
    "websockets",
]

setup(
    name="wsgateway",
    version="0.0.3",
    author="leopf",
    author_email="",
    description="",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="",
    packages=[ "wsgateway", "wsgateway.tools" ],
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3.9",
    ],
    entry_points = {
        "console_scripts": [
            "wsgw-gateway=wsgateway.tools.gateway:main",
            "wsgw-provider=wsgateway.tools.provider:main",
            "wsgw-client=wsgateway.tools.client:main",
        ]
    }
)