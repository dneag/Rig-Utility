import maya.cmds as cmds

from . import rig_utility_helpers as helpers

def create_twist_joints(indices: list, *, current_suffix: str = None):
    """
    Create twist joints along a selected joint chain.

    Params:

        indices (list): Integer indices, 0-based relative to the selected joint, indicating joints on which to add twist joint(s) as children.
                        Elements can also be lists, with their first element being the integer index, and following elements floats or ints
                        indicating the position of the new joint(s) as a % of the distance from parent to child.  The default position is 50%.
        
        current_suffix (str):   An existing suffix on the name of the selected joint.  This allows us to insert the text '_twist' before any
                                specified suffix.  If not specified, '_twist' is inserted before the first '_' from the back.  If there is 
                                no '_', '_twist' becomes the suffix.

    Returns: None
    
    Example:

        create_twist_joints([[0,0,.5], 1])

        This will create 3 joints.  One directly on the selected joint (0%), one 50% between it and its child, and one 50% between child
        and grandchild.
    """

    indexMap = helpers.prepareIndexList(indices)
    
    initialSelection = nextJoint = cmds.ls(sl=True)

    if len(nextJoint) != 1 or cmds.objectType(nextJoint[0]) != 'joint':
        cmds.error("Select a single joint.")
    
    # Before modifying the skeleton, move the info from indexMap to a regular list, converting the indices to the actual joint names
    # paired with their children
    joints = []
    i = 0
    for jointIndex, positions in indexMap.items():

        # Get descendants of the selected joint until the index matches or the chain ends or branches
        while i != jointIndex:

            parentJoint = nextJoint
            nextJoint = cmds.listRelatives(parentJoint, c=True)

            if nextJoint is None or len(nextJoint) != 1:

                nextJoint = parentJoint # This will cause a break from the outer loop as well
                break

            i += 1

        nextJoint = nextJoint[0]
        children = cmds.listRelatives(nextJoint, c=True)

        # Terminate if the limb ends or branches
        if children is None or len(children) != 1:
            break
        
        joints.append([[nextJoint, children[0]], positions])
    
    for jointInfo in joints:

        parentJoint = jointInfo[0][0]
        childJoint = jointInfo[0][1]
        positions = jointInfo[1]
        twistJointBaseName = helpers.insertTextInName(parentJoint, "_twist", current_suffix)
        helpers.createJointsBetweenJoints(twistJointBaseName, parentJoint, childJoint, positions)
    
    cmds.select(initialSelection)
