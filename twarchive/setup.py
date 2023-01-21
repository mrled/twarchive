import setuptools


long_description = """
# twarchive

A companion package for the twarchive Hugo theme.
This package makes it easy to download tweets in the format that the Hugo theme expects.

For more information, see
<https://github.com/mrled/twarchive>
"""


version_ns = {}
with open("twarchive/version.py") as vfp:
    exec(vfp.read(), version_ns)


setuptools.setup(
    name="twarchive",
    version=version_ns["__version__"],
    author="Micah R Ledbetter",
    author_email="me@micahrl.com",
    description="Download tweets for use with the twarchive Hugo theme",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mrled/twarchive/",
    packages=["twarchive", "twarchive.inflatedtweet"],
    python_requires=">=3.9",
    include_package_data=True,
    install_requires=["tweepy"],
    setup_requires=[
        "black",
        "mypy",
        "pytest",
    ],
    entry_points={
        "console_scripts": ["twarchive=twarchive.cli:main"],
    },
)
