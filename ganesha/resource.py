from os.path import getsize
from struct import unpack


class Resource:
    def __init__(self):
        super(Resource, self).__init__()
        self.file_path = None
        self.file = None
        self.chunks = [""] * 49
        self.size = None

    def read(self, file_path):
        self.file_path = file_path
        self.size = getsize(self.file_path)
        self.file = open(self.file_path, "rb")
        toc = list(unpack("<49I", self.file.read(0xC4)))
        self.file.seek(0)
        data = self.file.read()
        self.file.close()
        toc.append(self.size)
        for i, entry in enumerate(toc[:-1]):
            begin = toc[i]
            if begin == 0:
                continue
            end = None
            for j in range(i + 1, len(toc)):
                if toc[j]:
                    end = toc[j]
                    break
            self.chunks[i] = data[begin:end]
        self.toc = toc


class Resources:
    def __init__(self):
        super(Resources, self).__init__()
        self.chunks = [None] * 49

    def read(self, files):
        for file_path in files:
            resource = Resource()
            resource.read(file_path)
            for i in range(49):
                if self.chunks[i] is not None:
                    continue
                if resource.chunks[i]:
                    self.chunks[i] = resource

    def get_tex_3gon_xyz(self, toc_offset=0x40):
        resource = self.chunks[toc_offset // 4]
        data = resource.chunks[toc_offset // 4]
        (tri_count, quad_count, untri_count, unquad_count) = unpack("<4H", data[0:8])
        offset = 8
        for i in range(tri_count):
            polygon_data = data[offset : offset + 18]
            yield polygon_data
            offset += 18

    def get_tex_4gon_xyz(self, toc_offset=0x40):
        resource = self.chunks[toc_offset // 4]
        data = resource.chunks[toc_offset // 4]
        (tri_count, quad_count, untri_count, unquad_count) = unpack("<4H", data[0:8])
        offset = 8 + tri_count * 18
        for i in range(quad_count):
            polygon_data = data[offset : offset + 24]
            yield polygon_data
            offset += 24

    def get_untex_3gon_xyz(self, toc_offset=0x40):
        resource = self.chunks[toc_offset // 4]
        data = resource.chunks[toc_offset // 4]
        (tri_count, quad_count, untri_count, unquad_count) = unpack("<4H", data[0:8])
        offset = 8 + tri_count * 18 + quad_count * 24
        for i in range(untri_count):
            polygon_data = data[offset : offset + 18]
            yield polygon_data
            offset += 18

    def get_untex_4gon_xyz(self, toc_offset=0x40):
        resource = self.chunks[toc_offset // 4]
        data = resource.chunks[toc_offset // 4]
        (tri_count, quad_count, untri_count, unquad_count) = unpack("<4H", data[0:8])
        offset = 8 + tri_count * 18 + quad_count * 24 + untri_count * 18
        for i in range(unquad_count):
            polygon_data = data[offset : offset + 24]
            yield polygon_data
            offset += 24

    def get_tex_3gon_norm(self, toc_offset=0x40):
        resource = self.chunks[toc_offset // 4]
        data = resource.chunks[toc_offset // 4]
        (tri_count, quad_count, untri_count, unquad_count) = unpack("<4H", data[0:8])
        offset = (
            8 + tri_count * 18 + quad_count * 24 + untri_count * 18 + unquad_count * 24
        )
        for i in range(tri_count):
            normal_data = data[offset : offset + 18]
            yield normal_data
            offset += 18

    def get_tex_4gon_norm(self, toc_offset=0x40):
        resource = self.chunks[toc_offset // 4]
        data = resource.chunks[toc_offset // 4]
        (tri_count, quad_count, untri_count, unquad_count) = unpack("<4H", data[0:8])
        offset = (
            8
            + tri_count * 18
            + quad_count * 24
            + untri_count * 18
            + unquad_count * 24
            + tri_count * 18
        )
        for i in range(quad_count):
            normal_data = data[offset : offset + 24]
            yield normal_data
            offset += 24

    def get_tex_3gon_uv(self, toc_offset=0x40):
        resource = self.chunks[toc_offset // 4]
        data = resource.chunks[toc_offset // 4]
        (tri_count, quad_count, untri_count, unquad_count) = unpack("<4H", data[0:8])
        offset = (
            8
            + tri_count * 18
            + quad_count * 24
            + untri_count * 18
            + unquad_count * 24
            + tri_count * 18
            + quad_count * 24
        )
        for i in range(tri_count):
            texcoord_data = data[offset : offset + 10]
            yield texcoord_data
            offset += 10

    def get_tex_4gon_uv(self, toc_offset=0x40):
        resource = self.chunks[toc_offset // 4]
        data = resource.chunks[toc_offset // 4]
        (tri_count, quad_count, untri_count, unquad_count) = unpack("<4H", data[0:8])
        offset = (
            8
            + tri_count * 18
            + quad_count * 24
            + untri_count * 18
            + unquad_count * 24
            + tri_count * 18
            + quad_count * 24
            + tri_count * 10
        )
        for i in range(quad_count):
            texcoord_data = data[offset : offset + 12]
            yield texcoord_data
            offset += 12

    def get_untex_3gon_unknown(self, toc_offset=0x40):
        resource = self.chunks[toc_offset // 4]
        data = resource.chunks[toc_offset // 4]
        (tri_count, quad_count, untri_count, unquad_count) = unpack("<4H", data[0:8])
        offset = (
            8
            + tri_count * 18
            + quad_count * 24
            + untri_count * 18
            + unquad_count * 24
            + tri_count * 18
            + quad_count * 24
            + tri_count * 10
            + quad_count * 12
        )
        for i in range(untri_count):
            unk_data = data[offset : offset + 4]
            yield unk_data
            offset += 4

    def get_untex_4gon_unknown(self, toc_offset=0x40):
        resource = self.chunks[toc_offset // 4]
        data = resource.chunks[toc_offset // 4]
        (tri_count, quad_count, untri_count, unquad_count) = unpack("<4H", data[0:8])
        offset = (
            8
            + tri_count * 18
            + quad_count * 24
            + untri_count * 18
            + unquad_count * 24
            + tri_count * 18
            + quad_count * 24
            + tri_count * 10
            + quad_count * 12
            + untri_count * 4
        )
        for i in range(unquad_count):
            unk_data = data[offset : offset + 4]
            yield unk_data
            offset += 4

    def get_tex_3gon_terrain_coords(self, toc_offset=0x40):
        resource = self.chunks[toc_offset // 4]
        data = resource.chunks[toc_offset // 4]
        (tri_count, quad_count, untri_count, unquad_count) = unpack("<4H", data[0:8])
        offset = (
            8
            + tri_count * 18
            + quad_count * 24
            + untri_count * 18
            + unquad_count * 24
            + tri_count * 18
            + quad_count * 24
            + tri_count * 10
            + quad_count * 12
            + untri_count * 4
            + unquad_count * 4
        )
        for i in range(tri_count):
            terrain_coord_data = data[offset : offset + 2]
            yield terrain_coord_data
            offset += 2

    def get_tex_4gon_terrain_coords(self, toc_offset=0x40):
        resource = self.chunks[toc_offset // 4]
        data = resource.chunks[toc_offset // 4]
        (tri_count, quad_count, untri_count, unquad_count) = unpack("<4H", data[0:8])
        offset = (
            8
            + tri_count * 18
            + quad_count * 24
            + untri_count * 18
            + unquad_count * 24
            + tri_count * 18
            + quad_count * 24
            + tri_count * 10
            + quad_count * 12
            + untri_count * 4
            + unquad_count * 4
            + tri_count * 2
        )
        for i in range(quad_count):
            terrain_coord_data = data[offset : offset + 2]
            yield terrain_coord_data
            offset += 2

    def get_tex_3gon_vis(self, toc_offset=0xB0):
        resource = self.chunks[toc_offset // 4]
        data = resource.chunks[toc_offset // 4]
        offset = 0x380
        for i in range(512):
            vis_data = data[offset : offset + 2]
            yield vis_data
            offset += 2

    def get_tex_4gon_vis(self, toc_offset=0xB0):
        resource = self.chunks[toc_offset // 4]
        data = resource.chunks[toc_offset // 4]
        offset = 0x380 + 512 * 2
        for i in range(768):
            vis_data = data[offset : offset + 2]
            yield vis_data
            offset += 2

    def get_untex_3gon_vis(self, toc_offset=0xB0):
        resource = self.chunks[toc_offset // 4]
        data = resource.chunks[toc_offset // 4]
        offset = 0x380 + 512 * 2 + 768 * 2
        for i in range(64):
            vis_data = data[offset : offset + 2]
            yield vis_data
            offset += 2

    def get_untex_4gon_vis(self, toc_offset=0xB0):
        resource = self.chunks[toc_offset // 4]
        data = resource.chunks[toc_offset // 4]
        offset = 0x380 + 512 * 2 + 768 * 2 + 64 * 2
        for i in range(256):
            vis_data = data[offset : offset + 2]
            yield vis_data
            offset += 2

    def get_color_palettes(self, toc_offset=0x44):
        resource = self.chunks[toc_offset // 4]
        data = resource.chunks[toc_offset // 4]
        offset = 0
        for i in range(16):
            yield data[offset : offset + 32]
            offset += 32

    def get_dir_light_rgb(self, toc_offset=0x64):
        resource = self.chunks[toc_offset // 4]
        data = resource.chunks[toc_offset // 4]
        offset = 0
        for i in range(3):
            yield data[offset : offset + 2] + data[offset + 6 : offset + 8] + data[
                offset + 12 : offset + 14
            ]
            offset += 2

    def get_dir_light_norm(self, toc_offset=0x64):
        resource = self.chunks[toc_offset // 4]
        data = resource.chunks[toc_offset // 4]
        offset = 18
        for i in range(3):
            yield data[offset : offset + 6]
            offset += 6

    def get_amb_light_rgb(self, toc_offset=0x64):
        resource = self.chunks[toc_offset // 4]
        data = resource.chunks[toc_offset // 4]
        offset = 36
        return data[offset : offset + 3]

    def get_background(self, toc_offset=0x64):
        resource = self.chunks[toc_offset // 4]
        data = resource.chunks[toc_offset // 4]
        offset = 39
        return data[offset : offset + 6]

    def get_terrain(self, toc_offset=0x68):
        resource = self.chunks[toc_offset // 4]
        data = resource.chunks[toc_offset // 4]
        return data

    def get_gray_palettes(self, toc_offset=0x7C):
        resource = self.chunks[toc_offset // 4]
        data = resource.chunks[toc_offset // 4]
        offset = 0
        for i in range(16):
            yield data[offset : offset + 32]
            offset += 32
