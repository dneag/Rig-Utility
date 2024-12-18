import maya.cmds as cmds
import numpy as np

# Validate, sort, and standardize the list of twist joint indices and their positioning along the skeleton
def prepareIndexList(jointIndices: list):

    if not isinstance(jointIndices, list):
        cmds.error("Joint indices must be specified in a list")
    
    indexMap = {}

    for t in jointIndices:

        valid = True

        if isinstance(t, int):
            
            if t not in indexMap:
                indexMap[t] = []

            indexMap[t].append(.5)

        elif isinstance(t, list) and isinstance(t[0], int):

            if t[0] not in indexMap:
                indexMap[t[0]] = []
            
            for v in t[1:]:

                if not isinstance(v, int) and not isinstance(v, float):

                    valid = False
                    break

                indexMap[t[0]].append(v)
        
        else:
            valid = False

        if not valid:
            cmds.error("list elements must be either integers or lists of [int, float, float, ...]")
    
    for v in indexMap.values():
        v.sort()

    return dict(sorted(indexMap.items()))

# Create joint(s) between pObj and cObj named as pObj with insertText inserted before currentSuffix.  The number of
# joints created is len(pos) and their positions correspond to pos values
def createJointsBetweenJoints(pObj: str, cObj: str, pos: list, insertText: str, currentSuffix: str):

    if currentSuffix is None:
        
        suffixIndex = pObj.rfind('_')
        currentSuffix = pObj[suffixIndex:] if suffixIndex != -1 else ''
    
    elif not pObj.endswith(currentSuffix):

        cmds.error("suffix '" + currentSuffix + "' not found")

    suffixIndex = pObj.rfind(currentSuffix)

    parentLocArray = cmds.xform(pObj, query=True, translation=True, worldSpace=True)
    childLocArray = cmds.xform(cObj, query=True, translation=True, worldSpace=True)
    parentLoc = np.array(parentLocArray)
    childLoc = np.array(childLocArray)
    pRadius = cmds.joint(pObj, q=True, rad=True)[0]

    for i in range(len(pos)):
        
        print("creating joint between " + pObj + " and " + cObj + " at " + str(int(pos[i] * 100)) + "% from " + pObj)
        loc = parentLoc + ((childLoc - parentLoc) * pos[i])
        t = insertText if len(pos) == 1 else insertText + str(i+1)
        jointName = pObj[:suffixIndex] + t + pObj[suffixIndex:]
        cmds.joint(n=jointName, p=loc, rad=pRadius)
        currentParent = cmds.listRelatives(jointName, parent=True)[0]
        if currentParent != pObj:
            cmds.parent(jointName,pObj)

def validateArgsForCleanOpp(space, axis, axes, center_threshold, neg_suffix, pos_suffix, skin_cluster):

    if space.lower() != 'world' and space.lower() != 'object':
        cmds.error("First argument must be 'world' or 'object'")
    elif axis.lower() not in axes:
        cmds.error("Second argument must specify 'x', 'y', or 'z'")

    mesh = cmds.ls(selection=True)[0] if cmds.ls(selection=True) else None
    if not mesh:
        cmds.error("Select a skinned mesh")
    
    if (neg_suffix and not pos_suffix) or (pos_suffix and not neg_suffix):
        cmds.error("If using a suffix, it must be specified for both negative and positive")

    if center_threshold < 0.:
        cmds.error("Center margin must be >= 0.")

    skin_clusters = cmds.ls(cmds.listHistory(mesh), type='skinCluster')
    if not skin_clusters:
        cmds.error("Select a skinned mesh")
    elif skin_cluster:
        if skin_cluster not in skin_clusters:
            cmds.error(skin_cluster + " not found in mesh history")
        else:
            skin_clusters = [skin_cluster]
    
    return mesh, skin_clusters

# Check that each suffix exists on at least one string in the list.
# Note that this assumes the strings will never end with more than one suffix 
def suffixesAreInStrings(suffixes: list, strings: list) -> bool:

    for s in strings:
        for sf in suffixes:
            if s.endswith(sf):
                suffixes.remove(sf)
                break
        if len(suffixes) == 0:
            break

    return len(suffixes) == 0