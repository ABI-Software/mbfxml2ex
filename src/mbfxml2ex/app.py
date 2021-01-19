import os
import sys
import argparse
import xml.etree.ElementTree as ElTree
from xml.etree.ElementTree import ParseError

from mbfxml2ex.classes import MBFData
from mbfxml2ex.exceptions import MBFXMLFormat, MBFXMLFile
from mbfxml2ex.parsers import parse_contour, parse_tree, parse_marker, parse_images, parse_vessel
from mbfxml2ex.utilities import get_raw_tag
from mbfxml2ex.zinc import write_ex

MBF_INTERNAL_DATA_SET_TAGS = ["filefacts", "thumbnail", "description", "property", "processedlocations", "sparcdata"]


class ProgramArguments(object):
    def __init__(self):
        self.external_annotation = None
        self.input_xml = None
        self.output_ex = None


def read_xml(file_name):
    if os.path.exists(file_name):
        data = MBFData()
        try:
            tree = ElTree.parse(file_name)
        except ParseError as e:
            raise MBFXMLFormat(e.msg) from None

        root = tree.getroot()

        # Need to move marker elements that appear in the tree structure.
        misplaced_marker_elements = []
        for child in root:
            raw_tag = get_raw_tag(child)
            if raw_tag == "tree" and child.find('.//{http://www.mbfbioscience.com/2007/neurolucida}marker'):
                misplaced_marker_elements.append(child)

        for tree_child in misplaced_marker_elements:
            marker_element = tree_child.find('.//{http://www.mbfbioscience.com/2007/neurolucida}marker')
            marker_element_parent = tree_child.find('.//{http://www.mbfbioscience.com/2007/neurolucida}marker/..')
            while marker_element:
                marker_element_parent.remove(marker_element)
                root.append(marker_element)
                marker_element = tree_child.find('.//{http://www.mbfbioscience.com/2007/neurolucida}marker')
                marker_element_parent = tree_child.find('.//{http://www.mbfbioscience.com/2007/neurolucida}marker/..')

        for child in root:
            raw_tag = get_raw_tag(child)
            if raw_tag == "tree":

                tree_data = parse_tree(child)
                data.add_tree(tree_data)
            elif raw_tag == "contour":
                contour_data = parse_contour(child)
                data.add_contour(contour_data)
            elif raw_tag == "marker":
                marker_data = parse_marker(child)
                data.add_marker(marker_data)
            elif raw_tag == "images":
                images_data = parse_images(child)
                data.set_images(images_data)
            elif raw_tag == "vessel":
                vessel_data = parse_vessel(child)
                data.add_vessel(vessel_data)
            elif raw_tag in MBF_INTERNAL_DATA_SET_TAGS:
                pass  # Do nothing.
            else:
                print('Unhandled tag: ', raw_tag)

        # Apparently this is not to be done.  These scaling factors are for model units
        # and not to be applied to contours, trees, etc.
        # data.process_scaling_and_offset()

        return data

    raise MBFXMLFile('File does not exist: "{0}"'.format(file_name))


def main():
    options = {}
    args = parse_args()
    if os.path.exists(args.input_xml):
        if args.output_ex is None:
            output_ex = args.input_xml + '.ex'
        else:
            output_ex = args.output_ex

        options["external_annotation"] = args.external_annotation

        contents = read_xml(args.input_xml)
        if contents is None:
            sys.exit(-2)
        else:
            write_ex(output_ex, contents, options)
    else:
        sys.exit(-1)


def parse_args():
    parser = argparse.ArgumentParser(description="Transform Neurolucida Xml data file to ex format.")
    parser.add_argument("input_xml", help="Location of the input xml file.")
    parser.add_argument("--output-ex", help="Location of the output ex file. "
                                            "[defaults to the location of the input file if not set.]")
    parser.add_argument("--external-annotation", help="Output any annotations as a separate file at "
                                                      "the same location as the output ex file.")

    program_arguments = ProgramArguments()
    parser.parse_args(namespace=program_arguments)

    return program_arguments


if __name__ == "__main__":
    main()
