import maya.api.OpenMaya as om

import GetClosestIntersection.constants as constants

from GetClosestIntersection.core.acceleration_structures.base import AccelerationStructure
import GetClosestIntersection.core.ray as ray

import GetClosestIntersection.util.maya.meshlist as meshlist
import GetClosestIntersection.util.timer as timer
import GetClosestIntersection.util.priority_set as priority_set
import GetClosestIntersection.util.debug as debug

class BVHNode:
    def __init__(self, bbox, indices = None, left = None, right = None):
        self.bbox: om.MBoundingBox = bbox
        self.indices: list[int] = indices
        self.left: BVHNode = left
        self.right: BVHNode = right

class BVH(AccelerationStructure):
    
    @timer.timer_decorator
    def __init__(self, meshlist: meshlist.MFnMeshList, bbox: om.MBoundingBox, max_depth = 32, sample_count = 32):
        if max_depth < 1:
            om.MGlobal.displayError(f"{self.__init__.__qualname__} max_depth parameter must be greater than 0")
        if sample_count < 1:
            om.MGlobal.displayError(f"{self.__init__.__qualname__} sample_count parameter must be greater than 0")
        self.meshlist = meshlist
        self._sample_count = sample_count
        self._max_depth = max_depth
        self._depth = 0
        self.root = self._recursive_build(meshlist, list(range(len(meshlist.mfn_meshes))), bbox, max_depth)

    def _find_longest_axis(self, bbox: om.MBoundingBox) -> int:
        '''
        Find the longest axis of a bounding box and return its index in 3d-space. I.e, return values range from 0-2
        '''
        axis_lengths = [bbox.max[0] - bbox.min[0], bbox.max[1] - bbox.min[1], bbox.max[2] - bbox.min[2]]
        longest_axis = axis_lengths.index(max(axis_lengths))
        return longest_axis

    def _recursive_build(self, meshlist: meshlist.MFnMeshList, indices: set, bbox: om.MBoundingBox, depth: int) -> BVHNode:
        '''
        Recursively build and fill the BVH using a median split along the provided indices. It works by finding the longest axis of the 
        input bbox and then sorting the indices set based on their positions along that axis, splitting across the median. 

        :returns: The node with the filled left and right children split across the median.
        :rtype: BVHNode
        '''
        # End calculations early if the node will contain less than 4 indices as further splitting would not necesarily increase performance
        # This is an arbitrary limit and can be played with
        if depth == 0 or len(indices) <= 4:
            if depth > self._depth:
                self._depth = depth
            return BVHNode(bbox, indices)

        longest_axis = self._find_longest_axis(bbox)
        positions = []
        # Expand the input bbox to match the items and store the positions of the other bboxes at the longest axis
        for index in indices:
            mesh_bbox = meshlist.get_bbox_at_index(index)
            positions.append(mesh_bbox.min[longest_axis] + mesh_bbox.max[longest_axis])

        sorted_indices = [x for _, x in sorted(zip(positions, indices))]   # Re-sort indices based on their positions
        midpoint = len(sorted_indices) // 2

        # Start from an empty bounding box and expand it until all the children fit into it
        left_indices = sorted_indices[:midpoint]
        left_bbox = om.MBoundingBox()
        for index in left_indices:
            mesh_bbox = meshlist.get_bbox_at_index(index)
            left_bbox.expand(mesh_bbox)

        # Start from an empty bounding box and expand it until all the children fit into it
        right_indices = sorted_indices[midpoint:]
        right_bbox = om.MBoundingBox()
        for index in right_indices:
            mesh_bbox = meshlist.get_bbox_at_index(index)
            right_bbox.expand(mesh_bbox)

        left_node = self._recursive_build(meshlist, left_indices, left_bbox, depth -1)
        right_node = self._recursive_build(meshlist, right_indices, right_bbox, depth -1)

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

    def find_intersections(self, node: BVHNode, heap: priority_set.PrioritySet, meshlist: meshlist.MFnMeshList, ray: ray.Ray, depth = 0) -> priority_set.PrioritySet:
        '''
        Recursively find intersections and store them in an ordered heap such that intersections get ordered by minimal distance
        '''
        if not ray.intersect_bbox(node.bbox):
            return heap
        
        if constants.DEBUG and self._depth > 0:
            # Create a debug cube that gets progressively darker as we progress through the tree depths
            debug.create_cube("bvhDebugCube", node.bbox, color=(float((self._depth - depth)) / float(self._depth), 0, 0), group="BVH")

        if node.indices:
            distance = ray.origin.distanceTo(node.bbox.center)
            for index in node.indices:
                heap.add(index, -distance)

        if node.left:
            self.find_intersections(node.left, heap, meshlist, ray, depth+1)
        if node.right:
            self.find_intersections(node.right, heap, meshlist, ray, depth+1)

    @timer.timer_decorator
    def get_closest_intersection(self, meshes: meshlist.MFnMeshList, ray:ray.Ray):
        '''
        Get the closest intersection point for a given ray in a list of meshes

        :param bvh: The Bounding Volume Hierarchy to be used for the acceleration of mesh collision checks
        :param meshes: the meshlist of the whole scene to iterate over
        :param ray: The ray to cast the intersection from

        :return: The mesh name the intersection was found for and the hit position or None
        '''
        indices_heap = priority_set.PrioritySet()
        self.find_intersections(self.root, indices_heap, meshes, ray)
        ray.create_debug_visualizer(scale=1000)

        # Convert to MFloatPoint ahead of time to avoid doing it for every mesh iteration
        ray_origin = om.MFloatPoint(ray.origin)
        ray_direction = om.MFloatVector(ray.direction)

        max_param = 9999999
        intersection_count = 0

        distances_stack = {}    # Key: Dist ; Value: index
        intersection_stack = {} # Key: index ; Value: intersection_point

        while(indices_heap.heap):
            index = indices_heap.pop()
            mesh = meshes.mfn_meshes[index]
            intersection_point = mesh.closestIntersection(ray_origin,                           # raySource
                                                        ray_direction,                        # rayDirection
                                                        om.MSpace.kWorld,                     # space
                                                        max_param,                            # maxParam
                                                        False)                                # testBothDirections

            if intersection_point:
                intersection_count = intersection_count + 1
                distances_stack[ray_origin.distanceTo(intersection_point[0])] = index
                intersection_stack[index] = intersection_point[0]
            
            # Break early if we reach maximum samples
            if intersection_count == self._sample_count:
                min_index = distances_stack[min(distances_stack.keys())]
                return (meshes.get_name_at_index(min_index), intersection_stack[min_index])
        
        # Find the closest intersection from our stack and return it
        if len(distances_stack) > 0:
                min_index = distances_stack[min(distances_stack.keys())]
                return (meshes.get_name_at_index(min_index), intersection_stack[min_index])

        # No intersection handling
        om.MGlobal.displayWarning(f"No intersection found for ray [{ray}]")
        return None