# -*- coding: utf-8 -*-
"""Basic scene using Cosserat in SofaPython3.

Based on the work done with SofaPython. See POEMapping.py
"""

from params import NeedleParameters
from cosserat.usefulFunctions import pluginList
from cosserat.createFemRegularGrid import createFemCubeWithParams
from cosserat.cosseratObject import Cosserat
from cosserat.utils import addConstraintPoint
import sys
params = NeedleParameters()

sys.path.append('../')
from cosserat.needle.needleController import Animation
nbFrames = params.Geometry.nbFrames
needleGeometryConfig = {'init_pos': [0., 0., 0.], 'tot_length': params.Geometry.totalLength,
                        'nbSectionS': params.Geometry.nbSections, 'nbFramesF': nbFrames,
                        'buildCollisionModel': 1, 'beamMass': params.Physics.mass}


def createScene(rootNode):
    rootNode.addObject(
        'RequiredPlugin', pluginName=pluginList, printLog='0')

    rootNode.addObject('VisualStyle', displayFlags='showVisualModels showBehaviorModels hideCollisionModels '
                                                   'hideBoundingCollisionModels hireForceFields '
                                                   'hideInteractionForceFields hideWireframe showMechanicalMappings')
    rootNode.addObject('DefaultPipeline')
    rootNode.addObject("DefaultVisualManagerLoop")
    rootNode.addObject('RuleBasedContactManager',
                       responseParams='mu=0.1', response='FrictionContactConstraint')
    rootNode.addObject('BruteForceBroadPhase')
    rootNode.addObject('BVHNarrowPhase')
    # rootNode.addObject('LocalMinDistance', alarmDistance=1.0, contactDistance=0.01)
    rootNode.addObject('LocalMinDistance', name="Proximity", alarmDistance=0.5,
                       contactDistance=params.contact.contactDistance,
                       coneFactor=params.contact.coneFactor, angleCone=0.1)

    rootNode.addObject('FreeMotionAnimationLoop')
    generic = rootNode.addObject('GenericConstraintSolver', tolerance="1e-20",
                                 maxIterations="500", computeConstraintForces=1, printLog="0")

    gravity = [0, 0, 0]
    rootNode.gravity.value = gravity
    rootNode.addObject('BackgroundSetting', color='0 0.168627 0.211765')
    # rootNode.addObject('OglSceneFrame', style="Arrows", alignment="TopRight")
    # ###############
    # New adds to use the sliding Actuator
    ###############
    solverNode = rootNode.addChild('solverNode')
    solverNode.addObject('EulerImplicitSolver',
                         rayleighStiffness=params.Physics.rayleighStiffness)
    solverNode.addObject('SparseLDLSolver', name='solver',
                         template="CompressedRowSparseMatrixd")
    solverNode.addObject('GenericConstraintCorrection')

    needle = solverNode.addChild(
        Cosserat(parent=solverNode, cosseratGeometry=needleGeometryConfig, radius=params.Geometry.radius,
                 name="needle", youngModulus=params.Physics.youngModulus, poissonRatio=params.Physics.poissonRatio,
                 rayleighStiffness=params.Physics.rayleighStiffness))
    needleCollisionModel = needle.addPointCollisionModel("needleCollision")

    # These state is mapped on the needle and used to compute the distance between the needle and the
    # FEM constraint points
    slidingPoint = needle.addSlidingPoints()

    # -----------------
    # Start the volume definition 
    # -----------------
    cubeNode = createFemCubeWithParams(rootNode, params.FemParams)
    gelNode = cubeNode.getChild('gelNode')
    # FEM constraint points
    constraintPointNode = addConstraintPoint(gelNode, slidingPoint.getLinkPath())

    # @info : This is the constraint point that will be used to compute the distance between the needle and the volume
    conttactL = rootNode.addObject('ContactListener', name="contactListener",
                                   collisionModel1=cubeNode.gelNode.surfaceNode.surface.getLinkPath(),
                                   collisionModel2=needleCollisionModel.collisionStats.getLinkPath())

    # -----------------
    # @info: Start controller node
    rootNode.addObject(Animation(needle,
                                 conttactL, generic, constraintPointNode, rootNode))
    # rootNode.addObject(Animation(needle.rigidBaseNode.RigidBaseMO, needle.cosseratCoordinateNode.cosseratCoordinateMO,
    #                              conttactL, generic, needleCollisionModel, constraintPointNode, rootNode))

    # These stats will represents the distance between the contraint point in the volume and
    # their projection on the needle
    # It 's also important to say that the x direction is not taken into account
    distanceStatsNode = slidingPoint.addChild('distanceStatsNode')
    constraintPointNode.addChild(distanceStatsNode)
    distanceStatsNode.addObject('MechanicalObject', name="distanceStats", template="Vec3d",
                                                position=[])

    inputVolumeMo = constraintPointNode.constraintPointsMo.getLinkPath()
    inputNeedleMo = slidingPoint.slidingPointMO.getLinkPath()
    outputDistanceMo = distanceStatsNode.distanceStats.getLinkPath()
    # distanceStatsNode.addObject('CosseratNeedleSlidingConstraint', name="computeDistanceComponent")
    # distanceStatsNode.addObject('DifferenceMultiMapping', name="pointsMulti", input1=inputVolumeMo, lastPointIsFixed=0,
    #                            input2=inputNeedleMo, output=outputDistanceMo, direction="@../../FramesMO.position")
