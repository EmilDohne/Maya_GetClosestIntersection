import maya.api.OpenMaya as om
import maya.api.OpenMayaUI as omui
import maya.cmds as cmds

import core.calculate_intersection as calculate_intersection
import core.acceleration_structures.octree as octree
import core.acceleration_structures.bvh as bvh
import util.mesh_list as mesh_list
import util.timer as timer

PLUG_IN_NAME = "CalculateClosestIntersection"

'''
Force Maya to only consider and pass API version 2.0 (maya.api.OpenMaya*) objects
'''
def maya_useNewAPI():
    return True

class ClosestIntersectionContext(omui.MPxContext):

    TITLE = "ClosestIntersectionCtx"

    def __init__(self):
        super().__init__()
        self.setTitleString(ClosestIntersectionContext.TITLE)

        # Initialize the acceleration structures and get the mesh list
        self.mesh_list = mesh_list.MFnMeshList(self.get_meshes_in_scene())
        self.bvh = bvh.BVH(self.mesh_list, self.mesh_list.bbox, max_depth=20)

    def get_meshes_in_scene(self) -> list:
        '''
        Return all mesh instances in a scene
        '''
        return cmds.ls(type="mesh")
    
    def check_meshes_is_stale(self):
        '''
        Checks if our list of mfn_meshes is stale and if so, recompute it.

        This does not check for animation! If your meshes move, please implement a function to check for it.
        '''
        scene_meshes = self.get_meshes_in_scene()
        if not self.mesh_list == scene_meshes:
            timer.ScopedTimer("Recalculating the MeshList and BVH")
            self.mesh_list = mesh_list.MFnMeshList(scene_meshes)
            self.bvh = bvh.BVH(self.mesh_list, self.mesh_list.bbox, max_depth=20)

    def doPress(self, event, draw_manager, frame_context):
        screen_space_pos = event.position
        ray = calculate_intersection.project_to_3d(screen_space_pos)

        self.check_meshes_is_stale()

        # Find the closest intersection for the mesh list using a BVH but can be modified to use an octree or brute-force
        result = calculate_intersection.get_closest_intersection_bvh(self.bvh, self.mesh_list, ray)
        if result:
            om.MGlobal.displayInfo(f"Found intersection for mesh {result[0]} at [{result[1][0], result[1][1], result[1][2]}]")
        


class ClosestIntersectionContextCommand(omui.MPxContextCommand):

    COMMAND_NAME = "ClosestIntersectionCommandCtx"

    def __init__(self):
        super().__init__()

    def makeObj(self):
        return ClosestIntersectionContext()
    
    @classmethod
    def creator(cls):
        return ClosestIntersectionContextCommand()