from setuptools import find_packages, setup

setup(
    name="cricstats",
    url="https://github.com/LiamBlake/cricstats",
    author="Liam Blake",
    author_email="",
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=["pandas", "pyreadr", "bs4"],
    extras_require={"dev": ["flake8", "black", "isort"]},
)
