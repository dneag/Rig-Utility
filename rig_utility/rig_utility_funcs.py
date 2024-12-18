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

def clean_opposite_influences(space: str, axis: str, center_threshold: float = .01, skin_cluster: str = None,
                          neg_suffix: str = None, pos_suffix: str = None):
    """
    Examines the influences on each vertex on the selected mesh and sets them to 0 if they are found to be
    on the opposite side of the mesh from their influenced vertex.  By default, this applies to all skin clusters
    on the mesh.  If your mesh has multiple clusters and you only want to apply it to one, set the skin_cluster
    argument with the desired cluster name.  Also by default, joints' translations are used to determine which side
    of the axis they are on.  Alternitavely, you can provide suffixes to indicate sides, i.e., '_l' for pos_suffix
    and '_r' for neg_suffix.

    Params:

        Positional:

            space (str): Either 'world' or 'object'.  Indicates whether to consider the axis in world or object space

            axis (str): 'x', 'y', or 'z'.

        Optional:

            center_threshold (float): The range from 0 where vertices and influences will not be considered.

            skin_cluster (str): The skin cluster to adjust influences on.

            neg_suffix (str): The suffix of joints on the negative side of the axis to be considered

            pos_suffix (str): The suffix of joints on the positive side of the axis to be considered
    """

    axes = { 'x': 0, 'y': 1, 'z': 2 }
    mesh, skin_clusters = helpers.validateArgsForCleanOpp(space, axis, axes, center_threshold, neg_suffix, pos_suffix, skin_cluster)
    axis = axes[axis.lower()]
    ws = False if space == 'object' else True

    for sc in skin_clusters:

        influences = cmds.skinCluster(sc, query=True, influence=True)
        if neg_suffix:
            # Ensure that the suffixes exist on at least one influence
            if not helpers.suffixesAreInStrings([neg_suffix, pos_suffix], influences):
                cmds.error("One or both of the specified suffixes were not found on any influences")

        vertices = cmds.ls(f"{mesh}.vtx[*]", flatten=True)
        for v in vertices:

            vertexAxisValue = cmds.pointPosition(v, world=ws)[axis]
            if vertexAxisValue < center_threshold and vertexAxisValue > -center_threshold:
                continue
            vertexAxisValueIsPositive = cmds.pointPosition(v, world=ws)[axis] > 0.
            weights = cmds.skinPercent(sc, v, query=True, value=True)
            badInfluences = []

            for j, w in zip(influences, weights):
                if w > 0.:

                    if neg_suffix:
                        if ((j.endswith(neg_suffix) and vertexAxisValueIsPositive)
                            or (j.endswith(pos_suffix) and not vertexAxisValueIsPositive)):
                            badInfluences.append((j, 0.0))
                    else:
                        jointAxisValue = cmds.xform(j, query=True, worldSpace=ws, translation=True)[axis]
                        if ((jointAxisValue > center_threshold and not vertexAxisValueIsPositive)
                            or (jointAxisValue < -center_threshold and vertexAxisValueIsPositive)):
                            badInfluences.append((j, 0.0))
                    
            cmds.skinPercent(sc, v, tv=badInfluences)       