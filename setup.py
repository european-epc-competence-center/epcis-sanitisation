import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="epcis-sanitiser",
    keywords="epcis GS1 hashing sanitisation traceability",
    version="1.0.0",
    author="Sebastian Schmittner",
    author_email="sebastian.schmittner@eecc.de",
    license="MIT",
    description="PoC implementation of the EPCIS Sanitiser. See the README for details.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/european-epc-competence-center/epcis-sanitisation",
    packages=["epcis_event_hash_generator"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points={
        "console_scripts": [
            "cli=epcis_event_hash_generator.main:main",
            "webservice=epcis_event_hash_generator.webservice:main"
        ]
    },
    install_requires=[
        'epcis_event_hash_generator>=1.6.2',
        'fastapi>=0.63.0',
        'uvicorn>=0.13.4',
        'tinydb>=4.4.0'
    ],
)
