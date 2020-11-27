import unittest
import coverage


cov = coverage.Coverage(include='src/mbfxml2ex/*')
cov.erase()
cov.start()

import test_mbfxml2ex

suite = unittest.TestSuite()
suite.addTest(unittest.defaultTestLoader.loadTestsFromName('test_mbfxml2ex'))
unittest.TextTestRunner().run(suite)

cov.stop()
cov.save()

cov.report()
cov.html_report(directory='htmlcov')
