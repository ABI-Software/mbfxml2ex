import itertools
import xml.etree.ElementTree as ET

from cmlibs.utils.zinc.general import AbstractNodeDataObject

from mbfxml2ex.conversions import hex_to_rgb
from mbfxml2ex.exceptions import MBFImagesException


class MBFPoint(AbstractNodeDataObject):

    def __init__(self, x, y, z, diameter=0.0):
        super(MBFPoint, self).__init__(['coordinates', 'radius'])
        self._x = x
        self._y = y
        self._z = z
        self._radius = diameter / 2.0

    def get(self):
        return [self._x, self._y, self._z, self._radius]

    def coordinates(self):
        return [self._x, self._y, self._z]

    def radius(self):
        return self._radius

    def scale(self, scale):
        self._x = self._x * scale[0]
        self._y = self._y * scale[1]

    def offset(self, offset):
        self._x = self._x + offset[0]
        self._y = self._y + offset[1]
        self._z = self._z + offset[2]

    def __repr__(self):
        return f'x="{self._x}" y="{self._y}" z="{self._z}" r="{self._radius}"'


class MBFProperty:

    def __init__(self, name, version):
        self._name = name
        self._version = version

    def is_valid(self):
        return True

    def version(self):
        return self._version

    def name(self):
        return self._name

    def get_group_names(self):
        raise NotImplementedError("Subclasses that make groups must implement get_group_names()")

    def __repr__(self):
        return f'name="{self._name}", version="{self._version}"'


class MBFPropertyChannel(MBFProperty):

    def __init__(self, version, number, colour):
        super(MBFPropertyChannel, self).__init__("Channel", version)
        self._number = number
        self._colour = colour

    def number(self):
        return self._number

    def colour(self):
        return self._colour

    def __repr__(self):
        version_str = super(MBFPropertyChannel, self).__repr__()
        return 'Channel {0} number="{1}" colour="{2}"'.format(version_str, self._number, self._colour)


class MBFPropertyFillDensity(MBFProperty):

    def __init__(self, number):
        super(MBFPropertyFillDensity, self).__init__("FillDensity", -1.0)
        self._number = number

    def number(self):
        return self._number


class MBFPropertyTreeOrder(MBFProperty):

    def __init__(self, number):
        super(MBFPropertyTreeOrder, self).__init__("TreeOrder", "1")
        self._number = number

    def number(self):
        return self._number

    def __repr__(self):
        version_str = super(MBFPropertyTreeOrder, self).__repr__()
        return f'Shaft={self._number} [{version_str}]'


class MBFPropertyPunctum(MBFProperty):

    def __init__(self, version, spread, mean_luminance, surface_area, voxel_count, flag_2d,
                 volume, location, colocalized_fraction, proximal_fraction):
        super(MBFPropertyPunctum, self).__init__("Punctum", version)
        self._spread = spread
        self._mean_luminance = mean_luminance
        self._surface_area = surface_area
        self._voxel_count = voxel_count
        self._flag_2d = flag_2d
        self._volume = volume
        self._location = location
        self._colocalized_fraction = colocalized_fraction
        self._proximal_fraction = proximal_fraction

    def spread(self):
        return self._spread

    def mean_luminance(self):
        return self._mean_luminance

    def surface_area(self):
        return self._surface_area

    def voxel_count(self):
        return self._voxel_count

    def flag_2d(self):
        return self._flag_2d

    def volume(self):
        return self._volume

    def location(self):
        return self._location

    def colocalized_fraction(self):
        return self._colocalized_fraction

    def proximal_fraction(self):
        return self._proximal_fraction

    def __repr__(self):
        version_str = super(MBFPropertyPunctum, self).__repr__()
        return 'Punctum {0} spread="{1}" mean_luminance="{2}" surface_area="{3}" voxel_count="{4}" flag_2d="{5}" ' \
               'volume="{6}" location="{7}" colocalized_fraction="{8}" proximal_fraction="{9}"'.format(
                version_str, self._spread, self._mean_luminance, self._surface_area, self._voxel_count, self._flag_2d,
                self._volume, self._location, self._colocalized_fraction, self._proximal_fraction)


class MBFPropertyVolumeRLE(MBFProperty):

    def __init__(self, volume_description):
        super(MBFPropertyVolumeRLE, self).__init__("VolumeRLE", -1.0)
        self._volume_description = volume_description

    def volume_description(self):
        return self._volume_description

    def scaling(self):
        v = self._volume_description
        return [float(v[0]), float(v[1]), float(v[2])]

    def foreground_voxels_total(self):
        return int(self._volume_description[3])

    def voxel_counts(self):
        v = self._volume_description
        return [float(v[4]), float(v[5]), float(v[6])]

    def origin(self):
        v = self._volume_description
        return [float(v[7]), float(v[8]), float(v[9])]

    def voxel_run(self):
        v = self._volume_description[:]
        return [int(num) for num in v[10:]]

    def corner_coordinates(self):
        origin = self.origin()
        counts = self.voxel_counts()
        scaling = self.scaling()
        min_corner = [origin[index] - scaling[index] * (counts[index] - 1) / 2 for index in [0, 1, 2]]
        max_corner = [origin[index] + scaling[index] * (counts[index] - 1) / 2 for index in [0, 1, 2]]
        corners = list(itertools.product(*zip(min_corner, max_corner)))
        corner_ordering = [0, 4, 2, 6, 1, 5, 3, 7]
        return [list(corners[index]) for index in corner_ordering]

    def __repr__(self):
        return 'Volume RLE {0}'.format(self._volume_description)


class MBFPropertyText(MBFProperty):

    def __init__(self, name, label, version=-1.0):
        super(MBFPropertyText, self).__init__(name, version)
        self._label = label

    def label(self):
        return self._label

    def get_group_names(self):
        return [self._label]


class MBFPropertySet(MBFProperty):

    def __init__(self, items):
        super(MBFPropertySet, self).__init__("Set", -1.0)
        self._items = items

    def items(self):
        return self._items

    def get_group_names(self):
        return self._items

    def __repr__(self):
        return 'Set: "{0}"'.format(', '.join(self._items))


class MBFAttribute:
    def __init__(self, name, value):
        self._name = name
        self._value = value

    def name(self):
        return self._name

    def value(self):
        return self._value

    def __repr__(self):
        return f"{self._name} = {self._value}"


class MBFPropertyGeneric(MBFProperty):

    def __init__(self, name, items):
        super(MBFPropertyGeneric, self).__init__(name, -1.0)
        self._items = items

    def items(self):
        return self._items

    def is_valid(self):
        valid = True
        for item in self._items:
            for k, v in item.items():
                if k == 'n':
                    valid = isinstance(v, float)
                elif k in ['s', 'c']:
                    valid = isinstance(v, str) and v
                else:
                    print(k, v)
                    raise NotImplementedError

        return valid

    def text(self):
        s = [f'{key}={val}' for item in self._items for key, val in item.items()]
        return f'<name={self.name()}><{"=".join(s)}>'

    def to_xml(self):
        root = ET.Element("property", name=self._name)
        for item in self._items:
            for key, value in item.items():
                child = ET.SubElement(root, key)
                if key == 'n':
                    child.text = str(int(value))  # Convert float to int string
                else:
                    child.text = value
        return ET.tostring(root, encoding='utf-8').decode()

    def __repr__(self):
        props = [f'{key}: {val}' for d in self._items for key, val in d.items()]
        return 'Generic property: "{0}" --> "{1}"'.format(self._name, ', '.join(props))


class MBFPropertyTraceAssociation(MBFPropertyText):

    def __init__(self, label):
        super(MBFPropertyTraceAssociation, self).__init__("TraceAssociation", label)

    def __repr__(self):
        return f'{self._name} "{self._label}"'


class MBFPropertyGUID(MBFPropertyText):

    def __init__(self, label):
        super(MBFPropertyGUID, self).__init__("GUID", label)

    def is_valid(self):
        print(self._label)
        return self._label is not None

    def to_xml(self):
        root = ET.Element("property", name="GUID")
        child = ET.SubElement(root, "s")
        child.text = self._label
        return ET.tostring(root, encoding='utf-8')

    def __repr__(self):
        return 'GUID "{0}"'.format(self._label)


class NeurolucidaZSpacing:

    def __init__(self, z=1.0, slices=0):
        self._z = z
        self._slices = slices

    def get_z(self):
        return self._z

    def get_slices(self):
        return self._slices

    def __repr__(self):
        return 'z = "{0}", slices = "{1}"'.format(self._z, self._slices)


class NeurolucidaChannel:

    def __init__(self, identifier=None, source=None):
        self._identifier = identifier
        self._source = source

    def __repr__(self):
        return 'id = "{0}", source = "{1}"'.format(self._identifier, self._source)


class NeurolucidaChannels:

    def __init__(self, merge):
        self._merge = merge
        self._channels = []

    def add_channel(self, channel):
        self._channels.append(channel)

    def __repr__(self):
        rep = 'merge = "{0}" ['.format(self._merge)
        rep += '; '.join([str(channel) for channel in self._channels])
        rep += "]"

        return rep


class MBFTree:

    def __init__(self, mbf_points):
        self._mbf_points = mbf_points

    def colour(self):
        return self._mbf_points['attributes'].get('color', '#000000')

    def rgb(self):
        return hex_to_rgb(self.colour())

    def properties(self, path):
        props, attrs = _determine_branch_properties(self._mbf_points, path)
        return props + [(k, v) for k, v in attrs.items()]

    def leaf(self):
        return self._mbf_points['attributes'].get('leaf')

    def type(self):
        return self._mbf_points['attributes'].get('type')

    def points(self):
        return _retrieve_points(self._mbf_points)
    #
    # def point_properties(self):
    #     return _determine_point_properties(self._structure)


def _determine_branch_properties(branch, path):
    parent_path = path[:-1]
    attributes = branch['attributes']
    for entry in parent_path:
        branch = branch['points'][entry]
        attributes = {**attributes, **branch['attributes']}

    return branch['properties'], attributes


def _retrieve_points(structure):
    points = []
    for item in structure['points']:
        if type(item) is dict:
            points.append(_retrieve_points(item))
        else:
            points.append(item)

    return points


class MBFData(object):

    def __init__(self):
        self._trees = []
        self._contours = []
        self._markers = []
        self._images = []
        self._vessels = []

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

    def add_vessel(self, vessel_data):
        self._vessels.append(vessel_data)

    def get_vessels(self):
        return self._vessels

    def get_vessel(self, index):
        return self._vessels[index]

    def vessel_count(self):
        return len(self._vessels)

    def set_images(self, images):
        self._images = images

    def _scale_and_offset_contours(self, scale, offset):
        for contour in self._contours:
            for data in contour['data']:
                data.scale(scale)
                data.offset(offset)

    def _scale_and_offset_markers(self, scale, offset):
        for marker in self._markers:
            for data in marker['data']:
                data.scale(scale)
                data.offset(offset)

    def _scale_and_offset_tree(self, tree, scale, offset):
        modified_tree = []
        for pt in tree:
            if isinstance(pt, list):
                modified_tree.append(self._scale_and_offset_tree(pt, scale, offset))
            else:
                pt.scale(scale)
                pt.offset(offset)
                modified_tree.append(pt)

        return modified_tree

    def _scale_and_offset_trees(self, scale, offset):
        modified_trees = []
        for tree in self._trees:
            modified_trees.append(self._scale_and_offset_tree(tree, scale, offset))

        self._trees = modified_trees

    def process_scaling_and_offset(self):
        common_image_info = None
        for image_info in self._images:
            if common_image_info is None:
                common_image_info = image_info
            elif common_image_info['scale'] != image_info['scale'] and \
                    common_image_info['offset'] != image_info['offset']:
                raise MBFImagesException("Multiple images do not have the same scale and offset.")

        if common_image_info and common_image_info['scale'] != [1.0, 1.0]:
            self._scale_and_offset_contours(common_image_info['scale'], common_image_info['offset'])
            self._scale_and_offset_markers(common_image_info['scale'], common_image_info['offset'])
            self._scale_and_offset_trees(common_image_info['scale'], common_image_info['offset'])

        # if len(self._images) > 0:
        #     if len(self._images) == 1:
        #         image_info = self._images[0]
        #         if image_info['scale'] != [1.0, 1.0]:
        #             self._scale_and_offset_contours(image_info['scale'], image_info['offset'])
        #             self._scale_and_offset_markers(image_info['scale'], image_info['offset'])
        #             self._scale_and_offset_trees(image_info['scale'], image_info['offset'])
        #
        #     else:
        #         raise MBFImagesException("Multiple individual images not yet handled.")

    def __len__(self):
        len_trees = len(self._trees)
        len_contours = len(self._contours)
        len_markers = len(self._markers)
        len_images = len(self._images)
        len_vessels = len(self._vessels)

        return len_trees + len_markers + len_contours + len_images + len_vessels


def get_text_properties(properties):
    text_properties = []
    for property_ in properties:
        if isinstance(property_, MBFPropertyText) and property_.label():
            text_properties.append(property_.label())
        elif isinstance(property_, MBFPropertySet) and len(property_.items()):
            text_properties.extend(property_.items())
        elif isinstance(property_, MBFPropertyGUID) and property_.is_valid():
            text_properties.append(property_.to_xml())
        elif isinstance(property_, MBFPropertyGeneric) and property_.is_valid():
            text_properties.append(property_.to_xml())

    return text_properties


def _get_inherited_properties(properties):
    inherited_properties = []
    for property_ in properties:
        if isinstance(property_, MBFPropertySet) and len(property_.items()):
            inherited_properties.extend(property_.items())

    return inherited_properties
