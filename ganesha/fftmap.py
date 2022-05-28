from math import sqrt

from struct import unpack

from ganesha.gns import GNS
from ganesha.resource import Resources
from ganesha.texture import Texture as Texture_File


class PointXYZ:
    def __init__(self, data):
        self.coords = (self.X, self.Y, self.Z) = unpack("<3h", data)


class PointUV:
    def __init__(self, data):
        self.coords = (self.U, self.V) = unpack("<2B", data)


class VectorXYZ:
    def __init__(self, data):
        self.coords = (self.X, self.Y, self.Z) = [
            x / 4096.0 for x in unpack("<3h", data)
        ]


class Vertex:
    def __init__(self, point_data, normal_data=None, texcoord_data=None):
        self.point = PointXYZ(point_data)
        self.normal = VectorXYZ(normal_data) if normal_data else None
        self.texcoord = PointUV(texcoord_data) if texcoord_data else None


class Triangle:
    def __init__(
        self,
        point,
        visangle,
        normal=None,
        texcoord=None,
        unknown5=None,
        terrain_coords=None,
    ):
        self.texture_palette = None
        self.texture_page = None
        self.visible_angles = None
        self.terrain_coords = None
        self.unknown1 = None
        self.unknown2 = None
        self.unknown3 = None
        self.unknown4 = None
        self.unknown5 = None

        if normal:
            self.A = Vertex(point[0:6], normal[0:6], texcoord[0:2])
            self.unknown1 = (unpack("B", texcoord[2:3])[0] >> 4) & 0xF
            self.texture_palette = unpack("B", texcoord[2:3])[0] & 0xF
            self.unknown2 = unpack("B", texcoord[3:4])[0]
            self.B = Vertex(point[6:12], normal[6:12], texcoord[4:6])
            self.unknown3 = (unpack("B", texcoord[6:7])[0] >> 2) & 0x3F
            self.texture_page = unpack("B", texcoord[6:7])[0] & 0x3
            self.unknown4 = unpack("B", texcoord[7:8])[0]
            self.C = Vertex(point[12:18], normal[12:18], texcoord[8:10])
            (val1, tx) = unpack("BB", terrain_coords)
            tz = val1 >> 1
            tlvl = val1 & 0x01
            self.terrain_coords = (tx, tz, tlvl)
        else:
            self.A = Vertex(point[0:6])
            self.B = Vertex(point[6:12])
            self.C = Vertex(point[12:18])
            self.unknown5 = unknown5
        vis = unpack("H", visangle)[0]
        self.visible_angles = [(vis & 2 ** (15 - x)) >> (15 - x) for x in range(16)]

    def vertices(self):
        for point in "ABC":
            yield getattr(self, point)


class Quad:
    def __init__(
        self,
        point,
        visangle,
        normal=None,
        texcoord=None,
        unknown5=None,
        terrain_coords=None,
    ):
        self.texture_palette = None
        self.texture_page = None
        self.visible_angles = None
        self.terrain_coords = None
        self.unknown1 = None
        self.unknown2 = None
        self.unknown3 = None
        self.unknown4 = None
        self.unknown5 = None

        if normal:
            self.A = Vertex(point[0:6], normal[0:6], texcoord[0:2])
            self.unknown1 = (unpack("B", texcoord[2:3])[0] >> 4) & 0xF
            self.texture_palette = unpack("B", texcoord[2:3])[0] & 0xF
            self.unknown2 = unpack("B", texcoord[3:4])[0]
            self.B = Vertex(point[6:12], normal[6:12], texcoord[4:6])
            self.unknown3 = (unpack("B", texcoord[6:7])[0] >> 2) & 0x3F
            self.texture_page = unpack("B", texcoord[6:7])[0] & 0x3
            self.unknown4 = unpack("B", texcoord[7:8])[0]
            self.C = Vertex(point[12:18], normal[12:18], texcoord[8:10])
            self.D = Vertex(point[18:24], normal[18:24], texcoord[10:12])
            (val1, tx) = unpack("BB", terrain_coords)
            tz = val1 >> 1
            tlvl = val1 & 0x01
            self.terrain_coords = (tx, tz, tlvl)
        else:
            self.A = Vertex(point[0:6])
            self.B = Vertex(point[6:12])
            self.C = Vertex(point[12:18])
            self.D = Vertex(point[18:24])
            self.unknown5 = unknown5
        vis = unpack("H", visangle)[0]
        self.visible_angles = [(vis & 2 ** (15 - x)) >> (15 - x) for x in range(16)]

    def vertices(self):
        for point in "ABCD":
            yield getattr(self, point)


class Palette:
    def __init__(self, data):
        colors = []
        for c in range(16):
            unpacked = unpack("H", data[c * 2 : c * 2 + 2])[0]
            a = (unpacked >> 15) & 0x01
            b = (unpacked >> 10) & 0x1F
            g = (unpacked >> 5) & 0x1F
            r = (unpacked >> 0) & 0x1F
            colors.append((r, g, b, a))
        self.colors = colors


class Ambient_Light:
    def __init__(self, data):
        self.color = unpack("3B", data)


class Directional_Light:
    def __init__(self, color_data, direction_data):
        self.color = unpack("3h", color_data)
        self.direction = VectorXYZ(direction_data)


class Background:
    def __init__(self, color_data):
        self.color1 = unpack("3B", color_data[0:3])
        self.color2 = unpack("3B", color_data[3:6])


class Tile:
    def __init__(self, tile_data):
        val1 = unpack("B", tile_data[0:1])[0]
        self.unknown1 = (val1 >> 6) & 0x3
        self.surface_type = (val1 >> 0) & 0x3F
        self.unknown2 = unpack("B", tile_data[1:2])[0]
        self.height = unpack("B", tile_data[2:3])[0]
        val4 = unpack("B", tile_data[3:4])[0]
        self.depth = (val4 >> 5) & 0x7
        self.slope_height = (val4 >> 0) & 0x1F
        self.slope_type = unpack("B", tile_data[4:5])[0]
        self.unknown3 = unpack("B", tile_data[5:6])[0]
        val7 = unpack("B", tile_data[6:7])[0]
        self.unknown4 = (val7 >> 2) & 0x3F
        self.cant_walk = (val7 >> 1) & 0x1
        self.cant_cursor = (val7 >> 0) & 0x1
        self.unknown5 = unpack("B", tile_data[7:8])[0]


class Terrain:
    def __init__(self, terrain_data):
        self.tiles = []
        (x_count, z_count) = unpack("2B", terrain_data[0:2])
        offset = 2
        for y in range(2):
            level = []
            for z in range(z_count):
                row = []
                for x in range(x_count):
                    tile_data = terrain_data[offset : offset + 8]
                    tile = Tile(tile_data)
                    row.append(tile)
                    offset += 8
                level.append(row)
            self.tiles.append(level)
            # Skip to second level of terrain data
            offset = 2 + 8 * 256


class Texture:
    def __init__(self, data):
        self.image = []
        for y in range(1024):
            row = []
            for x in range(128):
                i = y * 128 + x
                pair = unpack("B", data[i : i + 1])[0]
                pix1 = (pair >> 0) & 0xF
                pix2 = (pair >> 4) & 0xF
                row.append(pix1)
                row.append(pix2)
            self.image.append(row)


class Map:
    def __init__(self):
        self.gns = GNS()
        self.situation = None
        self.texture_files = None
        self.resource_files = None
        self.texture = Texture_File()
        self.resources = Resources()
        self.extents = None
        self.hypotenuse = None

    def set_situation(self, situation):
        self.situation = situation % len(self.gns.situations)
        self.texture_files = self.gns.get_texture_files(self.situation)
        self.resource_files = self.gns.get_resource_files(self.situation)
        self.texture = Texture_File()
        self.resources = Resources()

    def read(self):
        self.texture.read(self.texture_files)
        self.resources.read(self.resource_files)

    def get_texture(self):
        return Texture(self.texture.data)

    def get_polygons(self):
        minx = 32767
        miny = 32767
        minz = 32767
        maxx = -32768
        maxy = -32768
        maxz = -32768
        polygons = (
            list(self.get_tex_3gon())
            + list(self.get_tex_4gon())
            + list(self.get_untex_3gon())
            + list(self.get_untex_4gon())
        )
        for polygon in polygons:
            for vertex in polygon.vertices():
                minx = min(minx, vertex.point.X)
                miny = min(miny, vertex.point.Y)
                minz = min(minz, vertex.point.Z)
                maxx = max(maxx, vertex.point.X)
                maxy = max(maxy, vertex.point.Y)
                maxz = max(maxz, vertex.point.Z)
            yield polygon
        self.extents = ((minx, miny, minz), (maxx, maxy, maxz))
        self.get_hypotenuse()

    def get_hypotenuse(self):
        size_x = abs(self.extents[1][0] - self.extents[0][0])
        size_z = abs(self.extents[1][2] - self.extents[0][2])
        self.hypotenuse = sqrt(size_x**2 + size_z**2)

    def get_tex_3gon(self, toc_index=0x40):
        points = self.resources.get_tex_3gon_xyz(toc_index)
        if toc_index == 0x40:
            visangles = self.resources.get_tex_3gon_vis()
        else:
            visangles = ["\x00\x00"] * 512
        normals = self.resources.get_tex_3gon_norm(toc_index)
        texcoords = self.resources.get_tex_3gon_uv(toc_index)
        terrain_coords = self.resources.get_tex_3gon_terrain_coords(toc_index)
        for point, visangle, normal, texcoord, terrain_coord in zip(
            points, visangles, normals, texcoords, terrain_coords
        ):
            yield Triangle(
                point, visangle, normal, texcoord, terrain_coords=terrain_coord
            )

    def get_tex_4gon(self, toc_index=0x40):
        points = self.resources.get_tex_4gon_xyz(toc_index)
        if toc_index == 0x40:
            visangles = self.resources.get_tex_4gon_vis()
        else:
            visangles = ["\x00\x00"] * 768
        normals = self.resources.get_tex_4gon_norm(toc_index)
        texcoords = self.resources.get_tex_4gon_uv(toc_index)
        terrain_coords = self.resources.get_tex_4gon_terrain_coords(toc_index)
        for point, visangle, normal, texcoord, terrain_coord in zip(
            points, visangles, normals, texcoords, terrain_coords
        ):
            yield Quad(point, visangle, normal, texcoord, terrain_coords=terrain_coord)

    def get_untex_3gon(self, toc_index=0x40):
        points = self.resources.get_untex_3gon_xyz(toc_index)
        if toc_index == 0x40:
            visangles = self.resources.get_untex_3gon_vis()
        else:
            visangles = ["\x00\x00"] * 64
        unknowns = self.resources.get_untex_3gon_unknown(toc_index)
        for point, visangle, unknown in zip(points, visangles, unknowns):
            polygon = Triangle(point, visangle, unknown5=unknown)
            yield polygon

    def get_untex_4gon(self, toc_index=0x40):
        points = self.resources.get_untex_4gon_xyz(toc_index)
        if toc_index == 0x40:
            visangles = self.resources.get_untex_4gon_vis()
        else:
            visangles = ["\x00\x00"] * 256
        unknowns = self.resources.get_untex_4gon_unknown(toc_index)
        for point, visangle, unknown in zip(points, visangles, unknowns):
            polygon = Quad(point, visangle, unknown5=unknown)
            yield polygon

    def get_color_palettes(self):
        for data in self.resources.get_color_palettes():
            yield Palette(data)

    def get_dir_lights(self):
        colors = self.resources.get_dir_light_rgb()
        normals = self.resources.get_dir_light_norm()
        for color, normal in zip(colors, normals):
            yield Directional_Light(color, normal)

    def get_amb_light(self):
        return Ambient_Light(self.resources.get_amb_light_rgb())

    def get_background(self):
        return Background(self.resources.get_background())

    def get_terrain(self):
        return Terrain(self.resources.get_terrain())

    def get_gray_palettes(self):
        for data in self.resources.get_gray_palettes():
            yield Palette(data)
