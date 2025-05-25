
def get_raw_tag(element):
    element_tag = element.tag
    if '}' in element_tag:
        element_tag = element.tag.split('}', 1)[1]

    return element_tag


def extract_vessel_node_locations(vessel):
    return [point for edge in vessel.get('edges', []) for point in edge.get('data', [])]


def is_option(option, options):
    return isinstance(options, dict) and option in options


def classify_properties(attributes, attribute_data):
    """
    Classify attributes into data, metadata, and unknown groups, and determine the primary group.

    Parameters:
    attributes (list of tuples): List of attribute-value pairs.
    attribute_data (dict): Dictionary mapping attributes to their group and rank.

    Returns:
    dict: Classified data attributes.
    dict: Classified metadata attributes.
    list: Unknown attributes.
    str: Primary group.
    """
    group_attributes = {}
    metadata_attributes = {}
    unknown_attributes = []

    primary_group = None
    primary_group_rank = float('inf')

    for attr, value in attributes:
        if attr in attribute_data:
            data, rank = attribute_data[attr]
            if data == 'group':
                group_attributes[attr] = value
            elif data == 'metadata':
                metadata_attributes[attr] = value

            if data == 'group' and rank < primary_group_rank:
                primary_group = value
                primary_group_rank = rank
        else:
            unknown_attributes.append(attr)

    return group_attributes, metadata_attributes, unknown_attributes, primary_group


def reverse_element_to_node_map(element_to_node_map):
    node_to_element_map = {}
    for element_id, node_ids in element_to_node_map.items():
        for node_id in node_ids:
            if node_id not in node_to_element_map:
                node_to_element_map[node_id] = []
            node_to_element_map[node_id].append(element_id)
    return node_to_element_map


def get_minimal_list_paths(node_map):
    """
    Extracts the first unique path to each embedded list in a nested structure.
    A list is identified by its parent path (i.e., path excluding the last index).
    """
    unique_paths = []
    seen_paths = set()

    for path, node_id in node_map.items():
        parent_path = tuple(path[:-1])  # Identify the list this node belongs to
        if parent_path not in seen_paths:
            unique_paths.append(path)
            seen_paths.add(parent_path)

    return unique_paths


def get_elements_for_path(node_map, node_to_element_map, target_path):
    """
    Given a node_map and element_to_node_map, return all elements associated with
    nodes that share the same parent path as the given target_path.

    Parameters:
    - node_map: dict mapping node_id -> path (list of indices)
    - node_to_element_map: dict mapping node_ids -> list of element_ids
    - target_path: tuple representing the path to a node in the embedded structure

    Returns:
    - List of element_ids that are connected to nodes from the same embedded list
    """
    parent_path = target_path[:-1]

    # Find all node_ids that share the same parent path
    relevant_nodes = node_map[parent_path]
    # relevant_nodes = [
    #     node_id for path, node_id in node_map.items()
    #     if path[:-1] == parent_path
    # ]

    # Find all elements that use any of these nodes
    elements = set()
    for node_id in relevant_nodes:
        elements.update(set(node_to_element_map[node_id]))

    return list(elements)


def get_elements_for_path_old(node_map, element_to_node_map, target_path):
    """
    Given a node_map and element_to_node_map, return all elements associated with
    nodes that share the same parent path as the given target_path.

    Parameters:
    - node_map: dict mapping node_id -> path (list of indices)
    - element_to_node_map: dict mapping element_id -> list of node_ids
    - target_path: list representing the path to a node in the embedded structure

    Returns:
    - List of element_ids that are connected to nodes from the same embedded list
    """
    parent_path = tuple(target_path[:-1])

    # Find all node_ids that share the same parent path
    relevant_nodes = [
        node_id for node_id, path in node_map.items()
        if tuple(path[:-1]) == parent_path
    ]

    # Find all elements that use any of these nodes
    elements = set()
    for element_id, node_ids in element_to_node_map.items():
        if any(node in relevant_nodes for node in node_ids):
            elements.add(element_id)

    return list(elements)
