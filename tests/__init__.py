import os
import unittest

def test_suite():
    return unittest.TestLoader().discover(os.path.dirname(__file__))

def main():
    try:
        unittest.main()
    except Exception as e:
        print('Exception: %s' % e)

def run():
    test_runner = unittest.TextTestRunner()
    return test_runner.run(testsuite())
