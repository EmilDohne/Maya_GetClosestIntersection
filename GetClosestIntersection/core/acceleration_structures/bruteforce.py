import maya.api.OpenMaya as om

from GetClosestIntersection.core.acceleration_structures.base import AccelerationStructure
import GetClosestIntersection.core.ray as ray

import GetClosestIntersection.util.maya.meshlist as meshlist
import GetClosestIntersection.util.timer as timer

class BruteForce(AccelerationStructure):
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def find_intersections(self, *args, **kwargs) -> None:
        raise NotImplementedError("BruteForce has no method for intersecting bounding boxes")

    @timer.timer_decorator
    def get_closest_intersection(self, meshes: meshlist.MFnMeshList, ray: ray.Ray):
        '''
        Brute-force approach of getting the mesh intersection point for a given ray by iterating all the meshes

        :param meshes: the meshlist of the whole scene to iterate over

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

