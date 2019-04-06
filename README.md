title_grabber
=============


Usage instructions
------------------

* Just feed it 1 or more files containing URLs (1 per line)

`title_grabber /abs/path/2/urls1.csv rel/path/2/urls2.csv`

* Optionally, change the output file:

`title_grabber -o output.csv /abs/path/2/urls1.csv rel/path/2/urls2.csv`

* Get help:

`title_grabber -h`

dev setup instructions
----------------------

1. Clone the project

`git clone git@github.com:cristianrasch/title_grabber.git`

2. Create a new virtual environment for it

`cd title_grabber && python3 -m venv venv`

3. Install its dependencies

`pip install -r requirements.txt`

4. Run the test suite to make sure everything is set up OK

`python -m unittest discover -v -s title_grabber/tests/`
