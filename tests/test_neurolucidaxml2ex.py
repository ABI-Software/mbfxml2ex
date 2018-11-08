
import os
import unittest
from neurolucidaxml2ex import read_xml, determine_contour_connectivity
from neurolucidaxml2ex import NeurolucidaPoint
from neurolucidaxml2ex import NeurolucidaData
from neurolucidaxml2ex import write_ex
from neurolucidaxml2ex import determine_tree_connectivity
from neurolucidaxml2ex import reset_node_id

here = os.path.abspath(os.path.dirname(__file__))


class NeurolucidaXmlReadTreesTestCase(unittest.TestCase):

    def test_not_existing_xml_file(self):
        xml_file = os.path.join(here, "resources", "missing.xml")
        contents = read_xml(xml_file)
        self.assertIsNone(contents)

    def test_read_multi_tree_xml(self):
        xml_file = os.path.join(here, "resources", "multi_tree.xml")
        contents = read_xml(xml_file)
        self.assertEqual(3, len(contents))

    def test_read_not_xml(self):
        not_xml_file = os.path.join(here, "resources", "random_file.txt")
        contents = read_xml(not_xml_file)
        self.assertIsNone(contents)


class NeurolucidaXmlReadTreesWithMarkersTestCase(unittest.TestCase):

    def test_read_tree_with_markers(self):
        xml_file = os.path.join(here, "resources", "tree_with_markers.xml")
        neurolucida_data = read_xml(xml_file)
        self.assertEqual(0, neurolucida_data.contours_count())
        self.assertEqual(2, neurolucida_data.markers_count())
        self.assertEqual(1, neurolucida_data.trees_count())

        tree = neurolucida_data.get_tree(0)
        marker = neurolucida_data.get_marker(1)

        self.assertTrue('colour' in tree)
        self.assertTrue('rgb' in tree)
        self.assertTrue('type' in tree)
        self.assertTrue('leaf' in tree)
        self.assertTrue('data' in tree)

        self.assertEqual([1.0, 0.0, 1.0], tree['rgb'])

        self.assertTrue('colour' in marker)
        self.assertTrue('rgb' in marker)
        self.assertTrue('name' in marker)
        self.assertTrue('type' in marker)
        self.assertTrue('varicosity' in marker)
        self.assertTrue('data' in marker)

        self.assertEqual('Dot', marker['type'])


class NeurolucidaReadScaleInformation(unittest.TestCase):

    def test_read_scale(self):
        xml_file = os.path.join(here, "resources", "scale_example.xml")
        neurolucida_data = read_xml(xml_file)
        self.assertEqual(1, neurolucida_data.contours_count())
        contour = neurolucida_data.get_contour(0)
        raw_data = contour['data']
        pt1 = raw_data[0]
        self.assertAlmostEqual(5276.676, pt1.coordinates()[0])


class NeurolucidaXmlReadContoursTestCase(unittest.TestCase):

    def test_read_basic_contour_xml(self):
        xml_file = os.path.join(here, "resources", "basic_heart_contours.xml")
        contents = read_xml(xml_file)
        self.assertEqual(1, len(contents))


class NeurolucidaPointTestCase(unittest.TestCase):

    def test_point(self):
        p = NeurolucidaPoint(1, 2, 4, 5)
        self.assertListEqual([1, 2, 4], p.coordinates())
        self.assertEqual(2.5, p.radius())

    def test_point_set(self):
        p = NeurolucidaPoint(6, 3, 4, 9)
        self.assertListEqual([6, 3, 4, 4.5], p.get())


class DetermineTreeConnectivityTestCase(unittest.TestCase):

    def test_determine_connectivity_basic(self):
        reset_node_id()
        tree = [NeurolucidaPoint(3, 3, 4, 2), NeurolucidaPoint(2, 1, 5, 7), NeurolucidaPoint(3, 1, 4.2, 7.1)]
        self.assertListEqual([[1, 2], [2, 3]], determine_tree_connectivity(tree))

    def test_determine_connectivity_branch(self):
        reset_node_id()
        tree = [NeurolucidaPoint(3, 3, 4, 2), [NeurolucidaPoint(2, 1, 5, 7)], [NeurolucidaPoint(2, 4, 8, 5.7)]]
        self.assertListEqual([[1, 2], [1, 3]], determine_tree_connectivity(tree))

    def test_determine_connectivity_multiple_branch(self):
        reset_node_id()
        tree = [NeurolucidaPoint(3, 3, 4, 2), NeurolucidaPoint(3, 3, 4, 2), NeurolucidaPoint(3, 3, 4, 2),
                [NeurolucidaPoint(2, 1, 5, 7), NeurolucidaPoint(2, 1, 5, 7), NeurolucidaPoint(2, 1, 5, 7),
                 [NeurolucidaPoint(2, 4, 8, 5.7), NeurolucidaPoint(2, 4, 8, 5.7), NeurolucidaPoint(2, 4, 8, 5.7),
                  NeurolucidaPoint(2, 4, 8, 5.7)],
                 [NeurolucidaPoint(2, 4, 8, 5.7), NeurolucidaPoint(2, 4, 8, 5.7), NeurolucidaPoint(2, 4, 8, 5.7)]],
                [NeurolucidaPoint(2, 4, 8, 5.7), NeurolucidaPoint(2, 4, 8, 5.7)]]
        self.assertListEqual([[1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 8], [8, 9],
                              [9, 10], [6, 11], [11, 12], [12, 13], [3, 14], [14,15]], determine_tree_connectivity(tree))


class DetermineContourConnectivityTestCase(unittest.TestCase):

    def test_determine_connectivity_open_contour(self):
        reset_node_id()
        contour = {'colour': '#00ff00', 'closed': False, 'name': 'Heart',
                   'data': [NeurolucidaPoint(3, 3, 4, 1), NeurolucidaPoint(2, 1, 5, 1),
                            NeurolucidaPoint(3, 1, 4.2, 1)]}
        self.assertListEqual([[1, 2], [2, 3]], determine_contour_connectivity(contour['data'], contour['closed']))

    def test_determine_connectivity_closed_contour(self):
        reset_node_id()
        contour = {'colour': '#00ff00', 'closed': True, 'name': 'Heart',
                   'data': [NeurolucidaPoint(3, 3, 4, 1), NeurolucidaPoint(2, 1, 5, 1),
                            NeurolucidaPoint(3, 1, 4.2, 1)]}
        self.assertListEqual([[1, 2], [2, 3], [3, 1]], determine_contour_connectivity(contour['data'], contour['closed']))


class ExWritingTreeTestCase(unittest.TestCase):

    def test_write_ex_basic(self):
        ex_file = os.path.join(here, "resources", "basic_tree.ex")
        if os.path.exists(ex_file):
            os.remove(ex_file)

        tree = {'rgb': [0, 0, 0],
                'data': [NeurolucidaPoint(3, 3, 4, 2), NeurolucidaPoint(2, 1, 5, 7), NeurolucidaPoint(3, 1, 4.2, 7.1)]}
        data = NeurolucidaData()
        data.add_tree(tree)

        write_ex(ex_file, data)
        self.assertTrue(os.path.exists(ex_file))

    def test_write_ex_branch(self):
        ex_file = os.path.join(here, "resources", "multi_tree.ex")
        if os.path.exists(ex_file):
            os.remove(ex_file)

        tree = {'rgb': [0, 0, 0],
                'data': [NeurolucidaPoint(3, 3, 4, 2), [NeurolucidaPoint(2, 1, 5, 7)], [NeurolucidaPoint(2, 4, 8, 5.7)]]}
        data = NeurolucidaData()
        data.add_tree(tree)

        write_ex(ex_file, data)
        self.assertTrue(os.path.exists(ex_file))


class ExWritingContoursTestCase(unittest.TestCase):

    def test_write_ex_basic(self):
        ex_file = os.path.join(here, "resources", "basic_contour.ex")
        if os.path.exists(ex_file):
            os.remove(ex_file)

        data = NeurolucidaData()
        contour = {'colour': '#00ff00', 'rgb': [0, 1, 0], 'closed': True, 'name': 'Heart',
                   'data': [NeurolucidaPoint(3, 3, 4, 1), NeurolucidaPoint(2, 1, 5, 1),
                            NeurolucidaPoint(3, 1, 4.2, 1)]}
        data.add_contour(contour)

        write_ex(ex_file, data)
        self.assertTrue(os.path.exists(ex_file))


if __name__ == "__main__":
    unittest.main()