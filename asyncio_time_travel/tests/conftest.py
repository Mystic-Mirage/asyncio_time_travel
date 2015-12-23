import sys


def pytest_ignore_collect(path,config):
    """
    Return True to prevent considering this path for collection
    """
    # Don't run the py35 tests if the python version is less than 3.5
    if 'py35' in str(path):
        if sys.version_info < (3,5,0):
            return True

