import maya.api.OpenMaya as om

import context.screen_space_context as screen_space_context

'''
Force Maya to only consider and pass API version 2.0 (maya.api.OpenMaya*) objects
'''
def maya_useNewAPI():
    return True


def initializePlugin(mobject: om.MObject):
    mplugin = om.MFnPlugin(mobject, "EmilDohne", "1.0", "Any")
    try:
        mplugin.registerContextCommand(screen_space_context.ClosestIntersectionContextCommand.COMMAND_NAME, screen_space_context.ClosestIntersectionContextCommand.creator)
    except Exception as e:
        om.MGlobal.displayError(f"Unable to register '{screen_space_context.ClosestIntersectionContextCommand.COMMAND_NAME}' command")
        raise(e)


def uninitializePlugin(mobject: om.MObject):
    mplugin = om.MFnPlugin(mobject)
    try:
        mplugin.deregisterContextCommand(screen_space_context.ClosestIntersectionContextCommand.COMMAND_NAME)
    except Exception as e:
        om.MGlobal.displayError(f"Unable to deregister '{screen_space_context.ClosestIntersectionContextCommand.COMMAND_NAME}' command")
        raise(e)