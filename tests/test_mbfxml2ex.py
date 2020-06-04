import os
import unittest
from mbfxml2ex import read_xml, determine_contour_connectivity, determine_vessel_connectivity, \
    extract_vessel_node_locations
from mbfxml2ex import MBFPoint
from mbfxml2ex import MBFData
from mbfxml2ex import write_ex
from mbfxml2ex import determine_tree_connectivity
from mbfxml2ex import reset_node_id
from mbfxml2ex import is_option

here = os.path.abspath(os.path.dirname(__file__))


class NeurolucidaXmlReadTreesTestCase(unittest.TestCase):

    def test_not_existing_xml_file(self):
        xml_file = _resource_path("missing.xml")
        contents = read_xml(xml_file)
        self.assertIsNone(contents)

    def test_read_multi_tree_xml(self):
        xml_file = _resource_path("multi_tree.xml")
        contents = read_xml(xml_file)
        self.assertEqual(3, len(contents))

    def test_read_not_xml(self):
        not_xml_file = _resource_path("random_file.txt")
        contents = read_xml(not_xml_file)
        self.assertIsNone(contents)


class NeurolucidaXmlReadTreesWithAnatomicalTermsTestCase(unittest.TestCase):

    def test_read_tree_with_anatomical_terms(self):
        xml_file = _resource_path("tree_with_anatomical_terms.xml")
        neurolucida_data = read_xml(xml_file)
        self.assertEqual(2, neurolucida_data.trees_count())

        tree = neurolucida_data.get_tree(0)

        self.assertTrue('colour' in tree)
        self.assertTrue('rgb' in tree)
        self.assertTrue('type' in tree)
        self.assertTrue('leaf' in tree)
        self.assertTrue('data' in tree)
        self.assertTrue('anatomical term' in tree)
        self.assertEqual([0.0, 1.0, 1.0], tree['rgb'])


class NeurolucidaXmlReadTreesWithMarkersTestCase(unittest.TestCase):

    def test_read_tree_with_markers(self):
        xml_file = _resource_path("tree_with_markers.xml")
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
        xml_file = _resource_path("scale_example.xml")
        neurolucida_data = read_xml(xml_file)
        self.assertEqual(1, neurolucida_data.contours_count())
        contour = neurolucida_data.get_contour(0)
        raw_data = contour['data']
        pt1 = raw_data[0]
        # The scale shouldn't be applied to the data so no scaling should take place
        self.assertAlmostEqual(8794.46, pt1.coordinates()[0])

    def test_read_multi_images(self):
        xml_file = _resource_path("scale_example_2.xml")
        neurolucida_data = read_xml(xml_file)
        self.assertEqual(1, neurolucida_data.contours_count())
        contour = neurolucida_data.get_contour(0)
        raw_data = contour['data']
        pt1 = raw_data[0]
        # The scale shouldn't be applied to the data so no scaling should take place
        self.assertAlmostEqual(8794.46, pt1.coordinates()[0])


class NeurolucidaXmlReadContoursTestCase(unittest.TestCase):

    def test_read_basic_contour_xml(self):
        xml_file = _resource_path("basic_heart_contours.xml")
        contents = read_xml(xml_file)
        self.assertEqual(1, len(contents))


class VessellucidaXmlReadTestCase(unittest.TestCase):

    def test_read_vessel_xml(self):
        xml_file = _resource_path("tracing_vessels_and_markers.xml")
        contents = read_xml(xml_file)
        self.assertEqual(7, len(contents))


class MBFPointTestCase(unittest.TestCase):

    def test_point(self):
        p = MBFPoint(1, 2, 4, 5)
        self.assertListEqual([1, 2, 4], p.coordinates())
        self.assertEqual(2.5, p.radius())

    def test_point_set(self):
        p = MBFPoint(6, 3, 4, 9)
        self.assertListEqual([6, 3, 4, 4.5], p.get())


class DetermineTreeConnectivityTestCase(unittest.TestCase):

    def test_determine_connectivity_basic(self):
        reset_node_id()
        tree = [MBFPoint(3, 3, 4, 2), MBFPoint(2, 1, 5, 7), MBFPoint(3, 1, 4.2, 7.1)]
        self.assertListEqual([[1, 2], [2, 3]], determine_tree_connectivity(tree))

    def test_determine_connectivity_branch(self):
        reset_node_id()
        tree = [MBFPoint(3, 3, 4, 2), [MBFPoint(2, 1, 5, 7)], [MBFPoint(2, 4, 8, 5.7)]]
        self.assertListEqual([[1, 2], [1, 3]], determine_tree_connectivity(tree))

    def test_determine_connectivity_multiple_branch(self):
        reset_node_id()
        tree = [MBFPoint(3, 3, 4, 2), MBFPoint(3, 3, 4, 2), MBFPoint(3, 3, 4, 2),
                [MBFPoint(2, 1, 5, 7), MBFPoint(2, 1, 5, 7), MBFPoint(2, 1, 5, 7),
                 [MBFPoint(2, 4, 8, 5.7), MBFPoint(2, 4, 8, 5.7), MBFPoint(2, 4, 8, 5.7),
                  MBFPoint(2, 4, 8, 5.7)],
                 [MBFPoint(2, 4, 8, 5.7), MBFPoint(2, 4, 8, 5.7), MBFPoint(2, 4, 8, 5.7)]],
                [MBFPoint(2, 4, 8, 5.7), MBFPoint(2, 4, 8, 5.7)]]
        self.assertListEqual([[1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 8], [8, 9],
                              [9, 10], [6, 11], [11, 12], [12, 13], [3, 14], [14, 15]],
                             determine_tree_connectivity(tree))


class DetermineContourConnectivityTestCase(unittest.TestCase):

    def test_determine_connectivity_open_contour(self):
        reset_node_id()
        contour = {'colour': '#00ff00', 'closed': False, 'name': 'Heart',
                   'data': [MBFPoint(3, 3, 4, 1), MBFPoint(2, 1, 5, 1),
                            MBFPoint(3, 1, 4.2, 1)]}
        self.assertListEqual([[1, 2], [2, 3]], determine_contour_connectivity(contour['data'], contour['closed']))

    def test_determine_connectivity_closed_contour(self):
        reset_node_id()
        contour = {'colour': '#00ff00', 'closed': True, 'name': 'Heart',
                   'data': [MBFPoint(3, 3, 4, 1), MBFPoint(2, 1, 5, 1),
                            MBFPoint(3, 1, 4.2, 1)]}
        self.assertListEqual([[1, 2], [2, 3], [3, 1]],
                             determine_contour_connectivity(contour['data'], contour['closed']))


class ExWritingTreeWithAnnotationTestCase(unittest.TestCase):

    def test_write_ex_with_annotation(self):
        ex_file = _resource_path("tree_with_annotation.ex")
        if os.path.exists(ex_file):
            os.remove(ex_file)

        xml_file = _resource_path("tree_with_anatomical_terms.xml")
        data = read_xml(xml_file)

        write_ex(ex_file, data)
        self.assertTrue(os.path.exists(ex_file))


class ExWritingTreeTestCase(unittest.TestCase):

    def test_write_ex_basic(self):
        ex_file = _resource_path("basic_tree.ex")
        if os.path.exists(ex_file):
            os.remove(ex_file)

        tree = {'rgb': [0, 0, 0],
                'data': [MBFPoint(3, 3, 4, 2), MBFPoint(2, 1, 5, 7), MBFPoint(3, 1, 4.2, 7.1)]}
        data = MBFData()
        data.add_tree(tree)

        write_ex(ex_file, data)
        self.assertTrue(os.path.exists(ex_file))

    def test_write_ex_branch(self):
        ex_file = _resource_path("multi_tree.ex")
        if os.path.exists(ex_file):
            os.remove(ex_file)

        tree = {'rgb': [0, 0, 0],
                'data': [MBFPoint(3, 3, 4, 2), [MBFPoint(2, 1, 5, 7)], [MBFPoint(2, 4, 8, 5.7)]]}
        data = MBFData()
        data.add_tree(tree)

        write_ex(ex_file, data)
        self.assertTrue(os.path.exists(ex_file))

    def test_write_tree_with_markers(self):
        xml_file = _resource_path("tree_with_markers.xml")
        neurolucida_data = read_xml(xml_file)

        ex_file = _resource_path("tree_with_markers.ex")
        if os.path.exists(ex_file):
            os.remove(ex_file)

        write_ex(ex_file, neurolucida_data)
        self.assertTrue(os.path.exists(ex_file))


class ExWritingContoursTestCase(unittest.TestCase):

    def test_write_ex_basic(self):
        ex_file = _resource_path("basic_contour.ex")
        if os.path.exists(ex_file):
            os.remove(ex_file)

        data = MBFData()
        contour = {'colour': '#00ff00', 'rgb': [0, 1, 0], 'closed': True, 'name': 'Heart',
                   'data': [MBFPoint(3, 3, 4, 1), MBFPoint(2, 1, 5, 1),
                            MBFPoint(3, 1, 4.2, 1)]}
        data.add_contour(contour)

        write_ex(ex_file, data)
        self.assertTrue(os.path.exists(ex_file))


class VesselConnectionTestCase(unittest.TestCase):

    def test_vessel_connection_basic(self):
        reset_node_id()

        vessel = _create_basic_vessel()
        connectivity = determine_vessel_connectivity(vessel)
        self.assertListEqual([1, 2], connectivity[0])
        self.assertListEqual([2, 3], connectivity[1])
        self.assertListEqual([6, 7], connectivity[5])
        self.assertListEqual([11, 12], connectivity[10])
        self.assertListEqual([12, 13], connectivity[11])

    def test_vessel_connection_repeated_point(self):
        reset_node_id()

        vessel = _create_repeated_vessel()
        connectivity = determine_vessel_connectivity(vessel)
        self.assertListEqual([1, 2], connectivity[0])
        self.assertEqual(1, len(connectivity))

    def test_vessel_connection_branched(self):
        reset_node_id()

        vessel = _create_advanced_vessel()
        connectivity = determine_vessel_connectivity(vessel)
        self.assertListEqual([1, 2], connectivity[0])
        self.assertListEqual([2, 8], connectivity[6])

    def test_vessel_node_locations_basic(self):
        vessel = _create_basic_vessel()
        node_locations = extract_vessel_node_locations(vessel)

        self.assertEqual(13, len(node_locations))
        self.assertListEqual([5392.12, -3790.88, -1450.71], node_locations[0].coordinates())

    def test_vessel_node_locations_branched(self):
        pass


class ExWritingVesselTestCase(unittest.TestCase):

    def test_write_ex_basic(self):
        ex_file = _resource_path("basic_vessel.ex")
        if os.path.exists(ex_file):
            os.remove(ex_file)

        xml_file = _resource_path("tracing_vessels_and_markers.xml")
        data = read_xml(xml_file)

        write_ex(ex_file, data)
        self.assertTrue(os.path.exists(ex_file))


class ExWritingGroupsTestCase(unittest.TestCase):

    def test_write_ex_basic_group(self):
        ex_file = _resource_path("basic_groups.ex")
        if os.path.exists(ex_file):
            os.remove(ex_file)

        xml_file = _resource_path("tree_with_anatomical_terms.xml")
        data = read_xml(xml_file)

        write_ex(ex_file, data, {'external_annotation': True})
        self.assertTrue(_is_line_in_file(ex_file, " Group name: Thorasic Sympathetic Trunk"))


class IsOptionTestCase(unittest.TestCase):

    def test_is_option(self):
        o = {'external_annotation': False}
        self.assertTrue(is_option('external_annotation', o))

    def test_is_not_option(self):
        o = {'external_annotation': False}
        self.assertFalse(is_option('use_latest', o))


if __name__ == "__main__":
    unittest.main()


def _create_advanced_vessel():
    edges = [{'id': '0',
              'data': [MBFPoint(4612.96, -3183.24, -1880.82, 0.83), MBFPoint(4613.07, -3181.37, -1873.73, 0.83)]},
             {'id': '1',
              'data': [MBFPoint(4613.07, -3181.37, -1873.73, 0.83), MBFPoint(4614.62, -3194.86, -1880.82, 2.615),
                       MBFPoint(4620.71, -3203.48, -1880.5, 2.35), MBFPoint(4627.9, -3211.47, -1895.4, 2.615),
                       MBFPoint(4636.21, -3221.43, -1888.11, 3.525), MBFPoint(4643.67, -3227.75, -1872.88, 4.04)]},
             {'id': '2',
              'data': [MBFPoint(4613.07, -3181.37, -1873.73, 0.83), MBFPoint(4617.23, -3167.96, -1880.22, 3.11),
                       MBFPoint(4617.23, -3167.96, -1880.22, 3.11)]},
             {'id': '3', 'data': [MBFPoint(4617.23, -3167.96, -1880.22, 3.11),
                                  MBFPoint(4622.92, -3168.29, -1873.53, 2.625),
                                  MBFPoint(4614.62, -3174.94, -1873.53, 2.56),
                                  MBFPoint(4612.96, -3184.9, -1873.53, 2.59)]},
             {'id': '4', 'data': [
                 MBFPoint(4617.23, -3167.96, -1880.22, 3.11), MBFPoint(4605.6, -3160.61, -1872.13, 3.11),
                 MBFPoint(4599.3, -3161.49, -1879.86, 2.49), MBFPoint(4588.05, -3158.33, -1873.53, 2.49),
                 MBFPoint(4579.75, -3150.03, -1880.82, 2.995), MBFPoint(4573.45, -3142.22, -1865.03, 2.995),
                 MBFPoint(4568.12, -3133.42, -1866.24, 2.995), MBFPoint(4561.48, -3125.12, -1873.53, 2.995),
                 MBFPoint(4556.5, -3116.82, -1873.53, 2.995), MBFPoint(4546.63, -3110.34, -1872.48, 2.995),
                 MBFPoint(4541.56, -3101.87, -1873.53, 2.885), MBFPoint(4534.25, -3093.46, -1863.1, 2.885),
                 MBFPoint(4528.38, -3086.97, -1866.8, 2.885), MBFPoint(4519.3, -3078.87, -1863.55, 2.985),
                 MBFPoint(4508.88, -3070.2, -1871.19, 2.985), MBFPoint(4501.7, -3062.02, -1880.82, 2.35),
                 MBFPoint(4493.4, -3057.04, -1873.53, 2.35), MBFPoint(4482.46, -3054.08, -1876.4, 3.355),
                 MBFPoint(4475.13, -3050.4, -1888.11, 3.355), MBFPoint(4474.3, -3051.5, -1878.73, 2.49),
                 MBFPoint(4463.51, -3055.38, -1880.82, 2.49), MBFPoint(4403.73, -3042.09, -1888.11, 1.66)]}]

    vessel = {'version': '3', 'colour': '#80FF00', 'rgb': [0.5019607843137255, 1.0, 0.0], 'type': 'directed',
              'name': 'Vessel Name 1',
              'nodes': [{'id': '0', 'data': MBFPoint(4613.07, -3181.37, -1873.73, 0.83)},
                        {'id': '1', 'data': MBFPoint(4617.23, -3167.96, -1880.22, 3.11)}], 'edges': edges,
              'edgelists': [{'id': '0', 'edge': '0', 'sourcenode': '-1', 'targetnode': '0'},
                            {'id': '1', 'edge': '1', 'sourcenode': '0', 'targetnode': '-1'},
                            {'id': '2', 'edge': '2', 'sourcenode': '0', 'targetnode': '1'},
                            {'id': '3', 'edge': '3', 'sourcenode': '1', 'targetnode': '-1'},
                            {'id': '4', 'edge': '4', 'sourcenode': '1', 'targetnode': '-1'}]}

    return vessel


def _create_repeated_vessel():
    edges = [
        {'id': '2',
         'data': [MBFPoint(4613.07, -3181.37, -1873.73, 0.83), MBFPoint(4617.23, -3167.96, -1880.22, 3.11),
                  MBFPoint(4617.23, -3167.96, -1880.22, 3.11)]},
    ]
    vessel = {'version': '3', 'colour': '#80FF00', 'rgb': [0.5019607843137255, 1.0, 0.0], 'type': 'directed',
              'name': 'Vessel Name 1',
              'nodes': [{'id': '0', 'data': MBFPoint(4613.07, -3181.37, -1873.73, 0.83)},
                        {'id': '1', 'data': MBFPoint(4617.23, -3167.96, -1880.22, 3.11)}], 'edges': edges,
              'edgelists': [{'id': '0', 'edge': '0', 'sourcenode': '-1', 'targetnode': '0'},
                            {'id': '1', 'edge': '1', 'sourcenode': '0', 'targetnode': '-1'},
                            {'id': '2', 'edge': '2', 'sourcenode': '0', 'targetnode': '1'},
                            {'id': '3', 'edge': '3', 'sourcenode': '1', 'targetnode': '-1'},
                            {'id': '4', 'edge': '4', 'sourcenode': '1', 'targetnode': '-1'}]}

    return vessel


def _create_basic_vessel():
    points = [MBFPoint(5392.12, -3790.88, -1450.71, 0.0),
              MBFPoint(5388.43, -3792.66, -1450.71, 3.465),
              MBFPoint(5386.77, -3784.35, -1458.0, 2.995),
              MBFPoint(5385.11, -3776.05, -1465.29, 2.995),
              MBFPoint(5380.12, -3767.75, -1458.0, 2.425),
              MBFPoint(5375.25, -3762.97, -1462.01, 2.425),
              MBFPoint(5368.62, -3753.33, -1469.66, 2.375),
              MBFPoint(5362.75, -3744.75, -1472.56, 2.325),
              MBFPoint(5359.65, -3738.88, -1473.13, 2.085),
              MBFPoint(5351.89, -3731.22, -1472.58, 2.35),
              MBFPoint(5348.57, -3721.25, -1472.58, 2.35),
              MBFPoint(5340.27, -3712.95, -1479.87, 2.35),
              MBFPoint(5330.31, -3706.31, -1487.16, 2.35)]
    vessel = {'version': '3', 'colour': '#FFFF00', 'rgb': [1.0, 1.0, 0.0], 'type': 'directed',
              'name': 'Vessel Name 1', 'nodes': [],
              'edges': [{'id': '0', 'data': points}],
              'edgelists': [{'id': '0', 'edge': '0', 'sourcenode': '-1', 'targetnode': '-1'}]}

    return vessel


def _generate_lines_that_equal(string, fp):
    for line in fp:
        line = line.rstrip()
        if line == string:
            yield line


def _is_line_in_file(file_name, text):
    with open(file_name, "r") as fp:
        for _ in _generate_lines_that_equal(text, fp):
            return True

    return False


def _resource_path(resource_name):
    return os.path.join(here, "resources", resource_name)
