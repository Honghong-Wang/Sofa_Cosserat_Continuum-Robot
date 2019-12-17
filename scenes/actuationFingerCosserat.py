# -*- coding: utf-8 -*-

from CosseratActuation import *
import Sofa
import SofaPython
from math import sin,cos, sqrt, pi
from stlib.physics.collision import CollisionMesh
import os
path = os.path.dirname(os.path.abspath(__file__))+'/mesh/'


curv_abs_input=[0, 15, 30, 45, 60, 66, 81]
curv_abs_output=[0.0, 5, 10, 15, 20, 30, 35, 40, 45, 55, 60, 66, 71, 76, 81]

position=["0 0 0 " + "0 0 0 " + "0 0 0 " + "0 0 0 " + "0 0 0 " + "0 0 0 " ]
longeur = '15 15 15 15 6 15' # beams size
distance1 = [0.0,0.5,0.0]; distance2 = [0.0,0.1,0.0]; distance3 = [0.0,0.5,0.0]; _distance = [distance1, distance2, distance3]
ddistance1 = [0.0,0.0,0.0]; ddistance2 = [0.0,0.0,0.0]; ddistance3 = [0.0,0.0,0.0]; _ddistance = [ddistance1, ddistance2, ddistance3]
R_b = 1.0
L = 75.0

_tension = 0.0

class Animation(CosseratActuation):

    """docstring for DataComputationClass.Sofa.PythonScriptController"""

    def __init__(self):
        super(DataComputationClass,Sofa.PythonScriptController).__init__()

    def initGraph(self, node):
        self.tension = 50.0
        self.node = node;
        self.BeamHookeLawForce = self.node.getObject('BeamHookeLawForce')
        self.rateAngularDeformMO = self.node.getObject('rateAngularDeformMO')
        self.K = self.rateAngularDeformMO.findData('position').value
        print ("Size of K :", len(self.K))
        self.X  = self.computeX()
        self.distance = [] # distance
        self.d_distance = [] # derivative of the distance

        #CONSTANT parameters ( dy, dz, _dy, _dz)
        self.vec_dy  = [R_b/2.0]; self.vec_dz  = [0.0]
        self.vec_ddy = [0.0];     self.vec_ddz = [0.0]

        # self.vec_dy  = [R_b/2.0]; self.vec_dz  = [0.0]
        # self.vec_ddy = [-R_b/L];     self.vec_ddz = [0.0]

        self.muti_ActuationIntegral(self.vec_dy, self.vec_dz, self.vec_ddy, self.vec_ddz, self.K)


        ############################## HELICAL PARAMETERS ####################################""
        # d = R_b/2.0
        # alpha = 1.529
        # p = 2.0 * pi * d * tan(alpha)
        # self.computeHelicalParameters(d, p)
        # print ("############################## HELICAL PARAMETERS ####################################")
        # print ("=======+++++++> self.distance : ",self.distance)
        # print ("=======+++++++> self.distance : ",self.d_distance)
        #
        self.BeamHookeLawForce.findData('distance0').value = self.distance[0]
        self.BeamHookeLawForce.findData('distance1').value = self.distance[1]
        self.BeamHookeLawForce.findData('ddistance0').value = self.d_distance[0]
        self.BeamHookeLawForce.findData('ddistance1').value = self.d_distance[1]


    def onBeginAnimationStep(self, dt):
        self.tension = self.tension + 80.0 * dt;
        self.K = self.rateAngularDeformMO.findData('position').value

        integral = self.muti_ActuationIntegral(self.vec_dy, self.vec_dz, self.vec_ddy, self.vec_ddz, self.K)
        # print ("=++++++++=======+++> 0) muti_ActuationIntegral : ", integral )
        listIntegral = []
        for i in range(0,len(integral)):
            listIntegral.append(integral[i])

        # print("+++++++++++++++++++>>>> listIntegral: ",listIntegral)
        self.BeamHookeLawForce.findData('integral').value = listIntegral
        # print ("=++++++++=======+++> 1) muti_ActuationIntegral : ", integral )

        if(self.tension < 200.0):
            self.BeamHookeLawForce.findData('tension').value = self.tension
            # print("Tension is : "+str(self.tension))


def engineRigid2Vec3(mappedFrameNode,cable):
    mappedFrameNode = mappedFrameNode.getObject('FramesMO')
    cableNode = cable.getObject('cablePos')
    frames = mappedFrameNode.findData('position').value;
    position = []
    for i in range(len(frames)):
        position.append([])
        # print ('frames :', frames[i])
        for k in range(3) :
            position[i].append(frames[i][k])
    cableNode.findData('position').value = position
    cableNode.findData('rest_position').value = position


    print(position)


def createScene(rootNode):
                import os
                from stlib.scene import MainHeader, ContactHeader
                MainHeader(rootNode, plugins=["SoftRobots","SofaPython","SofaSparseSolver", "SofaPreconditioner", "SofaOpenglVisual", "CosseratPlugin", "BeamAdapter"],
                repositoryPaths=[os.getcwd()])
                # rootNode.createObject('RequiredPlugin', pluginName='SoftRobots SofaPython SofaSparseSolver ')
                rootNode.createObject('VisualStyle', displayFlags='showVisualModels hideBehaviorModels showCollisionModels hideBoundingCollisionModels hideForceFields showInteractionForceFields showWireframe')


                rootNode.gravity = "0 -9810 0"
                rootNode.dt="0.01"
                ContactHeader(rootNode, alarmDistance=4, contactDistance=3, frictionCoef=0.08)
                rootNode.createObject('BackgroundSetting', color='0 0.168627 0.211765')
                rootNode.createObject('OglSceneFrame', style="Arrows", alignment="TopRight")

                rootNode.createObject('FreeMotionAnimationLoop')
                rootNode.createObject('GenericConstraintSolver', tolerance="1e-5", maxIterations="100", printLog="1")
                
                cableNode = rootNode.createChild('cableNode')
                cableNode.createObject('EulerImplicitSolver', firstOrder="0", rayleighStiffness="1.0", rayleighMass='0.1')
                cableNode.createObject('SparseLUSolver', name='solver')
                cableNode.createObject('GenericConstraintCorrection')

                ###############hresho
                ## RigidBase
                ###############
                rigidBaseNode= cableNode.createChild('rigidBase')
                RigidBaseMO = rigidBaseNode.createObject('MechanicalObject', template='Rigid3d', name="RigidBaseMO", position="0 0 0  0 0 0 1", showObject='1', showObjectScale='0.1' )
                rigidBaseNode.createObject('RestShapeSpringsForceField', name='spring', stiffness="50000", angularStiffness="50000", external_points="0", mstate="@RigidBaseMO", points="0", template="Rigid3d"  )

                ###############
                ## Rate of angular Deformation  (2 sections)
                ###############
                rateAngularDeformNode = cableNode.createChild('rateAngularDeform')
                rateAngularDeformMO = rateAngularDeformNode.createObject('MechanicalObject', template='Vec3d', name='rateAngularDeformMO', position=position)
                # BeamHookeLawForce = rateAngularDeformNode.createObject('BeamHookeLawForceField', crossSectionShape='circular', length=longeur, radius='0.5', youngModulus='5e6')

                BeamHookeLawForce = rateAngularDeformNode.createObject('CosseratInternalActuation', name="BeamHookeLawForce",  crossSectionShape='circular', length=longeur, radius='0.5',
                youngModulus='5.93e4',distance0=_distance, distance1=_distance, ddistance=_ddistance, tension=_tension)
                rateAngularDeformNode.createObject('PythonScriptController', classname="Animation")

                ##############
                ## Frames
                ##############
                frames=[ "0.0 0 0  0 0 0 1   5 0 0  0 0 0 1  10.0 0 0  0 0 0 1    15.0 0 0  0 0 0 1   20.0 0 0  0 0 0 1" +
                                " 30.0 0 0  0 0 0 1  35.0 0 0  0 0 0 1   40.0 0 0  0 0 0 1   45.0 0 0  0 0 0 1 55.0 0 0  0 0 0 1 60.0 0 0  0 0 0 1"+
                                " 66.0 0 0  0 0 0 1   71.0 0 0  0 0 0 1   76.0 0 0  0 0 0 1  81.0 0 0  0 0 0 1"]
                # the node of the frame needs to inherit from rigidBaseMO and rateAngularDeform
                mappedFrameNode = rigidBaseNode.createChild('MappedFrames')
                rateAngularDeformNode.addChild(mappedFrameNode)
                framesMO = mappedFrameNode.createObject('MechanicalObject', template='Rigid3d', name="FramesMO", position=frames, showObject='1', showObjectScale='1' )

                # The mapping has two inputs: RigidBaseMO and rateAngularDeformMO
                #                 one output: FramesMO
                inputMO = rateAngularDeformMO.getLinkPath()
                inputMO_rigid = RigidBaseMO.getLinkPath()
                outputMO = framesMO.getLinkPath()

                mappedFrameNode.createObject('DiscretCosseratMapping', curv_abs_input=curv_abs_input, curv_abs_output=curv_abs_output, input1=inputMO, input2=inputMO_rigid,output=outputMO, debug='0' )

                # #### FingerTopo
                finger = mappedFrameNode.createChild('finger')
                finger.createObject('MeshVTKLoader', name='loader', filename=path+'finger.vtk', translation="-17.5 -12.5 7.5", rotation="0 180 0")
                finger.createObject('TetrahedronSetTopologyContainer', src='@loader', name='container')
                finger.createObject('TetrahedronSetTopologyModifier')
                finger.createObject('MechanicalObject', name='tetras', template='Vec3d', showIndices='false', showIndicesScale='4e-5', rx='0', dz='0')
                finger.createObject('Triangle')
                finger.createObject('SkinningMapping', nbRef='2')

                return rootNode

                ##########################################
                # FEM Model                              #
                ##########################################
                finger = rootNode.createChild('finger')
                finger.createObject('EulerImplicitSolver', name='odesolver', firstOrder='0', rayleighMass="0.1", rayleighStiffness="0.1")
                finger.createObject('SparseLDLSolver', name='preconditioner')

		        # Add a componant to load a VTK tetrahedral mesh and expose the resulting topology in the scene .
                finger.createObject('MeshVTKLoader', name='loader', filename=path+'finger.vtk', translation="-17.5 -12.5 7.5", rotation="0 180 0")
                finger.createObject('TetrahedronSetTopologyContainer', src='@loader', name='container')
                finger.createObject('TetrahedronSetTopologyModifier')
                finger.createObject('TetrahedronSetTopologyAlgorithms', template='Vec3d')
                finger.createObject('TetrahedronSetGeometryAlgorithms', template='Vec3d')

                # Create a mechanicaobject component to stores the DoFs of the model
                finger.createObject('MechanicalObject', name='tetras', template='Vec3d', showIndices='false', showIndicesScale='4e-5', rx='0', dz='0')

                # Gives a mass to the model
                finger.createObject('UniformMass', totalMass='0.075')

                # Add a TetrahedronFEMForceField componant which implement an elastic material model solved using the Finite Element Method on
                # tetrahedrons.
                finger.createObject('TetrahedronFEMForceField', template='Vec3d', name='FEM', method='large', poissonRatio='0.45',  youngModulus='600')

                # To facilitate the selection of DoFs, SOFA has a concept called ROI (Region of Interest).
		        # The idea is that ROI component "select" all DoFS that are enclosed by their "region".
                # We use ROI here to select a group of finger's DoFs that will be constrained to stay
                # at a fixed position.
                # You can either use "BoxROI"...
                finger.createObject('BoxROI', name='ROI1', box='-18 -15 -8 2 -3 8', drawBoxes='true')
                # Or "SphereROI"...
                #finger.createObject('SphereROI', name='ROI', centers='0 0 0', radii='5')

                # RestShapeSpringsForceField is one way in Sofa to implement fixed point constraint.
                # Here the constraints are applied to the DoFs selected by the previously defined BoxROI
                finger.createObject('RestShapeSpringsForceField', points='@ROI1.indices', stiffness='1e12')

                # It is also possible to simply set by hand the indices of the points you want to fix.
                #finger.createObject('RestShapeSpringsForceField', points='0 1 2 11 55', stiffness='1e12')
                finger.createObject('LinearSolverConstraintCorrection')

                ##########################################
                # Cable points                           #
                ##########################################
                # Mappe points inside the meca, this points will be use for the bilateral mapping
                points = finger.createChild('points')
                points.createObject('MechanicalObject', name="pointsInFEM" ,position=FEMpos, showObject="1", showIndices="1")
                points.createObject('BarycentricMapping')


                ##########################################
                # Visualization                          #
                ##########################################
                # In Sofa, visualization is handled by adding a rendering model.
                # Create an empty child node to store this rendering model.
                CollisionMesh(finger, surfaceMeshFileName="mesh/finger.stl", name="part0", translation="-17.5 -12.5 7.5",
                rotation="0 180 0", collisionGroup=[1, 2])

                ##########################################
                #  Finger auto-Collision            #
                ##########################################
                CollisionMesh(finger,
                 surfaceMeshFileName="mesh/fingerCollision_part1.stl",
                 name="CollisionMeshAuto1", translation="-17.5 -12.5 7.5", rotation="0 180 0", collisionGroup=[1])

                CollisionMesh(finger,
                  surfaceMeshFileName="mesh/fingerCollision_part2.stl",
                  name="CollisionMeshAuto2", translation="-17.5 -12.5 7.5", rotation="0 180 0", collisionGroup=[2])

                #
                # fingerVisu = finger.createChild('visu')
                #
                # # Add to this empty node a rendering model made of triangles and loaded from an stl file.
                # fingerVisu.createObject('MeshSTLLoader', filename=path+"finger.stl", name="loader", translation="-17.5 -12.5 7.5",rotation="0 180 0")
                # fingerVisu.createObject('OglModel', src="@loader", template='ExtVec3f', color="0.0 0.7 0.7")
                #
                # # Add a BarycentricMapping to deform the rendering model in a way that follow the ones of the parent mechanical model.
                # fingerVisu.createObject('BarycentricMapping')

                rootNode.createObject('BilateralInteractionConstraint', template='Vec3d', object2='@cableNode/rigidBase/MappedFrames/cable/cablePos', object1='@finger/points/pointsInFEM', first_point='6', second_point='14', merge="true")
                rootNode.createObject('CosseratSlidingConstraint', name="constraint2", object1="@finger/points/pointsInFEM", object2="@cableNode/rigidBase/MappedFrames/cable/cablePos", sliding_point="0 1", axis_1="0", axis_2="2")

                return rootNode
