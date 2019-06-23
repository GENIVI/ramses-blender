import sys
import os
# TODO: Improve this, how is this not in there already?
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import unittest

def run():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase()
    success = unittest.TextTestRunner().run(suite).wasSuccessful()
    if not success:
        raise Exception('Unit tests failed')

run()
