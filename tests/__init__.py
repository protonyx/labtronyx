import os
import unittest

def test_suite():
    return unittest.TestLoader().discover(os.path.dirname(__file__))

def main():
    unittest.main()

def run():
    test_runner = unittest.TextTestRunner()
    return test_runner.run(test_suite())
