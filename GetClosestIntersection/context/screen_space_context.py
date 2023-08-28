import maya.api.OpenMaya as om
import maya.api.OpenMayaUI as omui
import maya.cmds as cmds

import core.project_to_3d as project_to_3d
import core.octree as octree
import core.bvh as bvh
import util.mesh_list as mesh_list
import util.timer as timer

PLUG_IN_NAME = "ReturnClosestIntersection"

'''
Force Maya to only consider and pass API version 2.0 (maya.api.OpenMaya*) objects
'''
def maya_useNewAPI():
    return True

class ScreenSpaceContext(omui.MPxContext):

    TITLE = "ScreenSpaceContext"

    def __init__(self):
        super().__init__()
        self.setTitleString(ScreenSpaceContext.TITLE)

        self.mesh_list = mesh_list.MFnMeshList(self.get_meshes_in_scene())
        self.octree = octree.Octree(self.mesh_list, self.mesh_list.bbox, 3)
        self.bvh = bvh.BVH(self.mesh_list, self.mesh_list.bbox, max_depth=20)
        self.bvh.pprint(self.bvh.root)

    def get_meshes_in_scene(self) -> list:
        '''
        Return all mesh instances in a scene
        '''
        return cmds.ls(type="mesh")
    
    @timer.timer_decorator
    def check_meshes_is_stale(self):
        '''
        Checks if our list of mfn_meshes is stale and if so, recompute it
        '''
        scene_meshes = self.get_meshes_in_scene()
        if not self.mesh_list == scene_meshes:
            timer.ScopedTimer("Recalculating the MeshList and Octree")
            self.mesh_list = mesh_list.MFnMeshList(scene_meshes)
            self.octree = octree.Octree(self.mesh_list, self.mesh_list.bbox, 3)


    @timer.timer_decorator
    def doPress(self, event, draw_manager, frame_context):
        screen_space_pos = event.position
        ray = project_to_3d.project_to_3d(screen_space_pos)

        self.check_meshes_is_stale()

        # Find the closest intersection for the mesh list
        result = project_to_3d.get_closest_intersection_octree(self.octree, self.mesh_list, ray)
        if result:
            om.MGlobal.displayInfo(f"Found intersection for mesh {result[0]} at [{result[1][0], result[1][1], result[1][2]}]")
        result = project_to_3d.get_closest_intersection_bvh(self.bvh, self.mesh_list, ray)
        if result:
            om.MGlobal.displayInfo(f"Found intersection for mesh {result[0]} at [{result[1][0], result[1][1], result[1][2]}]")
        


class ScreenSpaceContextCommand(omui.MPxContextCommand):

    COMMAND_NAME = "ScreenSpaceSelectCtx"

    def __init__(self):
        super().__init__()

    def makeObj(self):
        return ScreenSpaceContext()
    
    @classmethod
    def creator(cls):
        return ScreenSpaceContextCommand()