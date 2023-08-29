import maya.api.OpenMaya as om
import maya.cmds as cmds

import util.timer as timer


class MFnMeshList():
    '''
    A wrapper around a list of meshes which speeds up mesh operations by pre-computing 
    MFnMesh, MFnDagPath and Bounding Boxes for the given set
    '''

    @timer.timer_decorator
    def __init__(self, meshes: list[str]):
        if len(meshes) == 0:
            om.MGlobal.displayError("Unable to construct MFnMeshList without any input meshes")
            return
        self.mfn_meshes = []
        self.mfn_dagpaths = []
        self._mesh_list = []
        self._bbox_cache = [None] * len(meshes)

        selection_list = om.MSelectionList()
        for i, mesh in enumerate(meshes):
            selection_list.add(mesh)
            dag_path = selection_list.getDagPath(i)
            self.mfn_dagpaths.append(dag_path)
            try:
                MFnMesh = om.MFnMesh(dag_path)
                self.mfn_meshes.append(MFnMesh)
                self._mesh_list.append(mesh)
            except Exception:
                om.MGlobal.displayWarning(f"Unable to construct MFnMesh instance for '{mesh}'")

        _bbox = cmds.exactWorldBoundingBox(self._mesh_list)     # Use cmds in this case to avoid iterating the mesh_list to construct the bbox
        self.bbox = om.MBoundingBox(om.MPoint(_bbox[0], _bbox[1], _bbox[2]), om.MPoint(_bbox[3], _bbox[4], _bbox[5]))

    def get_bbox_at_index(self, index: int) -> om.MBoundingBox:
        '''
        Get the bbox at a specified index, if it already exists grab the cached result. Otherwise compute on the fly
        '''
        try:
            if self._bbox_cache[index]:
                return self._bbox_cache[index]
        except IndexError:
            om.MGlobal.displayInfo("Tried to access illegal index at MFnMeshList.get_bbox_at_index()")
        
        min = self.mfn_meshes[index].boundingBox.min * self.mfn_dagpaths[index].inclusiveMatrix()
        max = self.mfn_meshes[index].boundingBox.max * self.mfn_dagpaths[index].inclusiveMatrix()

        self._bbox_cache[index] = om.MBoundingBox(min, max)
        return self._bbox_cache[index]

    def get_name_at_index(self, index: int) -> str:
        '''
        Get the name of a mesh by its index

        :return: The name of the mesh or None
        '''
        try:
            return self._mesh_list[index]
        except IndexError:
            om.MGlobal.displayError("Invalid index provided to get_name_at_index()")
            return None

    def __len__(self) -> int:
        return len(self.mfn_meshes)

    def __eq__(self, other) -> bool:
        if isinstance(other, MFnMeshList):
            return self._mesh_list == other._mesh_list
        elif isinstance(other, list):
            return self._mesh_list == other
        else:
            om.MGlobal.displayError(f"Equality check only supported for types [MFnMeshList, list], not {type(other)}")