'''
Maya Plug-In entry point, the initializePlugin and uninitializePlugin functions are required
for maya to register your plugin
'''

import maya.api.OpenMaya as om

import GetClosestIntersection.context.closest_intersection_ctx as closest_intersection_ctx

'''
Force Maya to only consider and pass API version 2.0 (maya.api.OpenMaya*) objects
'''
def maya_useNewAPI():
    return True


def initializePlugin(mobject: om.MObject):
    mplugin = om.MFnPlugin(mobject, "EmilDohne", "1.0", "Any")
    try:
        mplugin.registerContextCommand(closest_intersection_ctx.ClosestIntersectionContextCommand.COMMAND_NAME, closest_intersection_ctx.ClosestIntersectionContextCommand.creator)
    except Exception as e:
        om.MGlobal.displayError(f"Unable to register '{closest_intersection_ctx.ClosestIntersectionContextCommand.COMMAND_NAME}' command")
        raise(e)


def uninitializePlugin(mobject: om.MObject):
    mplugin = om.MFnPlugin(mobject)
    try:
        mplugin.deregisterContextCommand(closest_intersection_ctx.ClosestIntersectionContextCommand.COMMAND_NAME)
    except Exception as e:
        om.MGlobal.displayError(f"Unable to deregister '{closest_intersection_ctx.ClosestIntersectionContextCommand.COMMAND_NAME}' command")
        raise(e)