
__version__ = "0.1.1"

import os
import sys
import math
import argparse
import xml.etree.ElementTree as ElTree
from xml.etree.ElementTree import ParseError

from opencmiss.zinc.context import Context
from opencmiss.zinc.element import Element
from opencmiss.zinc.element import Elementbasis
from opencmiss.utils.zinc import createFiniteElementField
from opencmiss.utils.zinc import createNode


node_id = 0
branch_visits = []


class BranchVisitor(object):

    def __init__(self, branch_node_id):
        self._node_id = branch_node_id
        self._left_visited = False
        self._right_visited = False

    def visitBranch(self):
        if not self._left_visited:
            self._left_visited = True
        elif not self._right_visited:
            self._right_visited = True

    def visited(self):
        return self._left_visited and self._right_visited


class ProgramArguments(object):
    pass


class NeurolucidaPoint(object):

    def __init__(self, x, y, z, radius):
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

    def add_tree(self, tree_data):
        self._trees.append(tree_data)

    def get_tree(self):
        return self._trees

    def __len__(self):
        return len(self._trees)


def get_raw_tag(element):
    element_tag = element.tag
    if '}' in element_tag:
        element_tag = element.tag.split('}', 1)[1]

    return element_tag


def parse_tree(tree_root):
    tree = []
    for child in tree_root:
        raw_tag = get_raw_tag(child)
        if raw_tag == "point":
            tree.append(NeurolucidaPoint(float(child.attrib['x']),
                                         float(child.attrib['y']),
                                         float(child.attrib['z']),
                                         float(child.attrib['d'])))
        elif raw_tag == "branch":
            tree.append(parse_tree(child))
        else:
            raise NeurolucidaXMLException("XML format violation unkonwn tag {0}".format(raw_tag))

    return tree


def read_xml(file_name):
    if os.path.exists(file_name):
        data = NeurolucidaData()
        try:
            tree = ElTree.parse(file_name)
        except ParseError:
            return None

        root = tree.getroot()
        for child in root:
            raw_tag = get_raw_tag(child)
            # Only looking to deal with 'tree' elements
            if raw_tag == "tree":
                tree_data = parse_tree(child)
                data.add_tree(tree_data)

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

    for element_nodes in element_node_set:
        for i, node_identifier in enumerate(element_nodes):
            node = nodeset.findNodeByIdentifier(node_identifier)
            element_template.setNode(i + 1, node)

        mesh.defineElement(-1, element_template)


def reset_node_id():
    global node_id
    node_id = 0


def determine_connectivity(tree):
    global node_id
    global branch_visits

    connectivity = []
    node_pair = [None, None]
    for pt in tree:
        if isinstance(pt, list):
            # We have a branch
            br = pt[:]
            if branch_visits == 0:
                branching_node_id.append(node_id)

            print(branching_node_id, br)
            connectivity.extend(determine_connectivity(br))
            branch_visits += 1
        else:
            node_id += 1
            if node_pair[0] is None:
                node_pair[0] = node_id
                if branching_node_id is not None:
                    connectivity.append([branching_node_id, node_id])
            elif node_pair[1] is None:
                node_pair[1] = node_id
                connectivity.append(node_pair)
                node_pair = [node_id, None]

    return connectivity


def create_nodes(field_module, tree):
    for pt in tree:
        if isinstance(pt, list):
            create_nodes(field_module, pt)
        else:
            createNode(field_module, ['coordinates', 'radius'], pt)


def create_elements(field_module, connectivity):
    create_line_elements(field_module, connectivity, ['coordinates', 'radius'])


def write_ex(file_name, data):
    context = Context("Neurolucida")
    region = context.getDefaultRegion()
    createFiniteElementField(region)
    createFiniteElementField(region, field_name='radius', dimension=1, type_coordinate=False)
    field_module = region.getFieldmodule()
    reset_node_id()
    for tree in data.get_tree():
        connectivity = determine_connectivity(tree)
        create_nodes(field_module, tree)
        create_elements(field_module, connectivity)

    region.writeFile(file_name)


def main():
    args = parse_args()
    if os.path.exists(args.input_xml):
        if args.output_ex is None:
            output_ex = args.input_xml + '.ex'
        else:
            output_ex = args.output_ex

        contents = read_xml(args.input_xml)
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