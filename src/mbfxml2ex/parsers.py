from mbfxml2ex.classes import MBFPropertyChannel, MBFProperty, NeurolucidaChannel, NeurolucidaChannels, \
    NeurolucidaZSpacing, MBFPoint, MBFPropertyPunctum, MBFPropertyVolumeRLE, MBFPropertySet, MBFPropertyTraceAssociation, \
    MBFTree, MBFPropertyGUID, MBFPropertyFillDensity, MBFPropertyTreeOrder, MBFPropertyGeneric
from mbfxml2ex.conversions import hex_to_rgb
from mbfxml2ex.exceptions import MBFXMLException
from mbfxml2ex.utilities import get_raw_tag


def _parse_tree_structure(tree_root):
    tree = {'points': [], 'properties': [], 'attributes': {k: v for k, v in tree_root.attrib.items()}}
    # if 'class' in tree_root.attrib:
    #     tree['class'] = tree_root.attrib['class']

    for child in tree_root:
        raw_tag = get_raw_tag(child)
        if raw_tag == "point":
            tree['points'].append(_create_mbf_point(child))
        elif raw_tag == "branch":
            tree['points'].append(_parse_tree_structure(child))
        elif raw_tag == "property":
            prop = _parse_property(child)
            tree['properties'].append((prop.name(), prop))
        else:
            raise MBFXMLException("XML format violation unknown tag '{0}'.".format(raw_tag))

    return tree


def parse_tree(tree_root):
    return MBFTree(_parse_tree_structure(tree_root))


def parse_contour(contour_root):
    contour = {
        'colour': contour_root.attrib['color'],
        'rgb': hex_to_rgb(contour_root.attrib['color']),
        'closed': contour_root.attrib['closed'] == 'true',
        'name': contour_root.attrib['name'],
        'resolution': -1,
        'properties': [],
    }
    data = []
    for child in contour_root:
        raw_tag = get_raw_tag(child)
        if raw_tag == "point":
            data.append(_create_mbf_point(child))
        elif raw_tag == "property":
            contour['properties'].append(_parse_property(child))
        elif raw_tag == "resolution":
            contour['resolution'] = float(child.text)
        else:
            raise MBFXMLException("XML format violation unknown tag '{0}'.".format(raw_tag))

    contour['data'] = data

    return contour


def parse_channel_property_version_2(children):
    channel = float("".join(children[1].itertext()))
    colour = hex_to_rgb("".join(children[3].itertext()))
    return channel, colour


def parse_channel_property(property_root):
    children = list(property_root)
    if len(children) > 0:
        version_element = children[0]
        version = float("".join(version_element.itertext()))
        if version == 2:
            channel, colour = parse_channel_property_version_2(children)
        else:
            raise MBFXMLException("XML format violation channel property has unknown version '{0}'.".format(version))
    else:
        raise MBFXMLException("XML format violation channel property has no children.")

    return MBFPropertyChannel(version, channel, colour)


def parse_punctum_property_version_4(children):
    spread = float("".join(children[1].itertext()))
    mean_luminance = float("".join(children[2].itertext()))
    surface_area = float("".join(children[3].itertext()))
    voxel_count = float("".join(children[4].itertext()))
    flag_2d = float("".join(children[5].itertext()))
    volume = float("".join(children[6].itertext()))
    # type_ = float("".join(children[7].itertext()))
    location = float("".join(children[8].itertext()))
    colocalized_fraction = float("".join(children[9].itertext()))
    proximal_fraction = float("".join(children[10].itertext()))
    return spread, mean_luminance, surface_area, voxel_count, flag_2d, \
        volume, location, colocalized_fraction, proximal_fraction


def parse_punctum_property(property_root):
    children = list(property_root)
    if len(children) > 0:
        version_element = children[0]
        version = float("".join(version_element.itertext()))
        if version == 4:
            spread, mean_luminance, surface_area, voxel_count, flag_2d, \
                volume, location, colocalized_fraction, proximal_fraction = parse_punctum_property_version_4(children)
        else:
            raise MBFXMLException("XML format violation punctum property has unknown version '{0}'.".format(version))
    else:
        raise MBFXMLException("XML format violation punctum property has no children.")

    return MBFPropertyPunctum(version, spread, mean_luminance, surface_area, voxel_count, flag_2d,
                              volume, location, colocalized_fraction, proximal_fraction)


def parse_volume_rle_property(property_root):
    children = list(property_root)
    if len(children) > 0:
        volume_element = children[0]
        volume_string = "".join(volume_element.itertext())
        volume_description = volume_string.split(" ")
    else:
        raise MBFXMLException("XML format violation volume RLE property has no children.")

    return MBFPropertyVolumeRLE(volume_description)


def parse_numeric_value(element):
    return float(element.text)


def parse_string_value(element):
    return "" if element.text is None else element.text.strip()


def parse_fill_density_property(property_root):
    value = _parse_simple_property(property_root, "Fill Density", "n", parse_numeric_value)
    return MBFPropertyFillDensity(value)


def _property_text(property_root):
    children = list(property_root)
    if len(children) > 0:
        element = children[0]
        text = "".join(element.itertext())
    else:
        raise MBFXMLException("XML format violation text property has no children.")

    return text


def parse_set_property(property_root):
    items = []
    for child in property_root:
        items.append(child.text)

    return MBFPropertySet(items)


def _parse_simple_property(property_root, property_name, property_raw_tag, property_handler):
    local_property = None
    for child in property_root:
        raw_tag = get_raw_tag(child)
        if raw_tag == property_raw_tag:
            local_property = property_handler(child)
        else:
            raise MBFXMLException(f"XML format violation '{property_name}' property has invalid child.")

    if local_property is None:
        raise MBFXMLException(f"XML format violation '{property_name}' property has no children.")

    return local_property


def parse_trace_association_property(property_root):
    value = _parse_simple_property(property_root, "Trace Association", "s", parse_string_value)
    return MBFPropertyTraceAssociation(value)


def parse_guid_property(property_root):
    value = _parse_simple_property(property_root, "GUID", "s", parse_string_value)
    return MBFPropertyGUID(value)


def parse_tree_order_property(property_root):
    children = list(property_root)
    if len(children) == 2:
        label_element = children[0]
        number_element = children[1]
        label_string = "".join(label_element.itertext())
        if label_string != "Shaft":
            raise MBFXMLException("XML format violation tree order property first child is not 'Shaft'.")
        number_string = "".join(number_element.itertext())
    else:
        raise MBFXMLException("XML format violation tree order property has no children.")

    return MBFPropertyTreeOrder(int(number_string))


def parse_generic_property(property_root):
    # name = get_raw_tag(property_root)
    name = property_root.attrib.get("name", "unnamed-property")
    properties = []
    for child in property_root:
        raw_tag = get_raw_tag(child)
        value = child.text if child.text else None
        if raw_tag not in ["n", "s", "c", "l", "b"]:
            print(f"Need to handle this property child tag '{raw_tag}'.")
        if value is not None:
            if raw_tag == "n":
                value = float(value)

        properties.append({raw_tag: value})

    return MBFPropertyGeneric(name, properties)


def _parse_property(property_root) -> MBFProperty:
    name = property_root.attrib['name']
    if name == "Punctum":
        return parse_punctum_property(property_root)
    elif name == "VolumeRLE":
        return parse_volume_rle_property(property_root)
    elif name == "Set":
        return parse_set_property(property_root)
    elif name == "TraceAssociation":
        return parse_trace_association_property(property_root)
    elif name in ["Channel", "GUID", "FillDensity", "TreeOrder", "zSmear", "Densitometry"]:
        return parse_generic_property(property_root)
    # elif name == "Channel":
    #     return parse_channel_property(property_root)
    # elif name == "TreeOrder":
    #     return parse_tree_order_property(property_root)
    # elif name == "TraceAssociation":
    #     return parse_trace_association_property(property_root)
    # elif name == "GUID":
    #     return parse_guid_property(property_root)
    # elif name == "FillDensity":
    #     return parse_fill_density_property(property_root)
    # elif name == "TreeOrder":
    #     return parse_tree_order_property(property_root)
    # elif name == "zSmear":
    #     pass
    # elif name == "Densitometry":
    #     pass
    else:
        raise MBFXMLException("Unhandled property '{0}'".format(name))


def parse_marker(marker_root):
    marker = {'colour': marker_root.attrib['color'],
              'rgb': hex_to_rgb(marker_root.attrib['color']),
              'name': marker_root.attrib['name'],
              'type': marker_root.attrib['type'],
              'varicosity': marker_root.attrib['varicosity'] == "true",
              'properties': []}

    data = []
    for child in marker_root:
        raw_tag = get_raw_tag(child)
        if raw_tag == "point":
            data.append(_create_mbf_point(child))
        elif raw_tag == "property":
            marker['properties'].append(_parse_property(child))
        else:
            raise MBFXMLException("XML format violation unknown tag '{0}'.".format(raw_tag))

    marker['data'] = data

    return marker


def parse_channels(channels_root):
    channels = NeurolucidaChannels(channels_root.attrib['merge'])

    for child in channels_root:
        raw_tag = get_raw_tag(child)
        if raw_tag == "channel":
            channels.add_channel(NeurolucidaChannel(child.attrib['id'], child.attrib['source']))
        else:
            raise MBFXMLException("XML format violation unknown tag {0} in channels.".format(raw_tag))

    return channels


def parse_image(image_root):
    image = {'filename': '', 'channels': [], 'scale': [1.0, 1.0], 'offset': [0.0, 0.0, 0.0], 'z_spacing': None}

    for child in image_root:
        raw_tag = get_raw_tag(child)
        if raw_tag == "filename":
            image['filename'] = child.text
        elif raw_tag == "channels":
            image['channels'] = parse_channels(child)
        elif raw_tag == "scale":
            image['scale'] = [float(child.attrib['x']), float(child.attrib['y'])]
        elif raw_tag == "coord":
            image['offset'] = [float(child.attrib['x']), float(child.attrib['y']), float(child.attrib['z'])]
        elif raw_tag == "zspacing":
            image['z_spacing'] = NeurolucidaZSpacing(float(child.attrib['z']), int(child.attrib['slices']))

    return image


def parse_images(images_root):
    images = []

    for child in images_root:
        images.append(parse_image(child))

    return images


def parse_node(node_root):
    node = {'id': node_root.attrib['id'], }

    data = None
    for child in node_root:
        raw_tag = get_raw_tag(child)
        if raw_tag == "point":
            data = _create_mbf_point(child)
        else:
            raise MBFXMLException("XML format violation unknown tag '{0}'.".format(raw_tag))

    if data is None:
        raise MBFXMLException("XML format violation no point tag for node with id '{0}'.".format(node['id']))

    node['data'] = data
    return node


def parse_nodes(nodes_root):
    nodes = []
    for child in nodes_root:
        raw_tag = get_raw_tag(child)
        if raw_tag == "node":
            nodes.append(parse_node(child))
        else:
            raise MBFXMLException("XML format violation unknown tag '{0}'.".format(raw_tag))

    return nodes


def parse_edge(edge_root):
    edge = {'id': edge_root.attrib['id'], 'properties': []}
    if 'class' in edge_root.attrib:
        edge['class'] = edge_root.attrib['class']

    data = []
    for child in edge_root:
        raw_tag = get_raw_tag(child)
        if raw_tag == "point":
            data.append(_create_mbf_point(child))
        elif raw_tag == "property":
            edge['properties'].append(_parse_property(child))
        else:
            raise MBFXMLException("XML format violation unknown tag {0}".format(raw_tag))

    edge['data'] = data
    return edge


def parse_edges(edges_root):
    edges = []

    for child in edges_root:
        raw_tag = get_raw_tag(child)
        if raw_tag == "edge":
            edges.append(parse_edge(child))
        else:
            raise MBFXMLException("XML format violation unknown tag '{0}'.".format(raw_tag))

    return edges


def parse_edgelist(edgelist_root):
    edgelist = {'id': edgelist_root.attrib['id'],
                'edge': edgelist_root.attrib['edge'],
                'sourcenode': edgelist_root.attrib['sourcenode'],
                'targetnode': edgelist_root.attrib['targetnode'], }

    return edgelist


def parse_edgelists(edgelists_root):
    edgelists = []

    for child in edgelists_root:
        raw_tag = get_raw_tag(child)
        if raw_tag == "edgelist":
            edgelists.append(parse_edgelist(child))
        else:
            raise MBFXMLException("XML format violation unknown tag '{0}'.".format(raw_tag))

    return edgelists


def parse_vessel(vessel_root):
    version = int(vessel_root.attrib['version'])
    vessel = {
        'version': version,
        'colour': vessel_root.attrib['color'],
        'rgb': hex_to_rgb(vessel_root.attrib['color']),
        'type': vessel_root.attrib['type'],
        'properties': [],
        'name': vessel_root.attrib['name'] if version < 4 else vessel_root.attrib['class'],
    }

    for child in vessel_root:
        raw_tag = get_raw_tag(child)
        if raw_tag == "nodes":
            vessel['nodes'] = parse_nodes(child)
        elif raw_tag == "edges":
            vessel['edges'] = parse_edges(child)
        elif raw_tag == "edgelists":
            vessel['edgelists'] = parse_edgelists(child)
        elif raw_tag == "property":
            vessel['properties'].append(_parse_property(child))
        else:
            print(f"Unhandled tag in vessel: '{raw_tag}'")

    return vessel


def _create_mbf_point(child):
    return MBFPoint(float(child.attrib['x']),
                    float(child.attrib['y']),
                    float(child.attrib['z']),
                    float(child.attrib['d']))
