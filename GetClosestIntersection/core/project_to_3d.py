import maya.api.OpenMaya as om
import maya.api.OpenMayaUI as omui

import GetClosestIntersection.core.ray as ray
import GetClosestIntersection.util.timer as timer


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

