import maya.api.OpenMaya as om

import core.ray as ray

import util.mesh_list as mesh_list
import util.timer as timer
import util.priority_set as priority_set
import util.debug as debug

class BVHNode:
    def __init__(self, bbox, indices = None):
        self.bbox: om.MBoundingBox = bbox
        self.indices: list[int] = indices
        self.left: BVHNode = None
        self.right: BVHNode = None

class BVH:
    
    @timer.timer_decorator
    def __init__(self, mesh_list: mesh_list.MFnMeshList, bbox: om.MBoundingBox, max_depth=3):
        self.mesh_list = mesh_list
        self.root = self._recursive_build(mesh_list, list(range(len(mesh_list.mfn_meshes))), bbox, max_depth)

    def _find_longest_axis(self, bbox: om.MBoundingBox):
        axis_lengths = [bbox.max[0] - bbox.min[0], bbox.max[1] - bbox.min[1], bbox.max[2] - bbox.min[2]]
        longest_axis = axis_lengths.index(max(axis_lengths))
        return longest_axis

    def _split(self, bbox: om.MBoundingBox):
        # Split the bbox into two halves along its longest axis
        xyzmin = bbox.min
        xyzmax = bbox.max
        xyzmed = (bbox.max + om.MVector(bbox.min)) / 2

        longest_axis_index = self._find_longest_axis(bbox)
        if longest_axis_index == 0:
            # Split along the x axis
            left_bbox = om.MBoundingBox(om.MPoint(xyzmin[0], xyzmin[1], xyzmin[2]), om.MPoint(xyzmed[0], xyzmax[1], xyzmax[2]))
            right_bbox = om.MBoundingBox(om.MPoint(xyzmed[0], xyzmin[1], xyzmin[2]), om.MPoint(xyzmax[0], xyzmax[1], xyzmax[2]))
        elif longest_axis_index == 1:
            # Split along the y axis
            left_bbox = om.MBoundingBox(om.MPoint(xyzmin[0], xyzmin[1], xyzmin[2]), om.MPoint(xyzmax[0], xyzmed[1], xyzmax[2]))
            right_bbox = om.MBoundingBox(om.MPoint(xyzmin[0], xyzmed[1], xyzmin[2]), om.MPoint(xyzmax[0], xyzmax[1], xyzmax[2]))
        else:
            # Split along the z axis
            left_bbox = om.MBoundingBox(om.MPoint(xyzmin[0], xyzmin[1], xyzmin[2]), om.MPoint(xyzmax[0], xyzmax[1], xyzmed[2]))
            right_bbox = om.MBoundingBox(om.MPoint(xyzmin[0], xyzmin[1], xyzmed[2]), om.MPoint(xyzmax[0], xyzmax[1], xyzmax[2]))

        return left_bbox, right_bbox

    def _build(self, mesh_list: mesh_list.MFnMeshList, indices: set, bboxes: list[om.MBoundingBox]):
        left_indices = []
        right_indices = []

        for index in indices:
            mesh_bbox = mesh_list.get_bbox_at_index(index)
            if bboxes[0].contains(mesh_bbox.center):
                left_indices.append(index)
            elif bboxes[1].contains(mesh_bbox.center):
                right_indices.append(index)
            else:
                # Decide where to assign the mesh based on some criterion
                # For example, assign to the side with the greater distance
                distance_left = mesh_bbox.center.distanceTo(bboxes[0].center)
                distance_right = mesh_bbox.center.distanceTo(bboxes[1].center)

                if distance_left > distance_right:
                    left_indices.append(index)
                else:
                    right_indices.append(index)
        
        left_bbox = bboxes[0]
        right_bbox = bboxes[1]

        for index in left_indices:
            mesh_bbox = mesh_list.get_bbox_at_index(index)
            left_bbox.expand(mesh_bbox)
        for index in right_indices:
            mesh_bbox = mesh_list.get_bbox_at_index(index)
            right_bbox.expand(mesh_bbox)

        return left_indices, left_bbox, right_indices, right_bbox

    def _recursive_build(self, mesh_list: mesh_list.MFnMeshList, indices: list, bbox: om.MBoundingBox, depth: int):
        if depth == 0 or len(indices) <= 4:
            return BVHNode(bbox, indices)
        
        node = BVHNode(bbox)    # Dont initialize indices except for the lowest level

        # Only split if more than one object inhibits the space
        split_bbox = self._split(bbox)
        left_indices, left_bbox, right_indices, right_bbox = self._build(mesh_list, indices, split_bbox)
        node.left = self._recursive_build(mesh_list, left_indices, left_bbox, depth - 1)
        node.right = self._recursive_build(mesh_list, right_indices, right_bbox, depth - 1)

        return node

    def pprint(self, node: BVHNode, depth = 0):
        '''
        Pretty print function to inspect the tree structure
        '''
        tabs = "\t"*depth
        print(f"{tabs}Node_{depth} with Bbox{{ {node.bbox.min}, {node.bbox.max} }} has indices : {node.indices}")
        if node.left:
            self.pprint(node.left, depth+1)
        if node.right:
            self.pprint(node.right, depth+1)

    def find_intersections(self, node: BVHNode, heap: priority_set.PrioritySet, mesh_list: mesh_list.MFnMeshList, ray: ray.Ray) -> priority_set.PrioritySet:
        '''
        Recursively find intersections and store them in an ordered heap such that intersections get ordered by minimal distance
        '''
        if not ray.intersect_bbox(node.bbox):
            return heap
        
        debug.create_cube("bvhDebugCube", node.bbox, color=(1, 0, 0))

        if node.indices:
            distance = ray.origin.distanceTo(node.bbox.center)
            for index in node.indices:
                heap.add(index, -distance)

        if node.left:
            self.find_intersections(node.left, heap, mesh_list, ray)
        if node.right:
            self.find_intersections(node.right, heap, mesh_list, ray)