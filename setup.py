from setuptools import find_packages, setup

setup(
    name='title_grabber',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=False,
    zip_safe=False,
    install_requires=[
        'requests',
        'beautifulsoup4',
    ],
)
