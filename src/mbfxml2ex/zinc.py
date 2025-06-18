from cmlibs.utils.zinc.finiteelement import create_cube_element
from cmlibs.zinc.context import Context
from cmlibs.zinc.element import Element
from cmlibs.zinc.element import Elementbasis
from cmlibs.zinc.field import FieldGroup

from cmlibs.utils.zinc.field import create_field_finite_element, create_field_coordinates, find_or_create_field_group
from cmlibs.utils.zinc.general import create_node as create_zinc_node
from cmlibs.utils.zinc.general import ChangeManager

from mbfxml2ex.classes import MBFPropertyTraceAssociation, MBFPropertyVolumeRLE, MBFPropertyPunctum, MBFPropertySet, get_text_properties, MBFPropertyGeneric, MBFProperty
from mbfxml2ex.definitions import INFOSET_RANK_MAP
from mbfxml2ex.exceptions import MissingImplementationException, MBFDataException
from mbfxml2ex.utilities import extract_vessel_node_locations, get_minimal_list_paths, classify_properties, get_elements_for_path, reverse_element_to_node_map
from mbfxml2ex.templates import field_header_3d_template, grid_field_3d_template, field_data_template


def write_ex(file_name, data, options=None):
    context = Context("Neurolucida")
    region = context.getDefaultRegion()

    load(region, data, options)

    region.writeFile(file_name)


def determine_tree_connectivity_with_map(tree, node_map, path=None, parent_path=None):
    if path is None:
        path = []
    connectivity = []

    previous_path = parent_path

    for i, pt in enumerate(tree):
        current_path = path + [i]
        if isinstance(pt, list):
            # Recurse into branch
            child_connectivity = determine_tree_connectivity_with_map(pt, node_map, current_path, previous_path)
            connectivity.extend(child_connectivity)
        else:
            current_node_id = node_map[tuple(current_path)]
            if previous_path is not None:
                previous_node_id = node_map[tuple(previous_path)]
                connectivity.append([previous_node_id, current_node_id])
            previous_path = current_path

    return connectivity


def determine_tree_connectivity(tree, current_node_id=0, parent_node_id=None):
    connectivity = []

    previous_node_id = parent_node_id

    for pt in tree:
        if isinstance(pt, list):
            # Recurse into branch
            child_connectivity, current_node_id = determine_tree_connectivity(pt, current_node_id, previous_node_id)
            connectivity.extend(child_connectivity)
        else:
            current_node_id += 1
            if previous_node_id is not None:
                connectivity.append([previous_node_id, current_node_id])
            previous_node_id = current_node_id

    return connectivity, current_node_id


def determine_contour_connectivity(node_map, closed):
    connectivity = []
    node_ids = [value for key, value in sorted(node_map.items(), key=lambda item: item[0][0])]

    for i in range(len(node_ids) - 1):
        connectivity.append([node_ids[i], node_ids[i + 1]])

    if closed and len(node_ids) > 1:
        connectivity.append([node_ids[-1], node_ids[0]])

    return connectivity


def determine_vessel_connectivity(vessel, node_map):
    connectivity = []
    associated_groups = []
    groups = []
    edge_set = set()

    if 'edges' not in vessel:
        return connectivity, associated_groups, groups

    point_index = 0
    for edge in vessel['edges']:
        group = {'id': f"edge_id_{edge.get('id', 'X')}"}

        if 'class' in edge:
            group['name'] = edge['class']

        for prop in edge.get('properties', []):
            if isinstance(prop, MBFPropertyTraceAssociation):
                group['TraceAssociation'] = prop.label()

        group_index = len(groups)
        groups.append(group)

        previous_node_id = None
        for _ in edge.get('data', []):
            node_id = node_map[(point_index,)]

            if previous_node_id is not None and previous_node_id != node_id:
                edge_key = tuple(sorted((previous_node_id, node_id)))
                if edge_key not in edge_set:
                    connectivity.append([previous_node_id, node_id])
                    associated_groups.append(group_index)
                    edge_set.add(edge_key)

            previous_node_id = node_id
            point_index += 1

    return connectivity, associated_groups, groups


def load(region, data, options):
    punctum_data = []
    field_module = region.getFieldmodule()
    _coordinate_field = create_field_coordinates(field_module)
    _radius_field = create_field_finite_element(field_module, 'radius', 1, type_coordinate=False)
    _rgb_field = create_field_finite_element(field_module, 'rgb', 3, type_coordinate=False)

    for tree in data.get_trees():
        tree_data = tree.points()
        node_map = {}
        node_identifiers = create_nodes(field_module, tree_data, node_map=node_map)
        connectivity = determine_tree_connectivity_with_map(tree_data, node_map)

        field_info = {'rgb': tree.rgb()}
        merge_fields_with_nodes(field_module, node_identifiers, field_info)
        element_ids = create_elements(field_module, connectivity, field_names=['coordinates', 'radius', 'rgb'])

        element_to_node_map = dict(zip(element_ids, connectivity))
        node_to_element_map = reverse_element_to_node_map(element_to_node_map)

        unique_paths = get_minimal_list_paths(node_map)
        grouped_by_parent = _group_by_parent(node_map)

        sub_groups = _determine_sub_groups(grouped_by_parent, node_to_element_map, tree, unique_paths)

        for name, members in sub_groups.items():
            create_group_elements(field_module, name, members['el'])
            create_group_nodes(field_module, name, members['no'])

    for contour in data.get_contours():
        _resolution_field = contour.get('resolution')
        if _resolution_field is not None:
            _resolution_field = create_field_finite_element(field_module, 'resolution', 1, type_coordinate=False)

        node_map = {}
        node_identifiers = create_nodes(field_module, contour['data'], node_map=node_map)
        connectivity = determine_contour_connectivity(node_map, contour['closed'])

        field_info = {'rgb': contour['rgb']}
        if _resolution_field is not None:
            field_info['resolution'] = contour['resolution']

        merge_fields_with_nodes(field_module, node_identifiers, field_info)
        element_ids = create_elements(field_module, connectivity, field_names=['coordinates', 'radius', 'rgb', 'resolution'])
        create_group_elements(field_module, contour['name'], element_ids)
        create_group_nodes(field_module, contour['name'], node_identifiers)

        text_properties = get_text_properties(contour['properties'])
        for text_property in text_properties:
            create_group_elements(field_module, text_property, element_ids)
            create_group_nodes(field_module, text_property, node_identifiers)

    marker_groups = {}
    for marker in data.get_markers():
        if marker['name'] == "Punctum":
            volume_rle = None
            punctum = None
            set_name = None
            generics = []
            for property_ in marker['properties']:
                if type(property_) is MBFPropertyVolumeRLE:
                    volume_rle = property_
                elif type(property_) is MBFPropertyPunctum:
                    punctum = property_
                elif type(property_) is MBFPropertySet:
                    set_name = property_
                elif type(property_) is MBFPropertyGeneric:
                    generics.append(property_)

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
                        items = set_name.items()
                        if len(items) == 1:
                           punctum_datum["set_name"] = items[0]

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
                if marker['name'] in marker_groups:
                    marker_groups[marker['name']].extend(node_identifiers)
                else:
                    marker_groups[marker['name']] = node_identifiers
            merge_fields_with_nodes(field_module, node_identifiers, field_info, node_set_name='datapoints')
            create_group_nodes(field_module, 'marker', node_identifiers, node_set_name='datapoints')

    # Create groups for markers that occur more than once.
    for marker_group_name in marker_groups:
        node_identifiers = marker_groups[marker_group_name]
        if len(node_identifiers) > 1:
            create_group_nodes(field_module, marker_group_name, node_identifiers, node_set_name='datapoints')

    for vessel in data.get_vessels():
        node_map = {}
        node_locations = extract_vessel_node_locations(vessel)
        node_identifiers = create_nodes(field_module, node_locations, node_map=node_map)
        connectivity, associated_groups, groups = determine_vessel_connectivity(vessel, node_map)
        field_info = {'rgb': vessel['rgb']}
        merge_fields_with_nodes(field_module, node_identifiers, field_info)
        element_ids = create_elements(field_module, connectivity, field_names=['coordinates', 'radius', 'rgb'])

        groups.append({})
        for property_ in vessel['properties']:
            if type(property_) is MBFPropertyTraceAssociation:
                groups[-1]['TraceAssociation'] = property_.label()
                groups[-1]['elements'] = element_ids

        for index, associated_group in enumerate(associated_groups):
            element_id = element_ids[index]
            current_group = groups[associated_group]
            if 'elements' in current_group:
                current_group['elements'].append(element_id)
            else:
                current_group['elements'] = [element_id]

        for group in groups:
            if 'elements' in group:
                group_element_ids = group['elements']
                del group['elements']
                for key in group:
                    create_group_elements(field_module, group[key], group_element_ids)

    if punctum_data:
        _process_punctum_data(region, punctum_data)


def _determine_sub_groups(grouped_by_parent, node_to_element_map, tree, unique_paths):
    sub_groups = {}
    seen_unknown = set()
    all_unknowns = []
    for u in unique_paths:
        p = tree.properties(u)
        properties, metadata, unknown, group_primary_name = classify_properties(p, INFOSET_RANK_MAP)
        for un in unknown:
            if un not in seen_unknown:
                all_unknowns.append(un)
                seen_unknown.add(un)

        element_ids = get_elements_for_path(grouped_by_parent, node_to_element_map, u)
        group_names = _expand_properties(properties)
        for group_name in group_names:
            node_ids = grouped_by_parent[u[:-1]][:]
            node_ids.append(grouped_by_parent[u[:-2]][-1])
            if group_name in sub_groups:
                sub_groups[group_name]['el'].extend(element_ids[:])
                sub_groups[group_name]['no'].extend(node_ids)
            else:
                sub_groups[group_name] = {'el': element_ids[:], 'no': node_ids}

    if len(all_unknowns):
        print("Unknown attributes, not classified.")
        for un in all_unknowns:
            print(un)

    return sub_groups


def _group_by_parent(node_map):
    grouped_by_parent = {}
    for path, node_id in node_map.items():
        parent = path[:-1]
        grouped_by_parent[parent] = grouped_by_parent.get(parent, []) + [node_id]

    return grouped_by_parent


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
    with ChangeManager(field_module):
        mesh = field_module.findMeshByDimension(1)
        node_set = field_module.findNodesetByName('nodes')
        element_template = mesh.createElementtemplate()
        element_template.setElementShapeType(Element.SHAPE_TYPE_LINE)
        linear_basis = field_module.createElementbasis(1, Elementbasis.FUNCTION_TYPE_LINEAR_LAGRANGE)
        linear_eft = mesh.createElementfieldtemplate(linear_basis)
        for field_name in field_names:
            field = field_module.findFieldByName(field_name)
            element_template.defineField(field, -1, linear_eft)
    
        element_identifiers = []
        for element_nodes in element_node_set:
            element = mesh.createElement(-1, element_template)

            for i, node_identifier in enumerate(element_nodes):
                node = node_set.findNodeByIdentifier(node_identifier)
                element.setNode(linear_eft, i + 1, node)

            element_identifiers.append(element.getIdentifier())

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
            elif isinstance(field_values, float):
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


def create_nodes(field_module, embedded_lists, node_set_name='nodes', path=None, node_map=None, dupe_watch=None):
    if path is None:
        path = []
    if node_map is None:
        node_map = {}
    if dupe_watch is None:
        dupe_watch = {}

    node_identifiers = []
    for i, pt in enumerate(embedded_lists):
        current_path = path + [i]
        if isinstance(pt, list):
            node_ids = create_nodes(field_module, pt, node_set_name=node_set_name, path=current_path, node_map=node_map, dupe_watch=dupe_watch)
            node_identifiers.extend(node_ids)
        else:
            pos = tuple(str(f) for f in pt.coordinates())
            if pos in dupe_watch:
                local_node_id = dupe_watch[pos]
            else:
                local_node_id = create_zinc_node(field_module, pt, node_set_name=node_set_name)
                dupe_watch[pos] = local_node_id

            node_map[tuple(current_path)] = local_node_id
            node_identifiers.append(local_node_id)

    return list(set(node_identifiers))


def create_elements(field_module, connectivity, field_names=None):
    if field_names is None:
        field_names = ['coordinates']
    return create_line_elements(field_module, connectivity, field_names)


def create_group_elements(field_module, group_name, element_ids, dimension=1):
    with ChangeManager(field_module):
        group = find_or_create_field_group(field_module, name=group_name)
        # group.setSubelementHandlingMode(FieldGroup.SUBELEMENT_HANDLING_MODE_FULL)

        mesh = field_module.findMeshByDimension(dimension)
        mesh_group = group.getOrCreateMeshGroup(mesh)
        for element_id in element_ids:
            element = mesh.findElementByIdentifier(element_id)
            mesh_group.addElement(element)


def create_group_nodes(field_module, group_name, node_ids, node_set_name='nodes'):
    with ChangeManager(field_module):
        group = find_or_create_field_group(field_module, name=group_name)
        # group.setSubelementHandlingMode(FieldGroup.SUBELEMENT_HANDLING_MODE_FULL)

        nodeset = field_module.findNodesetByName(node_set_name)
        nodeset_group = group.getOrCreateNodesetGroup(nodeset)
        for group_node_id in node_ids:
            node = nodeset.findNodeByIdentifier(group_node_id)
            nodeset_group.addNode(node)


def get_element_field_template(field_module, element_identifier):
    coordinate_field = field_module.findFieldByName('coordinates')
    mesh = field_module.findMeshByDimension(1)
    element = mesh.findElementByIdentifier(element_identifier)
    element_field_template = element.getElementfieldtemplate(coordinate_field, -1)
    return element_field_template


def _expand_properties(properties):
    group_names = []

    for prop in properties.values():
        if isinstance(prop, str):
            group_names.append(prop)
        elif isinstance(prop, MBFProperty):
            group_names.extend(prop.get_group_names())
        else:
            raise TypeError(f"Unsupported property type: {type(prop)}")

    return group_names
