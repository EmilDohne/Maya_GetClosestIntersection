from abc import ABC, abstractmethod

import GetClosestIntersection.core.ray as ray
import GetClosestIntersection.util.maya.meshlist as meshlist

class AccelerationStructure(ABC):

    @abstractmethod
    def __init__(self, *args, **kwargs) -> None:
        super().__init__()

    @abstractmethod
    def find_intersections(self, *args, **kwargs) -> None:
        pass
    
    @abstractmethod
    def get_closest_intersection(self, meshes: meshlist.MFnMeshList, ray:ray.Ray) -> None:
        pass