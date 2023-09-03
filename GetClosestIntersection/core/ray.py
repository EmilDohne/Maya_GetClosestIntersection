import maya.api.OpenMaya as om
import maya.cmds as cmds

import GetClosestIntersection.constants as constants

class Ray():
    
    def __init__(self, origin: list[float] = [0, 0, 0], direction: list[float] = [0, 0, 0]) -> None:
        assert len(origin) == 3
        assert len(direction) == 3
        self.origin = om.MPoint(origin[0], origin[1], origin[2])
        self.direction = om.MVector(direction[0], direction[1], direction[2])

    def __str__(self):
        precision = 3
        return f"Ray Origin: [{round(self.origin[0], precision)}, {round(self.origin[1], precision)}, {round(self.origin[2], precision)}] \
            | Ray Direction: [{round(self.direction[0], precision)}, {round(self.direction[1], precision)}, {round(self.direction[2], precision)}]"
 
    def create_debug_visualizer(self, scale: int = 10):
        '''
        Create a debug line to visualize the ray's path, only executes in constants.DEBUG is True

        :param scale: the overall length (in maya units) for the ray
        '''
        if constants.DEBUG:
            dir = self.origin + self.direction * scale
            cmds.curve(degree=1, p=[(self.origin[0], self.origin[1], self.origin[2]), (dir[0], dir[1], dir[2])], name="DebugRay")

    def intersect_bbox(self, bbox: om.MBoundingBox):
        tmin = (bbox.min - self.origin)
        tmin[0] = tmin[0] / self.direction[0]
        tmin[1] = tmin[1] / self.direction[1]
        tmin[2] = tmin[2] / self.direction[2]
        tmax = (bbox.max - self.origin)
        tmax[0] = tmax[0] / self.direction[0]
        tmax[1] = tmax[1] / self.direction[1]
        tmax[2] = tmax[2] / self.direction[2]
        
        t_enter = max(min(tmin.x, tmax.x), min(tmin.y, tmax.y), min(tmin.z, tmax.z))
        t_exit = min(max(tmin.x, tmax.x), max(tmin.y, tmax.y), max(tmin.z, tmax.z))
        
        if t_enter > t_exit or t_exit < 0:
            return False
        
        return True
    
    def closest_bbox(self, bbox_list: list[om.MBoundingBox]) -> om.MBoundingBox:
        min_distance = float('inf')
        closest_bbox = None

        for bbox in bbox_list:
            if self.intersect_bbox(bbox):  # First check if the ray intersects the bounding box
                # Calculate the distance from the ray's origin to the center of the bounding box
                distance = om.MVector(bbox.center - om.MVector(self.origin)).length()
                
                if distance < min_distance:
                    min_distance = distance
                    closest_bbox = bbox
    
        return closest_bbox