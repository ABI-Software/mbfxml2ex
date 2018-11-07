__version__ = "0.1.4"

import os
import sys
import argparse
import xml.etree.ElementTree as ElTree
from xml.etree.ElementTree import ParseError

from opencmiss.zinc.context import Context
from opencmiss.zinc.element import Element
from opencmiss.zinc.element import Elementbasis
from opencmiss.utils.zinc import create_finite_element_field
from opencmiss.utils.zinc import create_node as create_zinc_node
from opencmiss.utils.zinc import AbstractNodeDataObject

node_id = 0


class ProgramArguments(object):
    pass


class NeurolucidaPoint(AbstractNodeDataObject):

    def __init__(self, x, y, z, radius):
        super(NeurolucidaPoint, self).__init__(['coordinates', 'radius'])
        self._x = x
        self._y = y
        self._z = z
        self._radius = radius

    def get(self):
        return [self._x, self._y, self._z, self._radius]

    def coordinates(self):
        return [self._x, self._y, self._z]

    def radius(self):
        return self._radius

    def __repr__(self):
        return 'x="{0} y="{1}" z="{2}" d="{3}"'.format(self._x, self._y, self._z, self._radius)


class NeurolucidaXMLException(Exception):
    pass


class NeurolucidaData(object):

    def __init__(self):
        self._trees = []
        self._contours = []
        self._markers = []

    def add_tree(self, tree_data):
        self._trees.append(tree_data)

    def get_trees(self):
        return self._trees

    def get_tree(self, index):
        return self._trees[index]

    def trees_count(self):
        return len(self._trees)

    def add_contour(self, contour_data):
        self._contours.append(contour_data)

    def get_contours(self):
        return self._contours

    def get_contour(self, index):
        return self._contours[index]

    def contours_count(self):
        return len(self._contours)

    def add_marker(self, marker_data):
        self._markers.append(marker_data)

    def get_markers(self):
        return self._markers

    def get_marker(self, index):
        return self._markers[index]

    def markers_count(self):
        return len(self._markers)

    def __len__(self):
        len_trees = len(self._trees)
        len_contours = len(self._contours)
        len_markers = len(self._markers)

        return len_trees + len_markers + len_contours


def convert_hex_to_rgb(hex_string):
    """
    Convert a hexadecimal string with leading hash into a three item list of values between [0, 1].

      E.g. #00ff00 --> [0, 1, 0]

    :return: The value of the hexadecimal string as a three element list with values in the range [0. 1].
    """
    hex_string = hex_string.lstrip('#')
    return [int(hex_string[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


def get_raw_tag(element):
    element_tag = element.tag
    if '}' in element_tag:
        element_tag = element.tag.split('}', 1)[1]

    return element_tag


def parse_tree_structure(tree_root):
    tree = []
    for child in tree_root:
        raw_tag = get_raw_tag(child)
        if raw_tag == "point":
            tree.append(NeurolucidaPoint(float(child.attrib['x']),
                                         float(child.attrib['y']),
                                         float(child.attrib['z']),
                                         float(child.attrib['d'])))
        elif raw_tag == "branch":
            tree.append(parse_tree_structure(child))
        else:
            raise NeurolucidaXMLException("XML format violation unknown tag {0}".format(raw_tag))

    return tree


def parse_tree(tree_root):
    tree = {'colour': tree_root.attrib['color'], 'rgb': convert_hex_to_rgb(tree_root.attrib['color']),
            'type': tree_root.attrib['type'], 'leaf': tree_root.attrib['leaf'], 'data': parse_tree_structure(tree_root)}

    return tree


def parse_contour(contour_root):
    contour = {'colour': contour_root.attrib['color'],
               'rgb': convert_hex_to_rgb(contour_root.attrib['color']),
               'closed': contour_root.attrib['closed'] == 'true',
               'name': contour_root.attrib['name']}
    data = []
    for child in contour_root:
        raw_tag = get_raw_tag(child)
        if raw_tag == "point":
            data.append(NeurolucidaPoint(float(child.attrib['x']),
                                         float(child.attrib['y']),
                                         float(child.attrib['z']),
                                         float(child.attrib['d'])))
        elif raw_tag == "property":
            pass
        elif raw_tag == "resolution":
            pass
        else:
            raise NeurolucidaXMLException("XML format violation unknown tag {0}".format(raw_tag))

    contour['data'] = data

    return contour


def parse_marker(marker_root):
    marker = {'colour': marker_root.attrib['color'],
              'rgb': convert_hex_to_rgb(marker_root.attrib['color']),
              'name': marker_root.attrib['name'],
              'type': marker_root.attrib['type'],
              'varicosity': marker_root.attrib['varicosity'] == "true"}

    data = []
    for child in marker_root:
        raw_tag = get_raw_tag(child)
        if raw_tag == "point":
            data.append(NeurolucidaPoint(float(child.attrib['x']),
                                         float(child.attrib['y']),
                                         float(child.attrib['z']),
                                         float(child.attrib['d'])))
        else:
            raise NeurolucidaXMLException("XML format violation unknown tag {0}".format(raw_tag))

    marker['data'] = data

    return marker


def read_xml(file_name):
    if os.path.exists(file_name):
        data = NeurolucidaData()
        try:
            tree = ElTree.parse(file_name)
        except ParseError as e:
            print(e)
            return None

        root = tree.getroot()
        for child in root:
            raw_tag = get_raw_tag(child)
            # Only looking to deal with 'tree' elements
            if raw_tag == "tree":
                tree_data = parse_tree(child)
                data.add_tree(tree_data)
            elif raw_tag == "contour":
                contour_data = parse_contour(child)
                data.add_contour(contour_data)
            elif raw_tag == "marker":
                marker_data = parse_marker(child)
                data.add_marker(marker_data)

        return data

    return None


def create_line_elements(field_module, element_node_set, field_names):
    mesh = field_module.findMeshByDimension(1)
    nodeset = field_module.findNodesetByName('nodes')
    element_template = mesh.createElementtemplate()
    element_template.setElementShapeType(Element.SHAPE_TYPE_LINE)
    element_template.setNumberOfNodes(2)
    linear_basis = field_module.createElementbasis(1, Elementbasis.FUNCTION_TYPE_LINEAR_LAGRANGE)
    for field_name in field_names:
        field = field_module.findFieldByName(field_name)
        element_template.defineFieldSimpleNodal(field, -1, linear_basis, [1, 2])

    element_identifiers = []
    for element_nodes in element_node_set:
        for i, node_identifier in enumerate(element_nodes):
            node = nodeset.findNodeByIdentifier(node_identifier)
            element_template.setNode(i + 1, node)

        mesh.defineElement(-1, element_template)
        element_identifiers.append(mesh.getSize())

    return element_identifiers


def create_field(field_module, field_info):
    if field_info['name'] == 'constant':
        field = field_module.createFieldConstant(field_info['values'])
    else:
        raise NotImplementedError('Field "{0}" creation is not implemented for this field'.format(field_info['name']))
    return field


def merge_fields_with_nodes(field_module, node_identifiers, field_information, node_set_name='nodes'):
    field_cache = field_module.createFieldcache()
    node_set = field_module.findNodesetByName(node_set_name)
    node_template = node_set.createNodetemplate()

    for node_identifier in node_identifiers:
        node = node_set.findNodeByIdentifier(node_identifier)
        for field_name in field_information:
            field = field_module.findFieldByName(field_name)
            field_values = field_information[field_name]
            node_template.defineField(field)
            node.merge(node_template)
            field_cache.setNode(node)
            if isinstance(field_values, ("".__class__, u"".__class__)):
                field.assignString(field_cache, field_values)
            else:
                field.assignReal(field_cache, field_values)


def merge_additional_fields(field_module, element_field_template, additional_field_info, element_identifiers):
    mesh = field_module.findMeshByDimension(1)
    constant_basis = field_module.createElementbasis(1, Elementbasis.FUNCTION_TYPE_CONSTANT)
    element_template = mesh.createElementtemplate()
    additional_fields = []
    for field_info in additional_field_info:
        field = create_field(field_module, field_info)
        additional_fields.append(field)

    element_field_template.setParameterMappingMode(element_field_template.PARAMETER_MAPPING_MODE_ELEMENT)
    for field in additional_fields:
        element_template.defineField(field, -1, element_field_template)

    for element_identifier in element_identifiers:
        element = mesh.findElementByIdentifier(element_identifier)
        print(element.merge(element_template))


def reset_node_id():
    global node_id
    node_id = 0


def determine_tree_connectivity(tree, parent_node_id=None):
    global node_id
    branching_node_id = None

    connectivity = []
    node_pair = [None, None]
    for pt in tree:
        if isinstance(pt, list):
            # We have a branch
            br = pt[:]
            if branching_node_id is None:
                branching_node_id = node_id
            connectivity.extend(determine_tree_connectivity(br, branching_node_id))
        else:
            node_id += 1
            if node_pair[0] is None:
                node_pair[0] = node_id
                if parent_node_id is not None:
                    connectivity.append([parent_node_id, node_id])
            elif node_pair[1] is None:
                node_pair[1] = node_id
                connectivity.append(node_pair)
                node_pair = [node_id, None]

    return connectivity


def determine_contour_connectivity(contour, closed):
    global node_id

    connectivity = []
    node_pair = [None, None]
    first_node = None
    last_node = None
    for _ in contour:
        node_id += 1
        if node_pair[0] is None:
            node_pair[0] = node_id
            first_node = node_id
        else:
            node_pair[1] = node_id
            connectivity.append(node_pair)
            node_pair = [node_id, None]
            last_node = node_id

    if closed:
        connectivity.append([last_node, first_node])

    return connectivity


def create_nodes(field_module, embedded_lists, node_set_name='nodes'):
    node_identifiers = []
    for pt in embedded_lists:
        if isinstance(pt, list):
            node_ids = create_nodes(field_module, pt, node_set_name=node_set_name)
            node_identifiers.extend(node_ids)
        else:
            local_node_id = create_zinc_node(field_module, pt, node_set_name=node_set_name)
            node_identifiers.append(local_node_id)

    return node_identifiers


def create_elements(field_module, connectivity, field_names=None):
    if field_names is None:
        field_names = ['coordinates']
    return create_line_elements(field_module, connectivity, field_names)


def get_element_field_template(field_module, element_identifier):
    coordinate_field = field_module.findFieldByName('coordinates')
    mesh = field_module.findMeshByDimension(1)
    element = mesh.findElementByIdentifier(element_identifier)
    element_field_template = element.getElementfieldtemplate(coordinate_field, -1)
    return element_field_template


def write_ex(file_name, data):
    context = Context("Neurolucida")
    region = context.getDefaultRegion()
    create_finite_element_field(region)
    create_finite_element_field(region, field_name='radius', dimension=1, type_coordinate=False)
    create_finite_element_field(region, field_name='rgb', type_coordinate=False)
    field_module = region.getFieldmodule()
    reset_node_id()
    for tree in data.get_trees():
        connectivity = determine_tree_connectivity(tree['data'])
        node_identifiers = create_nodes(field_module, tree['data'])
        field_info = {'rgb': tree['rgb']}
        merge_fields_with_nodes(field_module, node_identifiers, field_info)
        create_elements(field_module, connectivity, field_names=['coordinates', 'radius', 'rgb'])
    for contour in data.get_contours():
        connectivity = determine_contour_connectivity(contour['data'], contour['closed'])
        node_identifiers = create_nodes(field_module, contour['data'])
        field_info = {'rgb': contour['rgb']}
        merge_fields_with_nodes(field_module, node_identifiers, field_info)
        create_elements(field_module, connectivity, field_names=['coordinates', 'radius', 'rgb'])
    for marker in data.get_markers():
        node_identifiers = create_nodes(field_module, marker['data'], node_set_name='datapoints')
        field_info = {'rgb': marker['rgb']}
        if 'name' in marker:
            stored_string_field = field_module.createFieldStoredString()
            stored_string_field.setManaged(True)
            stored_string_field.setName('marker_name')
            field_info['marker_name'] = marker['name']
        merge_fields_with_nodes(field_module, node_identifiers, field_info, node_set_name='datapoints')

    region.writeFile(file_name)


def main():
    args = parse_args()
    if os.path.exists(args.input_xml):
        if args.output_ex is None:
            output_ex = args.input_xml + '.ex'
        else:
            output_ex = args.output_ex

        contents = read_xml(args.input_xml)
        if contents is None:
            sys.exit(-2)
        else:
            write_ex(output_ex, contents)
    else:
        sys.exit(-1)


def parse_args():
    parser = argparse.ArgumentParser(description="Transform Neurolucida Xml data file to ex format.")
    parser.add_argument("input_xml", help="Location of the input xml file.")
    parser.add_argument("--output_ex", help="Location of the output ex file. "
                                            "[defaults to the location of the input file if not set.]")

    program_arguments = ProgramArguments()
    parser.parse_args(namespace=program_arguments)

    return program_arguments


if __name__ == "__main__":
    main()
