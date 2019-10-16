from setuptools import find_packages, setup

import title_grabber

with open('README.md') as fh: long_description = fh.read()

setup(
    name='title_grabber-cristianrasch',
    version=title_grabber.version,
    author='Cristian Rasch',
    author_email='cristianrasch@fastmail.fm',
    description='Grabs page & article titles from lists of URLs contained in files passed in as arguments',
    long_description=long_description,
    long_description_content_type='text/markdown',
    py_modules=['title_grabber'],
    package_dir={'': 'title_grabber'},
    url='https://github.com/cristianrasch/title_grabber',
    packages=find_packages(),
    include_package_data=False,
    zip_safe=False,
    install_requires=[
        'requests >=2.0,<3.0',
        'beautifulsoup4 >=4.0,<5.0',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
