from opencmiss.utils.zinc.finiteelement import create_cube_element
from opencmiss.zinc.context import Context
from opencmiss.zinc.element import Element
from opencmiss.zinc.element import Elementbasis
from opencmiss.zinc.field import FieldGroup

from opencmiss.utils.zinc.field import create_field_finite_element, create_field_coordinates, find_or_create_field_group
from opencmiss.utils.zinc.general import create_node as create_zinc_node
from opencmiss.utils.zinc.general import ChangeManager

from mbfxml2ex.classes import MBFPropertyVolumeRLE, MBFPropertyPunctum, MBFPropertySet, get_text_properties
from mbfxml2ex.exceptions import MissingImplementationException, MBFDataException
from mbfxml2ex.utilities import extract_vessel_node_locations
from mbfxml2ex.templates import field_header_3d_template, grid_field_3d_template, field_data_template

node_id = 0


def write_ex(file_name, data, options=None):
    context = Context("Neurolucida")
    region = context.getDefaultRegion()

    load(region, data, options)

    region.writeFile(file_name)


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


def determine_vessel_connectivity(vessel):
    global node_id

    connectivity = []
    node_map = {}
    node_pair = [None, None]
    if 'edges' in vessel:
        edges = vessel['edges']
        for edge in edges:
            edge_map = {}
            if 'data' in edge:
                for point in edge['data']:
                    str_point = str(point)
                    if str_point not in edge_map:
                        edge_map[str_point] = node_id
                        if str_point in node_map:
                            next_node_id = node_map[str_point]
                        else:
                            node_id += 1
                            next_node_id = node_id
                            node_map[str_point] = node_id
                        if node_pair[0] is None:
                            node_pair[0] = next_node_id
                        else:
                            node_pair[1] = next_node_id
                            connectivity.append(node_pair)
                            node_pair = [node_id, None]
                node_pair = [None, None]

    return connectivity


def load(region, data, options):
    punctum_data = []
    field_module = region.getFieldmodule()
    create_field_coordinates(field_module)
    create_field_finite_element(field_module, 'radius', 1, type_coordinate=False)
    create_field_finite_element(field_module, 'rgb', 3, type_coordinate=False)
    annotation_stored_string_field = field_module.createFieldStoredString()
    annotation_stored_string_field.setName('annotation')
    reset_node_id()
    for tree in data.get_trees():
        tree_data = tree.points()
        point_properties = tree.point_properties()
        connectivity = determine_tree_connectivity(tree_data)
        node_identifiers = create_nodes(field_module, tree_data)

        group_name = tree.type_description()
        if group_name is None and len(point_properties) and len(point_properties[0]):
            group_name = point_properties[0][0]

        field_info = {'rgb': tree.rgb()}
        merge_fields_with_nodes(field_module, node_identifiers, field_info)
        element_ids = create_elements(field_module, connectivity, field_names=['coordinates', 'radius', 'rgb'])
        if group_name is not None:
            create_group_elements(field_module, group_name, element_ids)

        sub_groups = {}
        for index, connection in enumerate(connectivity):
            first_node = connection[0]
            second_node = connection[1]
            first_node_index = node_identifiers.index(first_node)
            second_node_index = node_identifiers.index(second_node)
            first_node_properties = point_properties[first_node_index]
            second_node_properties = point_properties[second_node_index]
            element_properties = list(set(first_node_properties + second_node_properties))

            for element_property in element_properties:
                element_id = element_ids[index]
                if element_property in sub_groups:
                    sub_groups[element_property].append(element_id)
                else:
                    sub_groups[element_property] = [element_id]

        for sub_group in sub_groups:
            create_group_elements(field_module, sub_group, sub_groups[sub_group])

    for contour in data.get_contours():
        connectivity = determine_contour_connectivity(contour['data'], contour['closed'])
        node_identifiers = create_nodes(field_module, contour['data'])
        field_info = {'rgb': contour['rgb']}
        merge_fields_with_nodes(field_module, node_identifiers, field_info)
        element_ids = create_elements(field_module, connectivity, field_names=['coordinates', 'radius', 'rgb'])
        create_group_elements(field_module, contour['name'], element_ids)

        text_properties = get_text_properties(contour['properties'])
        for text_property in text_properties:
            create_group_elements(field_module, text_property, element_ids)

    for marker in data.get_markers():
        if marker['name'] == "Punctum":
            volume_rle = None
            punctum = None
            set_name = None
            for property_ in marker['properties']:
                if type(property_) is MBFPropertyVolumeRLE:
                    volume_rle = property_
                elif type(property_) is MBFPropertyPunctum:
                    punctum = property_
                elif type(property_) is MBFPropertySet:
                    set_name = property_

            if punctum and volume_rle:
                voxel_counts = volume_rle.voxel_counts()
                if punctum.flag_2d():
                    raise MissingImplementationException("Have not implemented 2D Punctum.")
                else:
                    total_voxels = voxel_counts[0] * voxel_counts[1] * voxel_counts[2]
                    field_values = []
                    for index, run in enumerate(volume_rle.voxel_run()):
                        values = [0.25 if index % 2 == 0 else 1.00] * run
                        field_values.extend(values)
                    missing_values = int(total_voxels) - len(field_values)
                    if missing_values < 0:
                        raise MBFDataException("Data error: field values has '{0}' values which is more than"
                                               " '{1}' the total voxel count".format(len(field_values), total_voxels))
                    elif missing_values > 0:
                        field_values.extend([0.0] * missing_values)

                    punctum_datum = {"dimension": 3, "voxel_counts": voxel_counts, "total_voxels": total_voxels,
                                     "origin": volume_rle.origin(), "values": field_values,
                                     "corners": volume_rle.corner_coordinates()}
                    if set_name is not None:
                        punctum_datum["set_name"] = set_name.label()

                    punctum_data.append(punctum_datum)
            else:
                raise MBFDataException("Missing at least some of the required data for outputting punctum.")
        else:
            node_identifiers = create_nodes(field_module, marker['data'], node_set_name='datapoints')
            field_info = {'rgb': marker['rgb']}
            if 'name' in marker:
                stored_string_field = field_module.createFieldStoredString()
                stored_string_field.setManaged(True)
                stored_string_field.setName('marker_name')
                field_info['marker_name'] = marker['name']
            merge_fields_with_nodes(field_module, node_identifiers, field_info, node_set_name='datapoints')
            create_group_nodes(field_module, 'marker', node_identifiers, node_set_name='datapoints')
    for vessel in data.get_vessels():
        connectivity = determine_vessel_connectivity(vessel)
        node_locations = extract_vessel_node_locations(vessel)
        node_identifiers = create_nodes(field_module, node_locations)
        field_info = {'rgb': vessel['rgb']}
        merge_fields_with_nodes(field_module, node_identifiers, field_info)
        create_elements(field_module, connectivity, field_names=['coordinates', 'radius', 'rgb'])

    if punctum_data:
        _process_punctum_data(region, punctum_data)


def _process_punctum_data(region, punctum_data):
    r = region.createChild("punctum")
    field_module = r.getFieldmodule()
    mesh = field_module.findMeshByDimension(3)
    finite_element_field = create_field_coordinates(field_module)
    field_data = ""
    for index, data in enumerate(punctum_data):
        element_id = index + 1  # Guessing what the element id is going to be
        voxel_counts = data["voxel_counts"]
        xi_counts = [int(c) - 1 for c in voxel_counts]
        field_header = field_header_3d_template.format(
            1, "punctum", xi_counts[0], xi_counts[1], xi_counts[2])
        field_values = "  " + " ".join(str(v) for v in data["values"]) + "\n"
        field_details = field_data_template.format(element_id, field_values)
        create_cube_element(mesh, finite_element_field, data["corners"])
        field_data += field_header + field_details

        if "set_name" in data:
            create_group_elements(field_module, data["set_name"], [element_id], dimension=3)

    ex_data = grid_field_3d_template.format(field_data)
    sir = r.createStreaminformationRegion()
    sir.createStreamresourceMemoryBuffer(ex_data)
    r.read(sir)


def create_line_elements(field_module, element_node_set, field_names):
    mesh = field_module.findMeshByDimension(1)
    node_set = field_module.findNodesetByName('nodes')
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
            node = node_set.findNodeByIdentifier(node_identifier)
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

    for node_identifier in node_identifiers:
        node = node_set.findNodeByIdentifier(node_identifier)
        for field_name in field_information:
            field = field_module.findFieldByName(field_name)
            field_values = field_information[field_name]
            node_template = node_set.createNodetemplate()
            node_template.defineField(field)
            node.merge(node_template)
            field_cache.setNode(node)
            if isinstance(field_values, ("".__class__, u"".__class__)):
                field.assignString(field_cache, field_values)
            elif isinstance(field_values, list):
                field.assignReal(field_cache, field_values)
            else:
                pass


def merge_additional_fields(field_module, element_field_template, additional_field_info, element_identifiers):
    mesh = field_module.findMeshByDimension(1)
    # constant_basis = field_module.createElementbasis(1, Elementbasis.FUNCTION_TYPE_CONSTANT)
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
        element.merge(element_template)


def reset_node_id():
    global node_id
    node_id = 0


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


def create_group_elements(field_module, group_name, element_ids, dimension=1):
    with ChangeManager(field_module):
        group = find_or_create_field_group(field_module, name=group_name)
        group.setSubelementHandlingMode(FieldGroup.SUBELEMENT_HANDLING_MODE_FULL)

        mesh = field_module.findMeshByDimension(dimension)
        element_group = group.getFieldElementGroup(mesh)
        if not element_group.isValid():
            element_group = group.createFieldElementGroup(mesh)

        mesh_group = element_group.getMeshGroup()
        for element_id in element_ids:
            element = mesh.findElementByIdentifier(element_id)
            mesh_group.addElement(element)


def create_group_nodes(field_module, group_name, node_ids, node_set_name='nodes'):
    with ChangeManager(field_module):
        group = find_or_create_field_group(field_module, name=group_name)
        group.setSubelementHandlingMode(FieldGroup.SUBELEMENT_HANDLING_MODE_FULL)

        nodeset = field_module.findNodesetByName(node_set_name)
        node_group = group.getFieldNodeGroup(nodeset)
        if not node_group.isValid():
            node_group = group.createFieldNodeGroup(nodeset)

        nodeset_group = node_group.getNodesetGroup()
        for group_node_id in node_ids:
            node = nodeset.findNodeByIdentifier(group_node_id)
            nodeset_group.addNode(node)


def get_element_field_template(field_module, element_identifier):
    coordinate_field = field_module.findFieldByName('coordinates')
    mesh = field_module.findMeshByDimension(1)
    element = mesh.findElementByIdentifier(element_identifier)
    element_field_template = element.getElementfieldtemplate(coordinate_field, -1)
    return element_field_template
