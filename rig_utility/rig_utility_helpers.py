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

# Returns a new name with the text between the existing suffix and the rest of the current name of obj
def insertTextInName(obj: str, text: str, currentSuffix: str):

    if currentSuffix is None:
        
        suffixIndex = obj.rfind('_')
        currentSuffix = obj[suffixIndex:] if suffixIndex != -1 else ''
    
    elif not obj.endswith(currentSuffix):

        cmds.error("suffix '" + currentSuffix + "' not found")

    suffixIndex = obj.rfind(currentSuffix)

    return obj[:suffixIndex] + text + obj[suffixIndex:]

# Create joint(s) between pObj and cObj with the given name.  The number of joints created is len(pos) and their positions correspond to pos values
def createJointsBetweenJoints(name: str, pObj: str, cObj: str, pos: list):

    parentLocArray = cmds.xform(pObj, query=True, translation=True, worldSpace=True)
    childLocArray = cmds.xform(cObj, query=True, translation=True, worldSpace=True)
    parentLoc = np.array(parentLocArray)
    childLoc = np.array(childLocArray)
    pRadius = cmds.joint(pObj, q=True, rad=True)[0]

    for i in range(len(pos)):
        
        print("creating joint between " + pObj + " and " + cObj + " at " + str(int(pos[i] * 100)) + "% from " + pObj)
        loc = parentLoc + ((childLoc - parentLoc) * pos[i])
        jointName = name if len(pos) == 1 else (name + str(i+1))
        cmds.joint(n=jointName, p=loc, rad=pRadius)
        currentParent = cmds.listRelatives(jointName, parent=True)[0]
        if currentParent != pObj:
            cmds.parent(jointName,pObj)
