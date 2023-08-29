import maya.api.OpenMaya as om
import maya.cmds as cmds

def create_cube(name: str, bbox: om.MBoundingBox, color: tuple[float] = (1, 1, 1), group = "Debug"):
    '''
    Create a singular cube from a bounding box for debugging purpose

    :param bbox: the bounding box to construct the cube from
    :param color: the color to shade the box, defaults to white
    '''
    if not cmds.objExists(group):
        group = cmds.group(em=True, n=group)

    min_point = bbox.min
    max_point = om.MVector(bbox.max)

    center = (min_point + max_point) / 2
    width = max_point.x - min_point.x
    height = max_point.y - min_point.y
    depth = max_point.z - min_point.z

    # Create the polyCube
    obj = cmds.polyCube(width=width, height=height, depth=depth, name=name)[0]
    cmds.move(center.x, center.y, center.z, obj)

    rgb = ("R","G","B")
    cmds.setAttr(obj + ".overrideEnabled", 1)
    cmds.setAttr(obj + ".overrideLevelOfDetail", 1)    # Set LOD to wireframe for easier viewing
    cmds.setAttr(obj + ".overrideRGBColors", 1)
    for channel, color in zip(rgb, color):
        cmds.setAttr(obj + ".overrideColor%s" %channel, color)

    cmds.parent(obj, group)