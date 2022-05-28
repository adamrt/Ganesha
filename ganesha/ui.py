import wx
from direct.fsm.FSM import FSM
from direct.showbase.DirectObject import DirectObject
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    CollisionHandlerQueue,
    CollisionNode,
    CollisionRay,
    CollisionTraverser,
    CullFaceAttrib,
    GeomNode,
    Point2,
    WindowProperties,
)

from ganesha.constants import (
    MESH_ONLY,
    MOSTLY_MESH,
    MOSTLY_TERRAIN,
    TERRAIN_ONLY,
    terrain_modes,
)
from ganesha.world import Polygon, World

slope_types = [
    (0x00, "Flat 0"),
    (0x85, "Incline N"),
    (0x52, "Incline E"),
    (0x25, "Incline S"),
    (0x58, "Incline W"),
    (0x41, "Convex NE"),
    (0x11, "Convex SE"),
    (0x14, "Convex SW"),
    (0x44, "Convex NW"),
    (0x96, "Concave NE"),
    (0x66, "Concave SE"),
    (0x69, "Concave SW"),
    (0x99, "Concave NW"),
]


class ViewerMouse(DirectObject):
    def __init__(self, app):
        self.app = app

        self.init_collide()
        self.has_mouse = None
        self.prev_pos = None
        self.pos = None
        self.drag_start = None
        self.hovered_object = None
        self.button2 = False
        self.altButton2 = False
        self.mouseTask = self.app.base.taskMgr.add(self.mouse_task, "mouseTask")
        self.task = None
        self.accept("mouse1", self.mouse1)
        self.accept("control-mouse1", self.mouse1)
        self.accept("mouse1-up", self.mouse1_up)
        self.accept("mouse2", self.startPan)
        self.accept("mouse2-up", self.stopCamera)
        self.accept("mouse3", self.rotateCamera)
        self.accept("alt-mouse3", self.startPan)
        self.accept("alt-up", self.endPan)
        self.accept("mouse3-up", self.stopCamera)
        self.accept("wheel_up", self.wheel_up)
        self.accept("wheel_down", self.wheel_down)

    def init_collide(self):
        self.cTrav = CollisionTraverser("MousePointer")
        self.cQueue = CollisionHandlerQueue()
        self.cNode = CollisionNode("MousePointer")
        self.cNodePath = self.app.base.camera.attachNewNode(self.cNode)
        self.cNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.cRay = CollisionRay()
        self.cNode.addSolid(self.cRay)
        self.cTrav.addCollider(self.cNodePath, self.cQueue)

    def find_object(self):
        if self.app.world.node_path:
            self.cRay.setFromLens(
                self.app.base.camNode, self.pos.getX(), self.pos.getY()
            )
            if self.app.terrain_mode in [MESH_ONLY, MOSTLY_MESH]:
                self.cTrav.traverse(self.app.world.node_path_mesh)
            elif self.app.terrain_mode in [MOSTLY_TERRAIN, TERRAIN_ONLY]:
                self.cTrav.traverse(self.app.world.node_path_terrain)
            if self.cQueue.getNumEntries() > 0:
                self.cQueue.sortEntries()
                return self.cQueue.getEntry(0).getIntoNodePath()
        return None

    def mouse_task(self, task):
        action = task.cont
        self.has_mouse = self.app.base.mouseWatcherNode.hasMouse()
        if self.has_mouse:
            self.pos = self.app.base.mouseWatcherNode.getMouse()
            if self.prev_pos:
                self.delta = self.pos - self.prev_pos
            else:
                self.delta = None
            if self.task:
                action = self.task(task)
        else:
            self.pos = None
        if self.pos:
            self.prev_pos = Point2(self.pos.getX(), self.pos.getY())
        return action

    def hover(self, task):
        if self.hovered_object:
            self.hovered_object.unhover()
            self.hovered_object = None
        if self.button2:
            self.camera_drag()
        elif self.altButton2:
            self.camera_pan()
        hovered_node_path = self.find_object()
        if hovered_node_path:
            polygon = hovered_node_path.findNetTag("polygon_i")
            if not polygon.isEmpty():
                tag = polygon.getTag("polygon_i")
                i = int(tag)
                self.hovered_object = self.app.world.polygons[i]
                self.hovered_object.hover()
            tile = hovered_node_path.findNetTag("terrain_xyz")
            if not tile.isEmpty():
                tag = tile.getTag("terrain_xyz")
                (x, y, z) = [int(i) for i in tag.split(",")]
                self.hovered_object = self.app.world.terrain.tiles[y][z][x]
                self.hovered_object.hover()
        return task.cont

    def mouse1(self):
        if self.app.base.mouseWatcherNode.hasMouse():
            self.app.state.request("mouse1")

    def mouse1_up(self):
        self.app.state.request("mouse1-up")

    def camera_pan(self):
        if self.delta:
            self.app.world.set_camera_pos(self.delta.getX(), self.delta.getY())

    def startPan(self):
        self.altButton2 = True

    def endPan(self):
        self.altButton2 = False

    def camera_drag(self):
        if self.delta:
            old_heading = self.app.base.camera.getH()
            new_heading = old_heading - self.delta.getX() * 180
            new_heading = new_heading % 360
            old_pitch = self.app.base.camera.getP()
            new_pitch = old_pitch + self.delta.getY() * 90
            new_pitch = max(-90, min(0, new_pitch))
            new_heading = 270 + new_heading
            new_pitch = -new_pitch
            self.app.world.set_camera_angle(new_heading, new_pitch)

    def rotateCamera(self):
        self.button2 = True
        self.app.state.request("mouse2")

    def stopCamera(self):
        self.button2 = False
        self.app.state.request("mouse2-up")
        self.endPan()  # Also stops panning, since mouse3 can do both rotating and panning

    def wheel_up(self):
        if self.app.base.mouseWatcherNode.hasMouse():
            lens = self.app.base.cam.node().getLens()
            size = lens.getFilmSize()
            lens.setFilmSize(size / 1.2)
            scale = self.app.world.background.node_path.getScale()
            self.app.world.background.node_path.setScale(scale / 1.2)

    def wheel_down(self):
        if self.app.base.mouseWatcherNode.hasMouse():
            lens = self.app.base.cam.node().getLens()
            size = lens.getFilmSize()
            lens.setFilmSize(size * 1.2)
            scale = self.app.world.background.node_path.getScale()
            self.app.world.background.node_path.setScale(scale * 1.2)


class ViewerState(FSM):
    def __init__(self, app, name):
        FSM.__init__(self, name)
        self.app = app

    def enterSpin(self):
        # print 'enterSpin'
        self.app.base.taskMgr.add(self.app.world.spin_camera, "spin_camera")
        self.app.mouse.task = self.app.mouse.hover

    def filterSpin(self, request, args):
        # print 'filterSpin'
        if request == "mouse2":
            return "FreeRotate"
        if request == "mouse1":
            self.app.select(self.app.mouse.hovered_object)
        return None

    def exitSpin(self):
        # print 'exitSpin'
        self.app.base.taskMgr.remove("spin_camera")
        self.app.mouse.task = None

    def enterFreeRotate(self):
        # print 'enterFreeRotate'
        self.app.mouse.task = self.app.mouse.hover

    def filterFreeRotate(self, request, args):
        if request == "mouse1" or request == "control-mouse1":
            self.app.select(self.app.mouse.hovered_object)
        return None

    def exitFreeRotate(self):
        # print 'exitFreeRotate'
        self.app.mouse.task = None


class SettingsWindow(wx.Frame):
    def __init__(self, parent, ID, title):
        self.app = parent
        wx.Frame.__init__(
            self, parent.wx_win, ID, title, wx.DefaultPosition, wx.DefaultSize
        )
        self.Bind(wx.EVT_CLOSE, self.on_close)
        panel = wx.Panel(self, wx.ID_ANY)
        sizer_sections = wx.BoxSizer(wx.VERTICAL)
        text = (
            "[: Previous state\t]: Next State\n\n"
            + "n: Next map\t\tt: Next terrain mode\n\n"
            + "s: Save\t\t\to: Output texture\n\n"
            + "Alt-Right Click / Mouse-Wheel Click + Drag: Pan Camera\n\n"
            + "CTRL + A: Select all Polygons / Tiles depending on view.\nCTRL + A repeatedly: In terrain view, cycle through multiple levels.\n\n"
            + "Holding CTRL: Allows selection of multiple polygons\non which you can perform the following on:\n\n"
            + "q: Decrease Y (12)\te: Increase Y (12)\n\n"
            + "q: Decrease Tile height (1) \te: Increase Tile height (1)\n\n"
            + "Up: Increase X (28)\tDown: Decrease X (28)\n\n"
            + "Left: Increase Z (28)\tRight: Decrease Z (28)\n\n"
        )
        text_label = wx.StaticText(panel, wx.ID_ANY, text)
        textArea = wx.BoxSizer(wx.HORIZONTAL)
        textArea.Add(text_label)
        sizer_sections.Add(textArea, flag=wx.ALL, border=10)
        panel.SetSizer(sizer_sections)
        sizer_sections.SetSizeHints(panel)
        sizer_sections.SetSizeHints(self)

    def on_close(self, event):
        self.Show(False)


# This defines what the mouse clicks do
class MapViewer(DirectObject):
    def __init__(self, *args, **kwargs):
        self.base = ShowBase()
        wp = WindowProperties()
        wp.setTitle("Ganesha")
        self.base.win.requestProperties(wp)
        self.state = ViewerState(self, "viewer_state")
        self.mouse = ViewerMouse(self)
        self.world = World(self)
        self.selected_object = None
        self.full_light_enabled = False
        self.terrain_mode = MESH_ONLY
        self.width = None
        self.height = None
        self.accept("window-event", self.on_window_event)
        self.accept("]", self.next_situation)
        self.accept("[", self.prev_situation)
        self.accept("n", self.next_gns)
        self.accept("t", self.next_terrain_mode)

        self.base.disableMouse()
        self.state.request("Spin")
        self.selected_objects = []
        self.multiSelect = False
        self.accept("control", self.multi_select)
        self.accept("control-up", self.end_multi_select)
        self.accept("q", self.decrease_Y)
        self.accept("e", self.increase_Y)
        self.accept("arrow_down", self.decrease_X)
        self.accept("arrow_up", self.increase_X)
        self.accept("arrow_right", self.decrease_Z)
        self.accept("arrow_left", self.increase_Z)
        self.accept("escape", self.open_settings_window)
        self.accept("control-a", self.select_all)
        self.select_all_mode = 0
        # self.base.messenger.toggleVerbose()

    # TODO: move these functions somewhere after start (organize)

    def multi_select(self):
        self.multiSelect = True

    def end_multi_select(self):
        self.multiSelect = False

    def select_all(self):
        # Needs special version of unselect to avoid crashes
        for obj in self.selected_objects:
            obj.unselect()
            self.selected_objects = []
        if self.selected_object:
            self.selected_object.unselect()
            self.selected_object = None

        if self.terrain_mode == MOSTLY_TERRAIN or self.terrain_mode == TERRAIN_ONLY:
            if self.select_all_mode == 2:
                self.select_all_mode = 0
            else:
                self.select_all_mode += 1
            if self.select_all_mode == 2:
                for i in range(len(self.world.terrain.tiles)):
                    for j in range(len(self.world.terrain.tiles[i])):
                        for p in range(len(self.world.terrain.tiles[i][j])):
                            self.world.terrain.tiles[i][j][p].select()
                            self.selected_objects.append(
                                self.world.terrain.tiles[i][j][p]
                            )
            else:
                for j in range(len(self.world.terrain.tiles[self.select_all_mode])):
                    for p in range(
                        len(self.world.terrain.tiles[self.select_all_mode][j])
                    ):
                        self.world.terrain.tiles[self.select_all_mode][j][p].select()
                        self.selected_objects.append(
                            self.world.terrain.tiles[self.select_all_mode][j][p]
                        )
        else:
            for obj in self.world.polygons:
                obj.select()
                self.selected_objects.append(obj)

    def increase_Y(self):
        if len(self.selected_objects) > 0:
            if isinstance(self.selected_objects[0], Polygon):
                self.world.move_selected_poly("Y", 12, 1, self.selected_objects)
            else:  # It is a tile
                self.world.move_selected_tile(1, self.selected_objects)
        elif isinstance(self.selected_object, Polygon):
            self.world.move_selected_poly("Y", 12, 1, [self.selected_object])
        else:  # It is a tile
            if self.selected_object:
                self.world.move_selected_tile(1, [self.selected_object])

    def decrease_Y(self):
        if len(self.selected_objects) > 0:
            if isinstance(self.selected_objects[0], Polygon):
                self.world.move_selected_poly("Y", 12, -1, self.selected_objects)
            else:  # It is a tile
                self.world.move_selected_tile(-1, self.selected_objects)
        elif isinstance(self.selected_object, Polygon):
            self.world.move_selected_poly("Y", 12, -1, [self.selected_object])
        else:  # It is a tile
            if self.selected_object:
                self.world.move_selected_tile(-1, [self.selected_object])

    def increase_X(self):
        if len(self.selected_objects) > 0:
            if isinstance(self.selected_objects[0], Polygon):
                self.world.move_selected_poly("X", 28, 1, self.selected_objects)
        elif isinstance(self.selected_object, Polygon):
            self.world.move_selected_poly("X", 28, 1, [self.selected_object])

    def decrease_X(self):
        if len(self.selected_objects) > 0:
            if isinstance(self.selected_objects[0], Polygon):
                self.world.move_selected_poly("X", 28, -1, self.selected_objects)
        elif isinstance(self.selected_object, Polygon):
            self.world.move_selected_poly("X", 28, -1, [self.selected_object])

    def increase_Z(self):
        if len(self.selected_objects) > 0:
            if isinstance(self.selected_objects[0], Polygon):
                self.world.move_selected_poly("Z", 28, 1, self.selected_objects)
        elif isinstance(self.selected_object, Polygon):
            self.world.move_selected_poly("Z", 28, 1, [self.selected_object])

    def decrease_Z(self):
        if len(self.selected_objects) > 0:
            if isinstance(self.selected_objects[0], Polygon):
                self.world.move_selected_poly("Z", 28, -1, self.selected_objects)
        elif isinstance(self.selected_object, Polygon):
            self.world.move_selected_poly("Z", 28, -1, [self.selected_object])

    def start(self, gns_path):
        self.wx_app = wx.App(0)
        self.wx_win = wx.Frame(None, -1, "Ganesha wxWindow", wx.DefaultPosition)
        self.wx_event_loop = wx.GUIEventLoop()
        wx.GUIEventLoop.SetActive(self.wx_event_loop)

        self.base.taskMgr.add(self.handle_wx_events, "handle_wx_events")
        self.base.render.setAttrib(
            CullFaceAttrib.make(CullFaceAttrib.MCullCounterClockwise)
        )
        self.world.read_gns(gns_path)
        self.world.read()
        self.world.set_terrain_alpha(self.terrain_mode)
        self.set_full_light(self.full_light_enabled)
        self.settings_window = SettingsWindow(self, -1, "Settings Window")
        self.base.run()

    def handle_wx_events(self, task):
        while self.wx_event_loop.Pending():
            self.wx_event_loop.Dispatch()
        self.wx_event_loop.ProcessIdle()
        return task.cont

    def on_window_event(self, window):
        changed = False
        size_x = window.getProperties().getXSize()
        size_y = window.getProperties().getYSize()
        title = window.getProperties().getTitle()
        if title != "Ganesha":
            return None
        if size_x != self.width:
            self.width = size_x
            changed = True
        if size_y != self.height:
            self.height = size_y
            changed = True
        if changed:
            self.world.init_camera(1.0 * size_x / size_y)
            self.world.set_camera_zoom()

    def file_dialog(self):
        dlg = wx.FileDialog(
            self.wx_win, "Choose a GNS file", wildcard="GNS Files (*.GNS)|*.GNS;*.gns"
        )
        if dlg.ShowModal() == wx.ID_OK:
            return dlg.GetPath()
        dlg.Destroy()
        return None

    def set_full_light(self, light_on):
        self.full_light_enabled = light_on
        self.world.set_full_light(light_on)

    def find_polygon(self, level):
        tile = self.selected_object
        found = False
        for polygon in self.world.polygons:
            if polygon.terrain_coords == (tile.x, tile.z, level):
                self.terrain_mode = MOSTLY_MESH
                self.world.set_terrain_alpha(self.terrain_mode)
                self.select(polygon)
                found = True
                break
        if not found:
            print("No polygon found for the selected tile.")

    def find_tile(self):
        polygon = self.selected_object
        (x, z, level) = polygon.source.terrain_coords
        tile = None
        try:
            tile = self.world.terrain.tiles[level][z][x]
        except IndexError:
            print("No tile found for the selected polygon.")
        if tile is not None:
            self.terrain_mode = MOSTLY_TERRAIN
            self.world.set_terrain_alpha(self.terrain_mode)
            self.select(tile)

    def open_settings_window(self):
        self.settings_window.Show(True)

    def select(self, hovered_object):
        self.unselect()
        if hovered_object:
            if self.multiSelect:
                # If the object is not already selected
                if hovered_object not in self.selected_objects:
                    # If the list is empty, or if the types in the list match the type selected (so we don't mix Tile / Poly)
                    if len(self.selected_objects) == 0 or type(
                        self.selected_objects[0]
                    ) == type(hovered_object):
                        self.selected_objects.append(hovered_object)
                        hovered_object.select()
                    # If the user tries to multi-select polygons and tiles together, don't
                    else:
                        pass
                # If the object is already selected
                else:
                    self.selected_objects.remove(hovered_object)
                    hovered_object.unselect()
            else:
                self.selected_object = hovered_object
                self.selected_object.select()

    def unselect(self):
        if not self.multiSelect:
            for obj in self.selected_objects:
                obj.unselect()
            self.selected_objects = []
        if self.selected_object:
            self.selected_object.unselect()
            self.selected_object = None

    def next_situation(self):
        self.unselect()
        self.world.next_situation()
        self.world.set_terrain_alpha(self.terrain_mode)
        self.set_full_light(self.full_light_enabled)

    def prev_situation(self):
        self.unselect()
        self.world.prev_situation()
        self.world.set_terrain_alpha(self.terrain_mode)
        self.set_full_light(self.full_light_enabled)

    def next_gns(self):
        self.unselect()
        self.world.next_gns()
        self.world.set_terrain_alpha(self.terrain_mode)
        self.set_full_light(self.full_light_enabled)

    def next_terrain_mode(self):
        self.terrain_mode += 1
        self.terrain_mode %= len(terrain_modes)
        self.world.set_terrain_alpha(self.terrain_mode)
        self.set_full_light(self.full_light_enabled)
