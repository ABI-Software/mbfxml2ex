
import os
import unittest
from neurolucidaxml2ex import read_xml
from neurolucidaxml2ex import NeurolucidaPoint
from neurolucidaxml2ex import NeurolucidaData
from neurolucidaxml2ex import write_ex
from neurolucidaxml2ex import determine_connectivity
from neurolucidaxml2ex import reset_node_id

here = os.path.abspath(os.path.dirname(__file__))


class NeurolucidaXmlTestCase(unittest.TestCase):

    def test_not_existing_xml_file(self):
        xml_file = os.path.join(here, "resources", "missing.xml")
        contents = read_xml(xml_file)
        self.assertIsNone(contents)

    def test_read_xml(self):
        xml_file = os.path.join(here, "resources", "multi_tree.xml")
        contents = read_xml(xml_file)
        self.assertEqual(3, len(contents))

    def test_read_not_xml(self):
        not_xml_file = os.path.join(here, "resources", "random_file.txt")
        contents = read_xml(not_xml_file)
        self.assertIsNone(contents)


class NeurolucidaPointTestCase(unittest.TestCase):

    def test_point(self):
        p = NeurolucidaPoint(1, 2, 4, 5)
        self.assertListEqual([1, 2, 4], p.coordinates())
        self.assertEqual(5, p.radius())

    def test_point_set(self):
        p = NeurolucidaPoint(6, 3, 4, 9)
        self.assertListEqual([6, 3, 4, 9], p.get())


class DetermineConnectivityTestCase(unittest.TestCase):

    def test_determine_connectivity_basic(self):
        reset_node_id()
        tree = [NeurolucidaPoint(3, 3, 4, 2), NeurolucidaPoint(2, 1, 5, 7), NeurolucidaPoint(3, 1, 4.2, 7.1)]
        self.assertListEqual([[1, 2], [2, 3]], determine_connectivity(tree))

    def test_determine_connectivity_branch(self):
        reset_node_id()
        tree = [NeurolucidaPoint(3, 3, 4, 2), [NeurolucidaPoint(2, 1, 5, 7)], [NeurolucidaPoint(2, 4, 8, 5.7)]]
        self.assertListEqual([[1, 2], [1, 3]], determine_connectivity(tree))

    def test_determine_connectivity_multiple_branch(self):
        reset_node_id()
        tree = [NeurolucidaPoint(3, 3, 4, 2), NeurolucidaPoint(3, 3, 4, 2), NeurolucidaPoint(3, 3, 4, 2),
                [NeurolucidaPoint(2, 1, 5, 7), NeurolucidaPoint(2, 1, 5, 7), NeurolucidaPoint(2, 1, 5, 7),
                 [NeurolucidaPoint(2, 4, 8, 5.7), NeurolucidaPoint(2, 4, 8, 5.7), NeurolucidaPoint(2, 4, 8, 5.7),
                  NeurolucidaPoint(2, 4, 8, 5.7)],
                 [NeurolucidaPoint(2, 4, 8, 5.7), NeurolucidaPoint(2, 4, 8, 5.7), NeurolucidaPoint(2, 4, 8, 5.7)]],
                [NeurolucidaPoint(2, 4, 8, 5.7), NeurolucidaPoint(2, 4, 8, 5.7)]]
        self.assertListEqual([[1, 2], [2, 3], [3, 4]], determine_connectivity(tree))


class ExWritingTestCase(unittest.TestCase):

    def test_write_ex_basic(self):
        ex_file = os.path.join(here, "resources", "basic_tree.ex")
        if os.path.exists(ex_file):
            os.remove(ex_file)

        data = NeurolucidaData()
        data.add_tree([NeurolucidaPoint(3, 3, 4, 2), NeurolucidaPoint(2, 1, 5, 7), NeurolucidaPoint(3, 1, 4.2, 7.1)])

        write_ex(ex_file, data)
        self.assertTrue(os.path.exists(ex_file))

    def test_write_ex_branch(self):
        ex_file = os.path.join(here, "resources", "multi_tree.ex")
        if os.path.exists(ex_file):
            os.remove(ex_file)

        data = NeurolucidaData()
        data.add_tree([NeurolucidaPoint(3, 3, 4, 2), [NeurolucidaPoint(2, 1, 5, 7)], [NeurolucidaPoint(2, 4, 8, 5.7)]])

        write_ex(ex_file, data)
        self.assertTrue(os.path.exists(ex_file))


if __name__ == "__main__":
    unittest.main()