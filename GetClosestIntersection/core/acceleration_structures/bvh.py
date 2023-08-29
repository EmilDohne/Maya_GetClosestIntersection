import maya.api.OpenMaya as om

import core.ray as ray

import util.mesh_list as mesh_list
import util.timer as timer
import util.priority_set as priority_set
import util.debug as debug

class BVHNode:
    def __init__(self, bbox, indices = None, left = None, right = None):
        self.bbox: om.MBoundingBox = bbox
        self.indices: list[int] = indices
        self.left: BVHNode = left
        self.right: BVHNode = right

class BVH:
    
    @timer.timer_decorator
    def __init__(self, mesh_list: mesh_list.MFnMeshList, bbox: om.MBoundingBox, max_depth=3):
        self.mesh_list = mesh_list
        # self.root = self._recursive_build(mesh_list, list(range(len(mesh_list.mfn_meshes))), bbox, max_depth)
        self.root = self._recursive_build(mesh_list, list(range(len(mesh_list.mfn_meshes))), bbox, max_depth)

    def _find_longest_axis(self, bbox: om.MBoundingBox):
        axis_lengths = [bbox.max[0] - bbox.min[0], bbox.max[1] - bbox.min[1], bbox.max[2] - bbox.min[2]]
        longest_axis = axis_lengths.index(max(axis_lengths))
        return longest_axis

    def _recursive_build(self, mesh_list: mesh_list.MFnMeshList, indices: set, bbox: om.MBoundingBox, depth: int) -> BVHNode:
        '''
        Recursively build and fill the BVH using a median split along the provided indices
        '''
        if depth == 0 or len(indices) <= 4:
            return BVHNode(bbox, indices)

        longest_axis = self._find_longest_axis(bbox)
        positions = []
        # Expand the input bbox to match the items and store the positions of the other bboxes at the longest axis
        for index in indices:
            mesh_bbox = mesh_list.get_bbox_at_index(index)
            positions.append(mesh_bbox.min[longest_axis] + mesh_bbox.max[longest_axis])

        sorted_indices = [x for _, x in sorted(zip(positions, indices))]   # Re-sort indices based on their positions
        midpoint = len(sorted_indices) // 2

        # Start from an empty bounding box and expand it until all the children fit into it
        left_indices = sorted_indices[:midpoint]
        left_bbox = om.MBoundingBox()
        for index in left_indices:
            mesh_bbox = mesh_list.get_bbox_at_index(index)
            left_bbox.expand(mesh_bbox)

        # Start from an empty bounding box and expand it until all the children fit into it
        right_indices = sorted_indices[midpoint:]
        right_bbox = om.MBoundingBox()
        for index in right_indices:
            mesh_bbox = mesh_list.get_bbox_at_index(index)
            right_bbox.expand(mesh_bbox)

        left_node = self._recursive_build(mesh_list, left_indices, left_bbox, depth -1)
        right_node = self._recursive_build(mesh_list, right_indices, right_bbox, depth -1)

        return BVHNode(bbox, left=left_node, right=right_node)

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
        
        debug.create_cube("bvhDebugCube", node.bbox, color=(1, 0, 0), group="BVH")

        if node.indices:
            distance = ray.origin.distanceTo(node.bbox.center)
            for index in node.indices:
                heap.add(index, -distance)

        if node.left:
            self.find_intersections(node.left, heap, mesh_list, ray)
        if node.right:
            self.find_intersections(node.right, heap, mesh_list, ray)