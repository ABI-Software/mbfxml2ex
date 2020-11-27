import itertools

from opencmiss.utils.zinc.general import AbstractNodeDataObject


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
        return 'x="{0}" y="{1}" z="{2}" r="{3}"'.format(self._x, self._y, self._z, self._radius)


class MBFProperty(object):

    def __init__(self, version):
        self._version = version

    def version(self):
        return self._version

    def __repr__(self):
        return 'version="{0}"'.format(self._version)


class MBFPropertyChannel(MBFProperty):

    def __init__(self, version, number, colour):
        super(MBFPropertyChannel, self).__init__(version)
        self._number = number
        self._colour = colour

    def number(self):
        return self._number

    def colour(self):
        return self._colour

    def __repr__(self):
        version_str = super(MBFPropertyChannel, self).__repr__()
        return 'Channel {0} number="{1}" colour="{2}"'.format(version_str, self._number, self._colour)


class MBFPropertyPunctum(MBFProperty):

    def __init__(self, version, spread, mean_luminance, surface_area, voxel_count, flag_2d,
                 volume, location, colocalized_fraction, proximal_fraction):
        super(MBFPropertyPunctum, self).__init__(version)
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
        super(MBFPropertyVolumeRLE, self).__init__(-1.0)
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


class NeurolucidaZSpacing(object):

    def __init__(self, z=1.0, slices=0):
        self._z = z
        self._slices = slices

    def get_z(self):
        return self._z

    def get_slices(self):
        return self._slices

    def __repr__(self):
        return 'z = "{0}", slices = "{1}"'.format(self._z, self._slices)


class NeurolucidaChannel(object):

    def __init__(self, identifier=None, source=None):
        self._identifier = identifier
        self._source = source

    def __repr__(self):
        return 'id = "{0}", source = "{1}"'.format(self._identifier, self._source)


class NeurolucidaChannels(object):

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


class BinaryTreeNode(object):

    def __init__(self, data):

        self._left = None
        self._right = None
        self._data = data

    def insert(self, data):

        if self._data:
            if data < self._data:
                if self._left is None:
                    self._left = BinaryTreeNode(data)
                else:
                    self._left.insert(data)
            elif data > self._data:
                if self._right is None:
                    self._right = BinaryTreeNode(data)
                else:
                    self._right.insert(data)
        else:
            self._data = data

    def __contains__(self, data):
        if data < self._data:
            return False if self._left is None else data in self._left
        elif data > self._data:
            return False if self._right is None else data in self._right

        return True


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
