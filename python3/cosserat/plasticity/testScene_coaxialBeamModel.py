# -*- coding: utf-8 -*-
"""
Created on April 22 2022

@author: ckrewcun
"""

import Sofa
import os
import numpy as np
from CosseratNavigationController import CombinedInstrumentsController

# constants
GRAVITY = 0.0 # 9810
TOT_MASS = 0.1
DENSITY = 0.02
DT = 1e-2

# -------------------------------------#
# -----        SOFA scene        ----- #
# -------------------------------------#

pluginNameList = 'SofaPython3 CosseratPlugin' \
                 ' Sofa.Component.MechanicalLoad' \
                 ' Sofa.Component.ODESolver.Backward' \
                 ' Sofa.Component.SolidMechanics.Spring' \
                 ' Sofa.Component.StateContainer' \
                 ' Sofa.Component.Visual ' \
                 ' Sofa.Component.Constraint.Projective ' \
                 ' Sofa.Component.LinearSolver.Direct'
                 # ' Sofa.Component.LinearSolver.Iterative'

visualFlagList = 'showVisualModels showBehaviorModels showCollisionModels' \
                 ' hideBoundingCollisionModels hideForceFields' \
                 ' hideInteractionForceFields hideWireframe' \
                 ' showMechanicalMappings'

def createScene(rootNode):

    rootNode.addObject('RequiredPlugin', pluginName=pluginNameList, printLog='0')
    rootNode.addObject('VisualStyle', displayFlags=visualFlagList)

    rootNode.addObject('DefaultVisualManagerLoop')
    rootNode.findData('dt').value = DT
    rootNode.findData('gravity').value = [0., 0., -GRAVITY]

    rootNode.addObject('DefaultAnimationLoop')

    # -------------------------------------------------------------------- #
    # -----                   First beam parameters                  ----- #
    # -------------------------------------------------------------------- #

    # Define: the total length, number of beams, and number of frames
    totalLength = 15

    nbBeams = 4
    oneBeamLength = totalLength / nbBeams

    # nbFramesMax = 14
    # distBetweenFrames = totalLength / nbFrames
    nbFrames = 1

    # ----- Rigid base ----- #

    instrument0Node = rootNode.addChild('Instrument0')
    instrument0Node.addObject('EulerImplicitSolver', rayleighStiffness="1.2", rayleighMass='1.1')
    # instrument0Node.addObject('CGLinearSolver', name="solver",
    #                    iterations='100', tolerance='1e-5', threshold='1e-5')
    instrument0Node.addObject('SparseLUSolver',
                              template='CompressedRowSparseMatrixd',
                              printLog="false")

    rigidBaseNode0 = instrument0Node.addChild('rigidBase')
    RigidBaseMO = rigidBaseNode0.addObject('MechanicalObject', template='Rigid3d',
                                           name="RigidBaseMO", position=[0., 0., 0., 0, 0, 0, 1],
                                           showObject=True,
                                           showObjectScale=2.)
    rigidBaseNode0.addObject('RestShapeSpringsForceField', name='spring',
                             stiffness="5.e8", angularStiffness="5.e8",
                             external_points="0", mstate="@RigidBaseMO", points="0", template="Rigid3d")

    # ----- Rate of angular deformation ----- #
    # Define the length of each beam in a list, the positions of each beam

    beamStrainDoFs = []
    beamLengths = []
    sum = 0.
    beamCurvAbscissa = []
    beamCurvAbscissa.append(0.0)

    # EXPERIMENTAL: insertion navigation
    # Initially defining beams with 0 length, at 0
    # For each beam, we:
    #     - Add a Vec3 in beamStrainDoFs, with each strain component set at 0.
    #     - Add 0 in the length data field for the Cosserat mapping
    #     - Add the last curvilinear abscissa (total length) in the beams
    # curvilinear abcissas in the Cosserat mapping.
    # This is equivalent to saying that the beams are 0-length,
    # 0-strain beams, added at the beginning of the instrument.
    for i in range(0, nbBeams):
        beamStrainDoFs.append([0, 0, 0])
        beamLengths.append(0)
        beamCurvAbscissa.append(0)

    # for i in range(nbBeams):
    #     beamStrainDoFs.append([0, 0, 0])
    #     beamLengths.append(oneBeamLength)
    #     sum += beamLengths[i+nbStockBeams]
    #     beamCurvAbscissa.append(sum)
    # beamCurvAbscissa[nbBeams+nbStockBeams] = totalLength

    # Define angular rate which is the torsion(x) and bending (y, z) of each section
    rateAngularDeformNode0 = instrument0Node.addChild('rateAngularDeform0')
    rateAngularDeformMO = rateAngularDeformNode0.addObject('MechanicalObject',
                                                           template='Vec3d',
                                                           name='rateAngularDeformMO',
                                                           position=beamStrainDoFs,
                                                           showIndices=0,
                                                           rest_position=[0.0, 0.0, 0.0])

    beamCrossSectionShape='circular'
    sectionRadius = 0.5
    poissonRatio = 0.45
    beamPoissonRatioList = [poissonRatio]*(nbBeams)
    youngModulus = 5.0e6
    beamYoungModulusList = [youngModulus]*(nbBeams)
    yieldStress = 5.0e4
    yieldStressList = [yieldStress]*(nbBeams)
    plasticModulus = 2.0e5
    plasticModulusList = [plasticModulus]*(nbBeams)
    hardeningCoeff = 0.5
    hardeningCoefficientList = [hardeningCoeff]*(nbBeams)
    ### Plastic FF version
    rateAngularDeformNode0.addObject('BeamPlasticLawForceField', name="beamForceField",
                                     crossSectionShape=beamCrossSectionShape,
                                     radius=sectionRadius, variantSections="true",
                                     length=beamLengths, poissonRatioList=beamPoissonRatioList,
                                     youngModulusList=beamYoungModulusList,
                                     initialYieldStresses=yieldStressList,
                                     plasticModuli=plasticModulusList,
                                     mixedHardeningCoefficients= hardeningCoefficientList)
    ### Elastic FF version
    # rateAngularDeformNode.addObject('BeamHookeLawForceField', name="beamForceField",
    #                                 crossSectionShape=beamCrossSectionShape,
    #                                 radius=sectionRadius, variantSections="true",
    #                                 length=beamLengths, poissonRatioList=beamPoissonRatioList,
    #                                 youngModulusList=beamYoungModulusList)

    beamBendingMoment = 1.0e5
    bendingForces = np.array([0, beamBendingMoment, beamBendingMoment])
    # momentIndices = range(1, nbBeams)
    momentIndices = [nbBeams-1]
    # rateAngularDeformNode.addObject('ConstantForceField', name='Moment',
    #                                 indices=momentIndices,
    #                                 forces=bendingForces)

    # EXPERIMENTAL: navigation simulation
    # Adding constraints on the additional beams which are not meant to be
    # simulated at the beginning
    # fixedIndices = list(range(nbBeams, nbBeams+nbStockBeams))
    fixedIndices = list(range(0, nbBeams))
    rateAngularDeformNode0.addObject('FixedConstraint', name='FixedConstraint',
                                    indices=fixedIndices)

    # ----- Frames ----- #

    # Define local frames related to each section and parameters framesCurvAbscissa
    frames6DDoFs = []
    frames3DDoFs = []
    framesCurvAbscissa = []

    # for i in range(nbFrames):
    #     sol = i * distBetweenFrames
    #     frames3DDoFs.append([sol, 0, 0])
    #     frames6DDoFs.append([sol, 0, 0,  0, 0, 0, 1])
    #     framesCurvAbscissa.append(sol)
    #
    # frames6DDoFs.append([totalLength, 0, 0, 0, 0, 0, 1])
    # framesCurvAbscissa.append(totalLength)

    # EXPERIMENTAL: navigation simulation
    # At the beginning of the simulation, when no beam element is actually
    # simulated, all rigid frames are set at 0
    for i in range(nbFrames):
        frames3DDoFs.append([0, 0, 0])
        frames6DDoFs.append([0, 0, 0,  0, 0, 0, 1])
        framesCurvAbscissa.append(0)

    frames6DDoFs.append([0, 0, 0, 0, 0, 0, 1])
    framesCurvAbscissa.append(0)

    # The node of the frame needs to inherit from rigidBaseMO and rateAngularDeform
    mappedFrameNode = rigidBaseNode0.addChild('MappedFrames')
    rateAngularDeformNode0.addChild(mappedFrameNode)

    framesMO = mappedFrameNode.addObject('MechanicalObject', template='Rigid3d',
                                         name="FramesMO", position=frames6DDoFs,
                                         showObject=True, showObjectScale=1)

    # The mapping has two inputs: RigidBaseMO and rateAngularDeformMO
    #                 one output: FramesMO
    inputMO = rateAngularDeformMO.getLinkPath()
    inputMO_rigid = RigidBaseMO.getLinkPath()
    outputMO = framesMO.getLinkPath()

    mappedFrameNode.addObject('DiscreteCosseratMapping', curv_abs_input=beamCurvAbscissa,
                              curv_abs_output=framesCurvAbscissa, input1=inputMO, input2=inputMO_rigid,
                              output=outputMO, forcefield='@../../rateAngularDeform0/beamForceField',
                              drawBeamSegments=True, nonColored=False, debug=0, printLog=False)

    # mappedFrameNode.addObject('ConstantForceField', name='Moment',
    #                           indices=nbFrames-4,
    #                           forces=np.array([0, 0, 0, 0, 0, 8e4]))



    # -------------------------------------------------------------------- #
    # -----                  Second beam parameters                  ----- #
    # -------------------------------------------------------------------- #

    # # Define: the total length of the beam
    # totalLength = 20
    #
    # # Define: the number of section, the total length and the length of each beam.
    # nbBeams = 4
    # oneBeamLength = totalLength / nbBeams
    #
    # # Define: the number of frame and the length between each frame.
    # nbFrames = 12
    # distBetweenFrames = totalLength / nbFrames
    #
    # # ----- Rigid base ----- #
    #
    # instrument1Node = rootNode.addChild('Instrument1')
    # instrument1Node.addObject('EulerImplicitSolver', rayleighStiffness="1.2", rayleighMass='1.1')
    # # instrument1Node.addObject('CGLinearSolver', name="solver",
    # #                    iterations='100', tolerance='1e-5', threshold='1e-5')
    # instrument1Node.addObject('SparseLUSolver',
    #                            template='CompressedRowSparseMatrixd',
    #                            printLog="false")
    #
    # rigidBaseNode1= instrument1Node.addChild('rigidBase')
    # RigidBaseMO = rigidBaseNode1.addObject('MechanicalObject', template='Rigid3d',
    #                                       name="RigidBaseMO", position=[0., 0., 0., 0, 0, 0, 1],
    #                                       showObject=True,
    #                                       showObjectScale=2.)
    # rigidBaseNode1.addObject('RestShapeSpringsForceField', name='spring',
    #                          stiffness="5.e8", angularStiffness="5.e8",
    #                          external_points="0", mstate="@RigidBaseMO",
    #                          points="0", template="Rigid3d")
    #
    # # ----- Rate of angular deformation ----- #
    # # Define the length of each beam in a list, the positions of each beam
    #
    # beamStrainDoFs = []
    # beamLengths = []
    # sum = 0.
    # beamCurvAbscissa = []
    # beamCurvAbscissa.append(0.0)
    #
    # # EXPERIMENTAL: insertion navigation
    # # Initially defining beams with 0 length, at 0
    # # For each beam, we:
    # #     - Add a Vec3 in beamStrainDoFs, with each strain component set at 0.
    # #     - Add 0 in the length data field for the Cosserat mapping
    # #     - Add the last curvilinear abscissa (total length) in the beams
    # # curvilinear abcissas in the Cosserat mapping.
    # # This is equivalent to saying that the beams are 0-length,
    # # 0-strain beams, added at the beginning of the instrument.
    # for i in range(0, nbBeams):
    #     beamStrainDoFs.append([0, 0, 0])
    #     beamLengths.append(0)
    #     beamCurvAbscissa.append(0)
    #
    # # Define angular rate which is the torsion(x) and bending (y, z) of each section
    # rateAngularDeformNode1 = instrument1Node.addChild('rateAngularDeform1')
    # rateAngularDeformMO = rateAngularDeformNode1.addObject('MechanicalObject',
    #                                                        template='Vec3d',
    #                                                        name='rateAngularDeformMO',
    #                                                        position=beamStrainDoFs,
    #                                                        showIndices=0,
    #                                                        rest_position=[0.0, 0.0, 0.0])
    #
    # beamCrossSectionShape='circular'
    # sectionRadius = 0.5
    # poissonRatio = 0.45
    # beamPoissonRatioList = [poissonRatio]*(nbBeams)
    # youngModulus = 5.0e6
    # beamYoungModulusList = [youngModulus]*(nbBeams)
    # yieldStress = 5.0e4
    # yieldStressList = [yieldStress]*(nbBeams)
    # plasticModulus = 2.0e5
    # plasticModulusList = [plasticModulus]*(nbBeams)
    # hardeningCoeff = 0.5
    # hardeningCoefficientList = [hardeningCoeff]*(nbBeams)
    # ### Plastic FF version
    # rateAngularDeformNode1.addObject('BeamPlasticLawForceField', name="beamForceField",
    #                                  crossSectionShape=beamCrossSectionShape,
    #                                  radius=sectionRadius, variantSections="true",
    #                                  length=beamLengths, poissonRatioList=beamPoissonRatioList,
    #                                  youngModulusList=beamYoungModulusList,
    #                                  initialYieldStresses=yieldStressList,
    #                                  plasticModuli=plasticModulusList,
    #                                  mixedHardeningCoefficients= hardeningCoefficientList)
    # ### Elastic FF version
    # # rateAngularDeformNode.addObject('BeamHookeLawForceField', name="beamForceField",
    # #                                 crossSectionShape=beamCrossSectionShape,
    # #                                 radius=sectionRadius, variantSections="true",
    # #                                 length=beamLengths, poissonRatioList=beamPoissonRatioList,
    # #                                 youngModulusList=beamYoungModulusList)
    #
    # beamBendingMoment = 1.0e5
    # bendingForces = np.array([0, beamBendingMoment, beamBendingMoment])
    # # momentIndices = range(1, nbBeams)
    # momentIndices = [nbBeams-1]
    # # rateAngularDeformNode.addObject('ConstantForceField', name='Moment',
    # #                                 indices=momentIndices,
    # #                                 forces=bendingForces)
    #
    # # EXPERIMENTAL: navigation simulation
    # # Adding constraints on the additional beams which are not meant to be
    # # simulated
    # # fixedIndices = list(range(nbBeams, nbBeams+nbStockBeams))
    # fixedIndices = list(range(0, nbBeams))
    # rateAngularDeformNode1.addObject('FixedConstraint', name='FixedConstraint',
    #                                 indices=fixedIndices)
    #
    # # ----- Frames ----- #
    #
    # # Define local frames related to each section and parameters framesCurvAbscissa
    # frames6DDoFs = []
    # frames3DDoFs = []
    # framesCurvAbscissa = []
    # for i in range(nbFrames):
    #     sol = i * distBetweenFrames
    #     frames3DDoFs.append([0, 0, 0])
    #     frames6DDoFs.append([0, 0, 0,  0, 0, 0, 1])
    #     framesCurvAbscissa.append(0)
    #
    # frames6DDoFs.append([0, 0, 0, 0, 0, 0, 1])
    # framesCurvAbscissa.append(0)
    #
    # # The node of the frame needs to inherit from rigidBaseMO and rateAngularDeform
    # mappedFrameNode = rigidBaseNode1.addChild('MappedFrames')
    # rateAngularDeformNode1.addChild(mappedFrameNode)
    #
    # framesMO = mappedFrameNode.addObject('MechanicalObject', template='Rigid3d',
    #                                      name="FramesMO", position=frames6DDoFs,
    #                                      showObject=True, showObjectScale=1)
    #
    # # The mapping has two inputs: RigidBaseMO and rateAngularDeformMO
    # #                 one output: FramesMO
    # inputMO = rateAngularDeformMO.getLinkPath()
    # inputMO_rigid = RigidBaseMO.getLinkPath()
    # outputMO = framesMO.getLinkPath()
    #
    # mappedFrameNode.addObject('DiscreteCosseratMapping', curv_abs_input=beamCurvAbscissa,
    #                           curv_abs_output=framesCurvAbscissa, input1=inputMO, input2=inputMO_rigid,
    #                           output=outputMO, forcefield='@../../rateAngularDeform/beamForceField',
    #                           nonColored=False, debug=0)




    # -------------------------------------------------------------------- #
    # -----                    Python controllers                    ----- #
    # -------------------------------------------------------------------- #

    # rootNode.addObject(BendingController(name="BendingController",
    #                                      bendingMoment=beamBendingMoment))
    nbInstruments=1
    instrumentBeamDensities=[4]
    incrementDistance=0.1
    isInstrumentStraightVect=[True]
    curvAbsTolerance= incrementDistance * 1.0e-6
    instrumentLengths=[totalLength]

    rootNode.addObject(CombinedInstrumentsController(
                            name="NavigationController",
                            rootNode=rootNode,
                            nbInstruments=nbInstruments,
                            instrumentBeamDensityVect=instrumentBeamDensities,
                            incrementDistance=incrementDistance,
                            isInstrumentStraightVect=isInstrumentStraightVect,
                            curvAbsTolerance=curvAbsTolerance,
                            instrumentLengths=instrumentLengths))

    return rootNode