import cProfile
import pstats
import io
import unittest
import argparse
import importlib


def run_tests(test_case_class_name=None, test_method_name=None):
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    module = importlib.import_module('test_mbfxml2ex')

    if test_case_class_name:
        test_case_class = getattr(module, test_case_class_name)
        if test_method_name:
            suite.addTest(test_case_class(test_method_name))
        else:
            suite.addTests(loader.loadTestsFromTestCase(test_case_class))
    else:
        suite.addTests(loader.loadTestsFromModule(module))

    runner = unittest.TextTestRunner()
    runner.run(suite)


def _parse_args():
    parser = argparse.ArgumentParser(description='Profile unittest test cases.')
    parser.add_argument('-c', '--test-case-class', help='Name of the test case class (e.g., ExWritingTreeTestCase)')
    parser.add_argument('-m', '--test-method', help='Name of the test method (e.g., test_tree_order)')
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()

    pr = cProfile.Profile()
    pr.enable()

    run_tests(args.test_case_class, args.test_method)

    pr.disable()
    s = io.StringIO()
    sort_by = 'cumulative'
    ps = pstats.Stats(pr, stream=s).sort_stats(sort_by)
    ps.print_stats(20)
    print(s.getvalue())
