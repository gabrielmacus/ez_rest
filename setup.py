from setuptools import find_packages, setup

with open("app/README.md", "r") as f:
    long_description = f.read()

setup(
    name='ez_rest',
    url='https://github.com/gabrielmacus/ez_rest',
    license='MIT',
    author='gabrielmacus',
    author_email='gabrielmacus@gmail.com',
    version='0.1.0',
    packages=find_packages(exclude=['tests']),
    long_description=long_description,
    long_description_content_type="text/markdown",
    description="",
    install_requires=[
        "bcrypt>=^4.1.1",
        "fastapi>=^0.104.1",
        "passlib>=^1.7.4",
        "python-jose>=^3.3.0",
        "sqlalchemy>=^2.0.23"
    ],
    extras_require={
        "dev": ["pytest==7.4.3", 
                "twine==4.0.2", 
                "time-machine==2.13.0",
                "pytest-cov==4.1.0"],
    },
    python_requires=">=3.10",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
)