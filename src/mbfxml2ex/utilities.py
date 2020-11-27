from mbfxml2ex.classes import BinaryTreeNode


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


def extract_vessel_node_locations(vessel):
    node_locations = []
    node_binary_tree = None
    if 'edges' in vessel:
        edges = vessel['edges']
        for edge in edges:
            if 'data' in edge:
                for point in edge['data']:
                    str_point = str(point)
                    if node_binary_tree is None:
                        node_binary_tree = BinaryTreeNode(str_point)
                        node_locations.append(point)
                    elif str_point not in node_binary_tree:
                        node_binary_tree.insert(str_point)
                        node_locations.append(point)

    return node_locations


def is_option(option, options):
    return isinstance(options, dict) and option in options
