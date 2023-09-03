'''
Wrappper class for a maya Locator to simplify creation and modification while keeping a more 
pythonic structure. 

If one would expect the locator to be modified externally, a better way would be to keep track of it as a
om.MFnDependencyNode such that we have the attached function set and not just a reference to a name.
'''
import maya.api.OpenMaya as om
import maya.cmds as cmds


class Locator:

    def __init__(self, name: str, position: om.MPoint, scale: int = 10):
        self._name = cmds.spaceLocator(absolute = True,
                                       n = name)[0]
        cmds.scale(scale, scale, scale, self._name)
        cmds.move(position[0], position[1], position[2], self._name)
        self._position = position

    @property 
    def name(self):
        return self._name
    
    @property
    def position(self):
        return self._position
    
    def move(self, new_pos: om.MPoint, is_relative: bool = False):
        '''
        Transform the locator object to a new position, if is_relative perform the operation 
        relative to the objects current position
        '''
        if not is_relative:
            cmds.move(new_pos[0], new_pos[1], new_pos[2], self.name, absolute = True)
        else:
            cmds.move(new_pos[0], new_pos[1], new_pos[2], self.name, relative = True)

    def rename(self, new_name: str):
        self._name = cmds.rename(self._name, new_name)