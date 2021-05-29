import pathlib
from setuptools import setup

from dpixels import __version__

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name="dpixels",
    author="Circuit",
    url="https://github.com/CircuitSacul/dpixels",
    version=__version__,
    packages=["dpixels"],
    license="MIT",
    description="A(nother) wrapper for the Python Discord Pixels API.",
    long_description=README,
    long_description_content_type="text/markdown",
    install_requires=["Pillow", "aiohttp"],
    python_requires=">=3.7",
)
