title_grabber
=============


Usage instructions
------------------

* Just feed it 1 or more files containing URLs (1 per line)

`python -m title_grabber /abs/path/2/urls1.csv rel/path/2/urls2.csv`

* Optionally, change the output file:

`python -m title_grabber -o output.csv /abs/path/2/urls1.csv rel/path/2/urls2.csv`

* See all available config options:

`python -m title_grabber -h`

    usage: title_grabber [-h] [-o OUT_FILE] [--connect-timeout TIMEOUT]
                         [--read-timeout TIMEOUT] [-r RETRIES] [-t THREADS] [-d]
                         [FILES [FILES ...]]

    positional arguments:
      FILES                 1 or more CSV files containing URLs (1 per line)

    optional arguments:
      -h, --help            show this help message and exit
      -o OUT_FILE, --output OUT_FILE
                            Output file (defaults to out.csv)
      --connect-timeout TIMEOUT
                            HTTP connect timeout. Defaults to the value of the
                            CONNECT_TIMEOUT env var or 10
      --read-timeout TIMEOUT
                            HTTP read timeout. Defaults to the value of the
                            READ_TIMEOUT env var or 15
      -r RETRIES, --max-retries RETRIES
                            Max. # of times to retry failed HTTP reqs. Defaults to
                            the value of the MAX_RETRIES env var or 3
      -t THREADS, --max-threads THREADS
                            Max. # of threads to use. Defaults to the value of the
                            MAX_THREADS env var or the # of logical processors in
                            the system (8)
      -d, --debug           Log to STDOUT instead of to a file in the CWD.
                            Defaults to the value of the DEBUG env var or False

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
