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
    # and pairing them with their children
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

            if children is not None and i == jointIndex and positions[0] == 0.:
                joints.append([[nextJoint, children[0]], [positions[0]]])

            break
        
        joints.append([[nextJoint, children[0]], positions])
    
    for jointInfo in joints:

        parentJoint = jointInfo[0][0]
        childJoint = jointInfo[0][1]
        positions = jointInfo[1]
        helpers.createJointsBetweenJoints(parentJoint, childJoint, positions, "_twist", current_suffix)
    
    cmds.select(initialSelection)

def set_rotate_order(order):
    """
    Sets rotation order of selected joints and all their descendant joints.

    Params:

        order (str or int): The desired rotation order to apply to the selected joints.  If string, must be one of the 
                            available orders ('xyz', 'yzx', etc).  If int, must be the index of one of the available orders (0-5). 
    """

    availableOrders = {'xyz':0,'yzx':1,'zxy':2,'xzy':3,'yxz':4,'zyx':5}
    if isinstance(order, str) and order.lower() in availableOrders:
        index = availableOrders[order.lower()]
    elif isinstance(order, int) and order >= 0 and order <= 5:
        index = order
    else:
        cmds.error("Invalid order")

    selectedJoints = cmds.ls(sl=True, type='joint', l=True)

    all = selectedJoints[:]

    for j in selectedJoints:
        
        descendants = cmds.listRelatives(j, type='joint', f=True, ad=True)
        if descendants is not None:
            all.extend(descendants)
    
    for j in all:

        cmds.setAttr(j + '.rotateOrder', index)