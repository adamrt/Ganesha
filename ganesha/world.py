import os
from math import cos, pi, sin

from panda3d.core import (
    AmbientLight,
    DirectionalLight,
    Geom,
    GeomLines,
    GeomNode,
    GeomTristrips,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    OrthographicLens,
    PNMImage,
    Point3,
)
from panda3d.core import Texture as P3DTexture
from panda3d.core import TransparencyAttrib, VBase4, VBase4F

from ganesha import fftmap
from ganesha.constants import MESH_ONLY, MOSTLY_MESH, MOSTLY_TERRAIN, TERRAIN_ONLY


def coords_to_panda(x, y, z):
    return (x, z, -y)


def uv_to_panda(polygon, u, v):
    page = polygon.texture_page
    u = u / 256.0
    v = 1.0 - (page + v / 256.0) / 4.0
    return (u, v)


def uv_to_panda2(polygon, pal, u, v):
    page = polygon.texture_page
    u = (u + pal) / (256.0 * 17)
    v = 1.0 - (page + v / 256.0) / 4.0
    return (u, v)


global_polygon_id = 0


def reset_polygon_id():
    global global_polygon_id
    global_polygon_id = 0


def next_polygon_id():
    global global_polygon_id
    current_id = global_polygon_id
    global_polygon_id += 1
    return current_id


# Basic terrain slope types
flat = {"ne": 0, "se": 0, "sw": 0, "nw": 0}
slant = {"ne": 1, "se": 0, "sw": 0, "nw": 1}
convex = {"ne": 1, "se": 0, "sw": 0, "nw": 0}
concave = {"ne": 1, "se": 1, "sw": 0, "nw": 1}

# Terrain slope types at all the different orientations.
slope_types = {
    0x00: (flat, 0),
    0x85: (slant, 0),
    0x58: (slant, 90),
    0x25: (slant, 180),
    0x52: (slant, 270),
    0x41: (convex, 0),
    0x44: (convex, 90),
    0x14: (convex, 180),
    0x11: (convex, 270),
    0x96: (concave, 0),
    0x99: (concave, 90),
    0x69: (concave, 180),
    0x66: (concave, 270),
}


class Axes:
    def __init__(self, parent):
        self.parent = parent
        self.format = GeomVertexFormat.getV3c4()
        self.node_path = None
        self.init_node_path()

    def __del__(self):
        self.node_path.remove_node()

    def init_node_path(self):
        if self.node_path:
            self.node_path.remove_node()
        vdata = GeomVertexData("name_me", self.format, Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, "vertex")
        color = GeomVertexWriter(vdata, "color")
        primitive = GeomLines(Geom.UHStatic)
        vertex.addData3f(*coords_to_panda(0, 0, 0))
        vertex.addData3f(*coords_to_panda(1000, 0, 0))
        vertex.addData3f(*coords_to_panda(0, 0, 0))
        vertex.addData3f(*coords_to_panda(0, -1000, 0))
        vertex.addData3f(*coords_to_panda(0, 0, 0))
        vertex.addData3f(*coords_to_panda(0, 0, 1000))
        color.addData4f(1.0, 0.0, 0.0, 1.0)
        color.addData4f(1.0, 0.0, 0.0, 1.0)
        color.addData4f(0.0, 1.0, 0.0, 1.0)
        color.addData4f(0.0, 1.0, 0.0, 1.0)
        color.addData4f(0.0, 0.0, 1.0, 1.0)
        color.addData4f(0.0, 0.0, 1.0, 1.0)
        primitive.addNextVertices(6)
        primitive.closePrimitive()
        geom = Geom(vdata)
        geom.addPrimitive(primitive)
        node = GeomNode("gnode")
        node.addGeom(geom)
        self.node_path = self.parent.node_path_ui.attachNewNode(node)


class Vertex:
    def __init__(self, parent, point, coords):
        self.parent = parent
        self.format = GeomVertexFormat.getV3c4()
        self.point = point
        self.coords = coords
        self.node_path = None
        self.init_node_path()

    def __del__(self):
        self.node_path.remove_node()

    def init_node_path(self):
        if self.node_path:
            self.node_path.remove_node()
        vdata = GeomVertexData("name_me", self.format, Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, "vertex")
        color = GeomVertexWriter(vdata, "color")
        primitive = GeomTristrips(Geom.UHStatic)
        vertex.addData3f(-2.0, -2.0, -2.0)
        vertex.addData3f(2.0, -2.0, -2.0)
        vertex.addData3f(0, 2.0, -2.0)
        vertex.addData3f(0, 0, 2.0)
        vertex.addData3f(-2.0, -2.0, -2.0)
        vertex.addData3f(0, 0, 2.0)
        vertex.addData3f(2.0, -2.0, -2.0)
        vertex.addData3f(0, 0, 2.0)
        vertex.addData3f(0, 2.0, -2.0)
        color_tuple = (1.0, 1.0, 1.0)
        if self.point == "A":
            color_tuple = (1.0, 0.0, 0.0)
        elif self.point == "B":
            color_tuple = (0.0, 1.0, 0.0)
        elif self.point == "C":
            color_tuple = (0.0, 0.0, 1.0)
        elif self.point == "D":
            color_tuple = (1.0, 1.0, 0.0)
        color.addData4f(*color_tuple + (1.0,))
        color.addData4f(*color_tuple + (1.0,))
        color.addData4f(*color_tuple + (1.0,))
        color.addData4f(*color_tuple + (1.0,))
        color.addData4f(*color_tuple + (1.0,))
        color.addData4f(*color_tuple + (1.0,))
        color.addData4f(*color_tuple + (1.0,))
        color.addData4f(*color_tuple + (1.0,))
        color.addData4f(*color_tuple + (1.0,))
        primitive.addNextVertices(9)
        primitive.closePrimitive()
        geom = Geom(vdata)
        geom.addPrimitive(primitive)
        node = GeomNode("gnode")
        node.addGeom(geom)
        self.node_path = self.parent.parent.node_path_ui.attachNewNode(node)
        self.node_path.setP(180)
        self.node_path.setPos(*coords_to_panda(*self.coords))


class Vector:
    def __init__(self, parent, vector, coords):
        self.parent = parent
        self.format = GeomVertexFormat.getV3c4()
        self.vector = vector
        self.coords = coords
        self.node_path = None
        self.init_node_path()

    def __del__(self):
        self.node_path.remove_node()

    def init_node_path(self):
        if self.node_path:
            self.node_path.remove_node()
        vdata = GeomVertexData("name_me", self.format, Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, "vertex")
        color = GeomVertexWriter(vdata, "color")
        primitive = GeomLines(Geom.UHStatic)
        vertex.addData3f(*coords_to_panda(*self.vector))
        vertex.addData3f(*coords_to_panda(*[-x for x in self.vector]))
        color.addData4f(
            (
                1.0,
                0.0,
                0.0,
                1.0,
            )
        )
        color.addData4f(
            (
                0.0,
                0.0,
                1.0,
                1.0,
            )
        )
        primitive.addNextVertices(2)
        primitive.closePrimitive()
        geom = Geom(vdata)
        geom.addPrimitive(primitive)
        node = GeomNode("gnode")
        node.addGeom(geom)
        self.node_path = self.parent.parent.node_path_ui.attachNewNode(node)
        self.node_path.setScale(20)
        self.node_path.setPos(*coords_to_panda(*self.coords))


class Polygon:
    def __init__(self, parent):
        self.parent = parent
        self.source = None
        self.terrain_coords = None
        self.format = GeomVertexFormat.getV3n3c4t2()
        self.node_path = None
        self.old_color = None
        self.is_hovered = False
        self.is_selected = False
        self.palette = None
        self.vA = None
        self.vB = None
        self.vC = None
        self.vD = None
        self.nA = None
        self.nB = None
        self.nC = None
        self.nD = None

    def __del__(self):
        self.node_path.remove_node()

    def from_data(self, polygon):
        self.source = polygon
        if polygon.terrain_coords:
            tcoords = polygon.terrain_coords
            self.terrain_coords = tcoords
        if polygon.A.texcoord:
            self.palette = polygon.texture_palette
        self.init_node_path()

    def init_node_path(self):
        if self.node_path:
            self.node_path.remove_node()
        polygon = self.source
        vdata = GeomVertexData("name_me", self.format, Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, "vertex")
        normal = GeomVertexWriter(vdata, "normal")
        color = GeomVertexWriter(vdata, "color")
        texcoord = GeomVertexWriter(vdata, "texcoord")
        primitive = GeomTristrips(Geom.UHStatic)
        vertex.addData3f(*coords_to_panda(*polygon.A.point.coords))
        vertex.addData3f(*coords_to_panda(*polygon.B.point.coords))
        vertex.addData3f(*coords_to_panda(*polygon.C.point.coords))
        if hasattr(polygon, "D"):
            vertex.addData3f(*coords_to_panda(*polygon.D.point.coords))
        else:
            vertex.addData3f(*coords_to_panda(*polygon.C.point.coords))
        if polygon.A.normal:
            normal.addData3f(*coords_to_panda(*polygon.A.normal.coords))
            normal.addData3f(*coords_to_panda(*polygon.B.normal.coords))
            normal.addData3f(*coords_to_panda(*polygon.C.normal.coords))
            if hasattr(polygon, "D"):
                normal.addData3f(*coords_to_panda(*polygon.D.normal.coords))
        if polygon.A.normal:
            gray = 1.0
        else:
            gray = 0.0
        self.old_color = (gray, gray, gray, 1.0)
        color.addData4f(gray, gray, gray, 1.0)
        color.addData4f(gray, gray, gray, 1.0)
        color.addData4f(gray, gray, gray, 1.0)
        if hasattr(polygon, "D"):
            color.addData4f(gray, gray, gray, 1.0)
        if polygon.A.texcoord:
            pal = (polygon.texture_palette + 1) * 256

            texcoord_A = uv_to_panda2(polygon, pal, *polygon.A.texcoord.coords)
            texcoord_B = uv_to_panda2(polygon, pal, *polygon.B.texcoord.coords)
            texcoord_C = uv_to_panda2(polygon, pal, *polygon.C.texcoord.coords)
            texcoord.addData2f(*texcoord_A)
            texcoord.addData2f(*texcoord_B)
            texcoord.addData2f(*texcoord_C)
            if hasattr(polygon, "D"):
                texcoord_D = uv_to_panda2(polygon, pal, *polygon.D.texcoord.coords)
                texcoord.addData2f(*texcoord_D)
        primitive.addNextVertices(4)
        primitive.closePrimitive()
        geom = Geom(vdata)
        geom.addPrimitive(primitive)
        node = GeomNode("gnode")
        node.addGeom(geom)
        self.node_path = self.parent.node_path_mesh.attachNewNode(node)

    def hover(self):
        self.is_hovered = True
        if not self.is_selected:
            self.node_path.reparentTo(self.parent.node_path_ui)
            self.node_path.setColor(0.5, 0.5, 1.0, 1.0)

    def unhover(self):
        self.is_hovered = False
        if not self.is_selected:
            self.node_path.reparentTo(self.parent.node_path_mesh)
            self.node_path.setColor(*self.old_color)

    def select(self):
        self.unhover()
        self.is_selected = True
        if not self.source.A.normal:
            self.node_path.reparentTo(self.parent.node_path_ui)
        self.node_path.setColor(0.0, 1.0, 0.0, 1.0)
        self.vA = Vertex(self, "A", self.source.A.point.coords)
        self.vB = Vertex(self, "B", self.source.B.point.coords)
        self.vC = Vertex(self, "C", self.source.C.point.coords)
        if self.source.A.normal:
            self.nA = Vector(
                self, self.source.A.normal.coords, self.source.A.point.coords
            )
            self.nB = Vector(
                self, self.source.B.normal.coords, self.source.B.point.coords
            )
            self.nC = Vector(
                self, self.source.C.normal.coords, self.source.C.point.coords
            )
        if hasattr(self.source, "D"):
            self.vD = Vertex(self, "D", self.source.D.point.coords)
            if self.source.A.normal:
                self.nD = Vector(
                    self, self.source.D.normal.coords, self.source.D.point.coords
                )

    def unselect(self):
        self.is_selected = False
        if not self.source.A.normal:
            self.node_path.reparentTo(self.parent.node_path_mesh)
        self.node_path.setColor(*self.old_color)
        del self.vA
        del self.vB
        del self.vC
        if self.source.A.normal:
            del self.nA
            del self.nB
            del self.nC
        if hasattr(self.source, "D"):
            del self.vD
            if self.source.A.normal:
                del self.nD


class Palette:
    def __init__(self, parent):
        self.parent = parent
        self.colors = None

    def from_data(self, data):
        self.colors = data


class Ambient_Light:
    def __init__(self, parent):
        self.parent = parent
        self.node_path = None
        self.color = None

    def __del__(self):
        self.parent.node_path_mesh.clearLight(self.node_path)
        self.node_path.remove_node()

    def from_data(self, light_data):
        self.color = light_data.color
        self.init_node_path()

    def init_node_path(self):
        if self.node_path:
            self.parent.node_path_mesh.clearLight(self.node_path)
            self.node_path.remove_node()

        alight = AmbientLight("alight")
        alight.setColor(VBase4(*[x / 127.0 for x in self.color] + [1.0]))
        self.node_path = self.parent.node_path_mesh.attachNewNode(alight)
        self.parent.node_path_mesh.setLight(self.node_path)


class Directional_Light:
    def __init__(self, parent):
        self.parent = parent
        self.format = GeomVertexFormat.getV3c4()
        self.node_path = None
        self.node_path_line = None
        self.color = None
        self.direction = None

    def __del__(self):
        self.parent.node_path_mesh.clearLight(self.node_path)
        self.node_path.remove_node()
        self.node_path_line.remove_node()

    def from_data(self, light_data):
        self.color = light_data.color
        self.direction = light_data.direction
        self.init_node_path()

    def init_node_path(self):
        if self.node_path:
            self.parent.node_path_mesh.clearLight(self.node_path)
            self.node_path.remove_node()

        dlight = DirectionalLight("dlight")
        dlight.setColor(VBase4(*[x / 2048.0 for x in self.color] + [1.0]))
        self.node_path = self.parent.node_path_mesh.attachNewNode(dlight)
        self.node_path.setPos(*coords_to_panda(*self.direction.coords))
        self.node_path.lookAt(0, 0, 0)
        self.parent.node_path_mesh.setLight(self.node_path)

    def init_node_path_line(self, light_number):
        if self.node_path_line:
            self.node_path_line.remove_node()
        vdata = GeomVertexData("name_me", self.format, Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, "vertex")
        color = GeomVertexWriter(vdata, "color")
        primitive = GeomLines(Geom.UHStatic)
        vertex.addData3f(*coords_to_panda(0, 0, 0))
        vertex.addData3f(*coords_to_panda(*self.direction.coords))
        if light_number == 0:
            line_color = (0.0, 1.0, 1.0, 1.0)
        elif light_number == 1:
            line_color = (1.0, 0.0, 1.0, 1.0)
        elif light_number == 2:
            line_color = (1.0, 1.0, 0.0, 1.0)
        color.addData4f(*line_color)
        color.addData4f(*line_color)
        primitive.addNextVertices(2)
        primitive.closePrimitive()
        geom = Geom(vdata)
        geom.addPrimitive(primitive)
        node = GeomNode("gnode")
        node.addGeom(geom)
        self.node_path_line = self.parent.node_path_ui.attachNewNode(node)
        self.node_path_line.setScale(1000)
        self.node_path_line.setPos(100, 100, 0)

    def show_line(self, show):
        if show:
            self.node_path_line.setAlphaScale(1.0)
        else:
            self.node_path_line.setAlphaScale(0.0)


class Background:
    def __init__(self, parent):
        self.parent = parent
        self.format = GeomVertexFormat.getV3c4()
        self.node_path = None
        self.color1 = None
        self.color2 = None

    def __del__(self):
        self.node_path.remove_node()

    def from_data(self, background_data):
        self.color1 = background_data.color1
        self.color2 = background_data.color2
        self.init_node_path()

    def init_node_path(self):
        if self.node_path:
            self.node_path.remove_node()
        vdata = GeomVertexData("name_me", self.format, Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, "vertex")
        color = GeomVertexWriter(vdata, "color")
        primitive = GeomTristrips(Geom.UHStatic)
        film_size = base.cam.node().getLens().getFilmSize()
        x = film_size.getX() / 2.0
        z = x * 0.75
        vertex.addData3f(-x, 10000, z)
        vertex.addData3f(x, 10000, z)
        vertex.addData3f(-x, 10000, -z)
        vertex.addData3f(x, 10000, -z)
        color.addData4f(*[x / 255.0 for x in self.color1] + [1.0])
        color.addData4f(*[x / 255.0 for x in self.color1] + [1.0])
        color.addData4f(*[x / 255.0 for x in self.color2] + [1.0])
        color.addData4f(*[x / 255.0 for x in self.color2] + [1.0])
        primitive.addNextVertices(4)
        primitive.closePrimitive()
        geom = Geom(vdata)
        geom.addPrimitive(primitive)
        node = GeomNode("gnode")
        node.addGeom(geom)
        self.node_path = base.camera.attachNewNode(node)


class Tile:
    def __init__(self, parent):
        self.parent = parent
        self.format = GeomVertexFormat.getV3c4()
        self.node_path = None
        self.tile_color = None
        self.x = None
        self.y = None
        self.z = None
        self.coords = None
        self.unknown1 = None
        self.surface_type = None
        self.unknown2 = None
        self.height = None
        self.depth = None
        self.slope_height = None
        self.slope_type = None
        self.unknown3 = None
        self.unknown4 = None
        self.cant_walk = None
        self.cant_cursor = None
        self.unknown5 = None
        self.is_hovered = False
        self.is_selected = False

    def __del__(self):
        self.node_path.remove_node()

    def from_data(self, x, y, z, tile_data):
        self.x = x
        self.y = y
        self.z = z
        self.coords = (x, z)
        self.unknown1 = tile_data.unknown1
        self.surface_type = tile_data.surface_type
        self.unknown2 = tile_data.unknown2
        self.height = tile_data.height
        self.depth = tile_data.depth
        self.slope_height = tile_data.slope_height
        self.slope_type = tile_data.slope_type
        self.unknown3 = tile_data.unknown3
        self.unknown4 = tile_data.unknown4
        self.cant_walk = tile_data.cant_walk
        self.cant_cursor = tile_data.cant_cursor
        self.unknown5 = tile_data.unknown5

    def init_node_path(self):
        if self.node_path:
            self.node_path.remove_node()
        vdata = GeomVertexData("name_me", self.format, Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, "vertex")
        color = GeomVertexWriter(vdata, "color")
        primitive = GeomTristrips(Geom.UHStatic)
        y = self.height * 12 + self.depth * 12 + 1
        try:
            (slope, rotation) = slope_types[self.slope_type]
        except KeyError:
            print("Unknown slope type:", self.slope_type)
            (slope, rotation) = (flat, 0)
        if self.slope_height == 0:
            (slope, rotation) = (flat, 0)
        scale_y = self.slope_height * 12
        vertex.addData3f(*coords_to_panda(-14.0, -slope["sw"] * scale_y, -14.0))
        vertex.addData3f(*coords_to_panda(-14.0, -slope["nw"] * scale_y, 14.0))
        vertex.addData3f(*coords_to_panda(14.0, -slope["ne"] * scale_y, 14.0))
        vertex.addData3f(*coords_to_panda(14.0, -slope["se"] * scale_y, -14.0))
        vertex.addData3f(*coords_to_panda(-14.0, -slope["sw"] * scale_y, -14.0))
        tile_color = (0.5, 0.5, 1.0)
        if self.cant_walk:
            tile_color = (1.0, 0.5, 0.5)
        if self.cant_cursor:
            tile_color = (0.5, 0.0, 0.0)
        if (self.x + self.z) % 2 == 0:
            tile_color = tuple([x * 0.8 for x in tile_color])
        self.tile_color = tile_color
        color.addData4f(*tile_color + (1.0,))
        color.addData4f(*tile_color + (1.0,))
        color.addData4f(*tile_color + (1.0,))
        color.addData4f(*tile_color + (1.0,))
        color.addData4f(*tile_color + (1.0,))
        primitive.addNextVertices(5)
        primitive.closePrimitive()
        geom = Geom(vdata)
        geom.addPrimitive(primitive)
        node = GeomNode("gnode")
        node.addGeom(geom)
        self.node_path = self.parent.node_path.attachNewNode(node)
        self.node_path.setH(rotation)
        can_stand_height = 0
        if not self.cant_cursor:
            can_stand_height = 1
        self.node_path.setPos(
            *coords_to_panda(
                self.x * 28 + 14,
                -((self.height + self.depth) * 12 + 1 + can_stand_height),
                self.z * 28 + 14,
            )
        )
        self.node_path.setTag("terrain_xyz", "%u,%u,%u" % (self.x, self.y, self.z))

    def hover(self):
        self.is_hovered = True
        if not self.is_selected:
            self.node_path.setColor(0.8, 0.5, 1.0, 1.0)

    def unhover(self):
        self.is_hovered = False
        if not self.is_selected:
            self.node_path.setColor(*self.tile_color + (1.0,))

    def select(self):
        self.unhover()
        self.is_selected = True
        self.node_path.setColor(0.0, 1.0, 0.0, 1.0)

    def unselect(self):
        self.is_selected = False
        self.node_path.setColor(*self.tile_color + (1.0,))


class Terrain:
    def __init__(self, parent):
        self.parent = parent
        self.node_path = None
        self.tiles = None

    def __del__(self):
        self.node_path.remove_node()

    def from_data(self, terrain_data):
        self.tiles = []
        y = 0
        for level_data in terrain_data.tiles:
            level = []
            for z, row_data in enumerate(level_data):
                row = []
                for x, tile_data in enumerate(row_data):
                    tile = Tile(self)
                    tile.from_data(x, y, z, tile_data)
                    row.append(tile)
                level.append(row)
            self.tiles.append(level)
            y += 1
        self.init_node_path()

    def init_node_path(self):
        if self.node_path:
            self.node_path.remove_node()
        node = GeomNode("gnode")
        self.node_path = self.parent.node_path_terrain.attachNewNode(node)
        for level in self.tiles:
            for row in level:
                for tile in row:
                    tile.init_node_path()


class Texture:
    def __init__(self):
        self.texture = None
        self.texture2 = None

    def from_data(self, texture_data, palettes):
        tex_pnm = PNMImage(17 * 256, 1024)
        tex_pnm.addAlpha()

        testpnm = PNMImage(256, 1024)

        palette = [(x, x, x, 1) for x in range(16)]
        colors = []
        for color in palette:
            color_list = [c / 15.0 for c in color[:3]]
            color_list.append(0 if color == (0, 0, 0, 0) else 1)
            colors.append(VBase4F(*color_list))

        for y in range(1024):
            row = texture_data.image[y]
            for x in range(256):
                testpnm.setXelA(x, y, colors[row[x]])

        self.texture2 = P3DTexture()
        self.texture2.load(testpnm)
        self.texture2.setMagfilter(P3DTexture.FTNearest)
        self.texture2.setMinfilter(P3DTexture.FTLinear)

        self.update(tex_pnm, texture_data, palettes)

    def update(self, pnm, texture_data, palettes):

        self.palettes = []
        temp = []
        for x in range(16):
            temp.append((x, x, x, 1))

        self.palettes.append(temp)

        for y, palette in enumerate(palettes):
            selfpalette = []
            for x, color in enumerate(palette.colors.colors):
                selfpalette.append((color[0], color[1], color[2], 1))
            self.palettes.append(selfpalette)

        i = 0
        for palette in self.palettes:
            colors = []
            for color in palette:
                color_list = [c / 15.0 for c in color[:3]]
                color_list.append(0 if color == (0, 0, 0, 0) else 1)
                colors.append(VBase4F(*color_list))

            for y in range(1024):
                row = texture_data.image[y]
                for x in range(256):
                    pnm.setXelA(x + (256 * i), y, colors[row[x]])
            i += 1

        self.texture = P3DTexture()
        self.texture.load(pnm)
        self.texture.setMagfilter(P3DTexture.FTNearest)
        self.texture.setMinfilter(P3DTexture.FTLinear)


class World:
    def __init__(self, parent):
        self.parent = parent
        self.map = fftmap.Map()
        self.node_path = None
        self.textures = []
        self.polygons = None
        self.color_palettes = None
        self.dir_lights = None
        self.amb_light = None
        self.background = None
        self.terrain = None
        self.texture_anim = None
        self.palette_anim = None
        self.gray_palettes = None
        self.polygon_anim = None
        self.animated_polygons = None
        self.center_x = 0
        self.center_y = 0
        self.center_z = 0
        self.init_camera()

    def read(self):
        self.node_path = render.attachNewNode("world")
        self.node_path.setTransparency(TransparencyAttrib.MAlpha)
        self.node_path_mesh = self.node_path.attachNewNode("mesh")
        self.node_path_ui = self.node_path.attachNewNode("ui")
        self.node_path_terrain = self.node_path_ui.attachNewNode("terrain")
        self.axes = Axes(self)
        self.map.read()
        self.get_color_palettes()
        self.get_texture()
        self.get_polygons()
        self.set_camera_zoom()
        self.get_dir_lights()
        self.get_amb_light()
        self.get_background()
        self.get_terrain()
        self.get_gray_palettes()
        self.full_light = Ambient_Light(self)
        self.full_light.color = (255, 255, 255)
        self.full_light.init_node_path()
        self.set_center()

    def init_camera(self, aspect_ratio=4.0 / 3.0):

        lens = OrthographicLens()
        lens.setAspectRatio(aspect_ratio)
        lens.setNear(-32768)
        lens.setFar(131072)
        base.cam.node().setLens(lens)

    def set_center(self):
        size_x = abs(self.map.extents[1][0] - self.map.extents[0][0])
        size_y = abs(self.map.extents[1][1] - self.map.extents[0][1])
        size_z = abs(self.map.extents[1][2] - self.map.extents[0][2])
        self.center_x = size_x / 2.0
        self.center_y = size_y / 3.0
        self.center_z = size_z / 2.0
        (self.center_x, self.center_y, self.center_z) = coords_to_panda(
            self.center_x, -self.center_y, self.center_z
        )

    def set_camera_zoom(self):
        base.cam.node().getLens().setFilmSize(self.map.hypotenuse)

    def set_camera_angle(self, azimuth, elevation):
        y = cos(pi * elevation / 180) * self.map.hypotenuse
        z = sin(pi * elevation / 180) * self.map.hypotenuse
        x = cos(pi * azimuth / 180) * y
        y = sin(pi * azimuth / 180) * y
        base.camera.setPos(self.center_x + x, self.center_y + y, self.center_z + z)

        base.camera.lookAt(Point3(self.center_x, self.center_y, self.center_z))

    def set_camera_pos(self, deltaX, deltaY):
        oldX = base.camera.getX()
        oldY = base.camera.getY()
        oldZ = base.camera.getZ()
        base.camera.setPos(base.camera, -deltaX * 150, 0, -deltaY * 150)
        self.center_x += base.camera.getX() - oldX
        self.center_y += base.camera.getY() - oldY
        self.center_z += base.camera.getZ() - oldZ

    def spin_camera(self, task):
        azimuth = task.time * 30
        elevation = 30
        self.set_camera_angle(azimuth, elevation)
        return task.cont

    def set_terrain_alpha(self, mode):
        if mode == MESH_ONLY:
            self.node_path_mesh.setAlphaScale(1.0)
            self.node_path_terrain.setAlphaScale(0.0)
        elif mode == MOSTLY_MESH:
            self.node_path_mesh.setAlphaScale(1.0)
            self.node_path_terrain.setAlphaScale(0.5)
        elif mode == MOSTLY_TERRAIN:
            self.node_path_mesh.setAlphaScale(0.5)
            self.node_path_terrain.setAlphaScale(1.0)
        elif mode == TERRAIN_ONLY:
            self.node_path_mesh.setAlphaScale(0.0)
            self.node_path_terrain.setAlphaScale(1.0)
        else:
            raise NotImplementedError()

    def set_full_light(self, light_on):
        if light_on:
            self.node_path_mesh.setLight(self.full_light.node_path)
        else:
            self.node_path_mesh.clearLight(self.full_light.node_path)

    def get_texture(self):
        texture = Texture()
        texture.from_data(self.map.get_texture(), self.color_palettes)
        self.texture = texture
        self.node_path_mesh.setTexture(self.texture.texture)

    def get_polygons(self):
        polygons = []
        reset_polygon_id()
        for i, poly_data in enumerate(self.map.get_polygons()):
            polygon = Polygon(self)
            polygon.from_data(poly_data)
            polygon_id = next_polygon_id()
            polygon.node_path.setTag("polygon_i", str(polygon_id))
            polygons.append(polygon)
        self.polygons = polygons

    def get_color_palettes(self):
        palettes = []
        for palette_data in self.map.get_color_palettes():
            palette = Palette(self)
            palette.from_data(palette_data)
            palettes.append(palette)
        self.color_palettes = palettes

    def get_dir_lights(self):
        dir_lights = []
        for i, dir_light_data in enumerate(self.map.get_dir_lights()):
            dir_light = Directional_Light(self)
            dir_light.from_data(dir_light_data)
            dir_light.init_node_path_line(i)
            dir_lights.append(dir_light)
        self.dir_lights = dir_lights

    def get_amb_light(self):
        amb_light_data = self.map.get_amb_light()
        amb_light = Ambient_Light(self)
        amb_light.from_data(amb_light_data)
        self.amb_light = amb_light

    def get_background(self):
        background_data = self.map.get_background()
        background = Background(self)
        background.from_data(background_data)
        self.background = background

    def get_terrain(self):
        terrain_data = self.map.get_terrain()
        terrain = Terrain(self)
        terrain.from_data(terrain_data)
        # Why is this necessary?
        if self.terrain:
            self.terrain.__del__()
        self.terrain = terrain

    def get_gray_palettes(self):
        palettes = []
        for palette_data in self.map.get_gray_palettes():
            palette = Palette(self)
            palette.from_data(palette_data)
            palettes.append(palette)
        self.gray_palettes = palettes

    def read_gns(self, gns_path):
        if gns_path is None:
            gns_path = self.parent.file_dialog()
        assert gns_path is not None, "No GNS file chosen. Exiting."
        self.map.gns = fftmap.GNS()
        self.map.gns.read(gns_path)
        self.map.set_situation(0)

    def next_gns(self):
        gns_path = self.map.gns.file_path
        gns_dir = os.path.dirname(gns_path)
        gns_name = os.path.basename(gns_path)
        files = []
        for file_name in os.listdir(gns_dir):
            if file_name[-4:] in [".gns", ".GNS"]:
                files.append(file_name)
        files.sort()
        found = False
        for i, file_name in enumerate(files):
            if file_name == gns_name:
                found = True
                break
        if found:
            new_i = (i + 1) % len(files)
            new_file_name = files[new_i]
            new_gns_path = os.path.join(gns_dir, new_file_name)
            self.read_gns(new_gns_path)
            self.read()

    def next_situation(self):
        sit = self.map.situation + 1
        self.map.set_situation(sit)
        self.read()

    def prev_situation(self):
        sit = self.map.situation - 1
        self.map.set_situation(sit)
        self.read()
