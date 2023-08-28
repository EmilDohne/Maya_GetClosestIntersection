import maya.api.OpenMaya as om
import maya.cmds as cmds

import core.ray as ray

import util.mesh_list as mesh_list
import util.timer as timer
import util.debug as debug


class Octree():
    '''
    Bounding Box Based Octree to accelerate the computation of closest intersections
    '''

    @timer.timer_decorator
    def __init__(self, mesh_list: mesh_list.MFnMeshList, bbox = om.MBoundingBox(om.MPoint(-1, -1, -1), om.MPoint(1, 1, 1)), depth = 2):
        indices = [i for i in range(len(mesh_list.mfn_meshes))]
        self.grid = self._recursive_build(mesh_list, indices, bbox, depth)
        self.max_depth = depth
      
    def _does_overlap(self, mesh: om.MFnMesh, dagpath: om.MDagPath, bbox: om.MBoundingBox):
        # MFnMesh.boundingBox returns the local space bbox, we need to multiply it by the inclusive matrix
        # (the matrix of all transforms above the MFnMesh, excluding itself)
        transformed_bbox_min = mesh.boundingBox.min * dagpath.inclusiveMatrix()
        transformed_bbox_max = mesh.boundingBox.max * dagpath.inclusiveMatrix()
        transformed_bbox = om.MBoundingBox(transformed_bbox_min, transformed_bbox_max)
        if bbox.intersects(transformed_bbox):
            return True
        return False

    def _split(self, bbox: om.MBoundingBox) -> dict[om.MBoundingBox]:
        '''
        Split a given bbox into 8 equal parts and return those parts, adapted from: https://codereview.stackexchange.com/questions/126521/python-octree-implementation
        '''
        xyzmin = bbox.min
        xyzmax = bbox.max
        xyzmed = (bbox.max + om.MVector(bbox.min)) / 2
        nodes = {
            om.MBoundingBox(om.MPoint(xyzmin[0], xyzmin[1], xyzmin[2]), om.MPoint(xyzmed[0], xyzmed[1], xyzmed[2])) : {},
            om.MBoundingBox(om.MPoint(xyzmin[0], xyzmed[1], xyzmin[2]), om.MPoint(xyzmed[0], xyzmax[1], xyzmed[2])) : {},
            om.MBoundingBox(om.MPoint(xyzmed[0], xyzmed[1], xyzmin[2]), om.MPoint(xyzmax[0], xyzmax[1], xyzmed[2])) : {},
            om.MBoundingBox(om.MPoint(xyzmed[0], xyzmin[1], xyzmin[2]), om.MPoint(xyzmax[0], xyzmed[1], xyzmed[2])) : {},
            om.MBoundingBox(om.MPoint(xyzmin[0], xyzmin[1], xyzmed[2]), om.MPoint(xyzmed[0], xyzmed[1], xyzmax[2])) : {},
            om.MBoundingBox(om.MPoint(xyzmin[0], xyzmed[1], xyzmed[2]), om.MPoint(xyzmed[0], xyzmax[1], xyzmax[2])) : {},
            om.MBoundingBox(om.MPoint(xyzmed[0], xyzmed[1], xyzmed[2]), om.MPoint(xyzmax[0], xyzmax[1], xyzmax[2])) : {},
            om.MBoundingBox(om.MPoint(xyzmed[0], xyzmin[1], xyzmed[2]), om.MPoint(xyzmax[0], xyzmed[1], xyzmax[2])) : {}, 
        }
        return nodes

    def _build(self, bbox: om.MBoundingBox, mesh_list: mesh_list.MFnMeshList, indices: list):
        index_list = []
        for index in indices:
            if self._does_overlap(mesh_list.mfn_meshes[index], mesh_list.mfn_dagpaths[index], bbox):
                index_list.append(index)
        return index_list

    def _recursive_build(self, mesh_list: mesh_list.MFnMeshList, indices : list, initial_bbox: om.MBoundingBox, depth: int) -> dict:
        '''
        Recursively build and fill the octree, only considering an already filtered list of indices to avoid iterating the full mesh_list
        8^n times in the worst case scenario.

        :param mesh_list: the original mesh list for the whole scene
        :param indices: the indices of the original mesh list to consider
        :param initial_bbox: the bounding box to split and fill
        :param depth: the current recursion depth, ranges from n-0
        '''
        depth = depth-1
        split_bbox = self._split(initial_bbox)
        keys_to_delete = []

        # Only fill the lowest depth with indices
        if depth == 0:
            for key in split_bbox:
                split_bbox[key] = self._build(key, mesh_list, indices)
                # Mark empty branches for deletion
                if len(split_bbox[key]) == 0:
                    keys_to_delete.append(key)
            # Delete empty branches
            for key in keys_to_delete:
                del split_bbox[key]
            return split_bbox
        
        # Recurse through the tree until depth == 0
        for bbox in split_bbox:
            # Calculate the indices to consider for the next iteration
            new_indices = []
            for index in indices:
                if self._does_overlap(mesh_list.mfn_meshes[index], mesh_list.mfn_dagpaths[index], bbox):
                    new_indices.append(index)
            # Filter out empty indices right away to avoid traversing to the deepest level
            if len(new_indices) == 0:
                keys_to_delete.append(bbox)
                continue
            split_bbox[bbox] = self._recursive_build(mesh_list, new_indices, bbox, depth)
        
        for key in keys_to_delete:
            del split_bbox[key]

        return split_bbox
   
    def find_intersections(self, my_dict: dict, indices: set, ray: ray.Ray):
        '''
        Recursively check the bounding boxes for intersections with the ray and modify in-place a set of the indices contained within that cube
        '''
        bbox = ray.closest_bbox(list(my_dict.keys()))
        
        if not bbox:
            return

        # Refine intersection check within all intersected bounding boxes
        intersected_bboxes = [b for b in my_dict.keys() if ray.intersect_bbox(b)]
        
        for bbox in intersected_bboxes:
            debug.create_cube("octreeDebugCube", bbox, color=(0, 0, 1))
            if isinstance(my_dict[bbox], list):
                for item in my_dict[bbox]:
                    indices.add(item)
            else:
                self.find_intersections(my_dict[bbox], indices, ray)
