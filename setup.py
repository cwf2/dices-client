import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dices-client",
    version="0.0.2",
    author="Chris Forstall",
    author_email="cforstall@gmail.com",
    description="Tools work interacting with the DICES database of Greek and Latin epic speeches",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cwf2/dices-client",
    project_urls={
        "Bug Tracker": "https://github.com/cwf2/dices-client",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.10",
    install_requires=[
        "requests",
        "numpy==1.26.4",
        "pandas",
        "cltk",
        "spacy",
        "MyCapytain",
    ]
)