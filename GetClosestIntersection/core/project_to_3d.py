import maya.api.OpenMaya as om
import maya.api.OpenMayaUI as omui

import heapq

import core.ray as ray
import core.octree as octree
import core.bvh as bvh
import util.mesh_list as mesh_list
import util.timer as timer
import util.priority_set as priority_set


@timer.timer_decorator
def project_to_3d(screen_space_coords) -> ray.Ray:
    '''
    Project a 2d screen space coordinate to a 3d Ray in the format {origin, direction}

    :returns: the projected ray
    :rtype: ray.Ray()
    '''
    projection_ray = ray.Ray()

    active_3d_view = omui.M3dView.active3dView()
    # The projection ray gets modified in-place by the viewToWorld function, similar to if you would pass by reference in c++
    active_3d_view.viewToWorld(
        screen_space_coords[0],
        screen_space_coords[1],
        projection_ray.origin,  
        projection_ray.direction
    )
    return projection_ray


@timer.timer_decorator
def get_closest_intersection(meshes: mesh_list.MFnMeshList, ray: ray.Ray):
    '''
    Get the closest intersection point for a given ray in a list of meshes

    :return: The mesh name the intersection was found for and the hit position or None
    '''

    # Convert to MFloatPoint ahead of time to avoid doing it for every mesh iteration
    ray_origin = om.MFloatPoint(ray.origin)
    ray_direction = om.MFloatVector(ray.direction)

    intersection_list = []
    distances_list = []
    max_param = 9999999

    for i, mesh in enumerate(meshes.mfn_meshes):
        intersection_point = mesh.closestIntersection(ray_origin,                           # raySource
                                                      ray_direction,                        # rayDirection
                                                      om.MSpace.kWorld,                     # space
                                                      max_param,                            # maxParam
                                                      False)                                # testBothDirections
        intersection_list.append(intersection_point)

        if intersection_list[i]:
            distances_list.append(ray_origin.distanceTo(intersection_point[0]))
        else:
            distances_list.append(max_param+1)

    if len(distances_list) > 0:
        min_index = min(range(len(distances_list)), key=distances_list.__getitem__)             # Get the lowest distance index
    else:
        om.MGlobal.displayWarning(f"No intersection found for ray [{ray}]")
        return None

    # Check for no intersection
    if distances_list[min_index] == max_param+1:
        om.MGlobal.displayWarning(f"No intersection found for ray [{ray}]")
        return None
    else:
        return (meshes.get_name_at_index(min_index), intersection_list[min_index][0])


@timer.timer_decorator
def get_closest_intersection_octree(octree: octree.Octree, meshes: mesh_list.MFnMeshList, ray:ray.Ray):
    '''
    Get the closest intersection point for a given ray in a list of meshes, using an octree to accelerate collision checks

    :return: The mesh name the intersection was found for and the hit position or None
    '''
    indices = set()
    octree.find_intersections(octree.grid, indices, ray)      # Modify indices set in place

    # Convert to MFloatPoint ahead of time to avoid doing it for every mesh iteration
    ray_origin = om.MFloatPoint(ray.origin)
    ray_direction = om.MFloatVector(ray.direction)

    intersections = {}
    distances = {}
    max_param = 9999999

    for index in indices:
        mesh = meshes.mfn_meshes[index]
        intersection_point = mesh.closestIntersection(ray_origin,                           # raySource
                                                      ray_direction,                        # rayDirection
                                                      om.MSpace.kWorld,                     # space
                                                      max_param,                            # maxParam
                                                      False)                                # testBothDirections
        if intersection_point:
            distances[index] = ray_origin.distanceTo(intersection_point[0])
            intersections[index] = (intersection_point[0])

    if len(distances) > 0:
        min_index = min(distances, key=distances.get)   # Get the lowest distance index
    else:
        om.MGlobal.displayWarning(f"No intersection found for ray [{ray}]")
        return None

    return (meshes.get_name_at_index(min_index), intersections[min_index])


@timer.timer_decorator
def get_closest_intersection_bvh(bvh: bvh.BVH, meshes: mesh_list.MFnMeshList, ray:ray.Ray, sample_count: int = 32):
    '''
    Get the closest intersection point for a given ray in a list of meshes, using bvh (Bounding Volume Hierarchy) to accelerate collision checks

    :return: The mesh name the intersection was found for and the hit position or None
    '''
    indices_heap = priority_set.PrioritySet()
    bvh.find_intersections(bvh.root, indices_heap, meshes, ray)
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
        
        if intersection_count == sample_count or intersection_count == len(indices_heap):
            min_index = distances_stack[min(distances_stack.keys())]
            return (meshes.get_name_at_index(min_index), intersection_stack[min_index])
        
    om.MGlobal.displayWarning(f"No intersection found for ray [{ray}]")
    return None
