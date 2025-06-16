from setuptools import setup, find_packages

setup(
    name="mangoapi",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["Django>=4.2", "uvicorn>=0.34.3", "starlette>=0.47.0"],
    entry_points={"console_scripts": ["mangoapi=mangoapi.cli:main"]},
    include_package_data=True,
    description="Modern lightweight framework for building async APIs on top of Django",
    author="Leandro Carriego",
    author_email="leandro.carriego@mendrisoftware.com",
    url="https://github.com/leandrocariego/mangoapi",
)
