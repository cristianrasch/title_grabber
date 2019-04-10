from setuptools import find_packages, setup

with open('README.md') as fh: long_description = fh.read()

setup(
    name='title_grabber-cristianrasch',
    version='0.1.0',
    author='Cristian Rasch',
    author_email='cristianrasch@fastmail.fm',
    description='Grabs page & article titles from lists of URLs contained in files passed in as arguments',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/cristianrasch/title_grabber',
    packages=find_packages(),
    include_package_data=False,
    zip_safe=False,
    install_requires=[
        'requests',
        'beautifulsoup4',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
