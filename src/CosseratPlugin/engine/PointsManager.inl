#pragma once

#include "PointsManager.h"
#include <sofa/type/Quat.h>
#include <sofa/core/visual/VisualParams.h>
#include <sofa/simulation/AnimateBeginEvent.h>
#include <SofaBaseMechanics/MechanicalObject.h>

namespace sofa::core::behavior
{

    PointsManager::PointsManager()
        : d_beamTip(initData(&d_beamTip, "beamTip", "The beam tip")),
          d_radius(initData(&d_radius, double(1), "radius", "sphere radius")),
          d_color(initData(&d_color, type::Vec4f(1, 0, 0, 1), "color", "Default color is (1,0,0,1)")),
          d_beamPath(initData(&d_beamPath, "beamPath", "path to beam state"))
    {
        this->f_listening.setValue(true);
    }

    void PointsManager::init()
    {
        if (getTopology() == NULL)
            msg_error() << "Error cannot find the topology";

        if (getMstate() == NULL)
            msg_error() << "Error cannot find the topology";

        this->getContext()->get(m_beam, d_beamPath.getValue());
        if (m_beam == nullptr)
            msg_error() << "Cannot find the beam collision state : " << d_beamPath.getValue();

        this->getContext()->get(m_modifier);
        if (m_modifier == NULL)
        {
            msg_error() << " Error cannot find the EdgeSetTopologyModifier";
            return;
        }
    }

    void PointsManager::addNewPointToState()
    {
        helper::WriteAccessor<Data<VecCoord>> x = *this->getMstate()->write(core::VecCoordId::position());
        helper::WriteAccessor<Data<VecCoord>> xfree = *this->getMstate()->write(core::VecCoordId::freePosition());
        const helper::ReadAccessor<Data<VecCoord>> &beam = m_beam->readPositions();
        unsigned nbPoints = this->getTopology()->getNbPoints(); // do not take the last point because there is a bug

        size_t beamSz = beam.size();
        m_modifier->addPoints(1, true);

        Vector3 pos = beam[beamSz - 1];
        std::cout << "beam tip is =-----> " << pos << std::endl;
        std::cout << "nbPoints is equal :" << nbPoints << std::endl;
        std::cout << "x.size is equal :" << x.size() << std::endl;

        x.resize(nbPoints + 1);
        xfree.resize(nbPoints + 1);

        x[nbPoints] = pos;
        xfree[nbPoints] = pos;
        std::cout << "End addNewPointToState " << std::endl;
        m_modifier->notifyEndingEvent();
        std::cout << "End notifyEndingEvent " << std::endl;
    }

    void PointsManager::removeLastePointfromState()
    {
        helper::WriteAccessor<Data<VecCoord>> x = *this->getMstate()->write(core::VecCoordId::position());
        helper::WriteAccessor<Data<VecCoord>> xfree = *this->getMstate()->write(core::VecCoordId::freePosition());
        const helper::ReadAccessor<Data<VecCoord>> &beam = m_beam->readPositions();
        unsigned nbPoints = this->getTopology()->getNbPoints(); // do not take the last point because there is a bug

        size_t beamSz = beam.size();
        sofa::type::vector<unsigned int> Indices;
        Indices.push_back(nbPoints - 1);
        m_modifier->removePoints(Indices, true);

        std::cout << "the size is equal :" << beamSz << std::endl;

        x.resize(nbPoints - 1);
        xfree.resize(nbPoints - 1);

        m_modifier->notifyEndingEvent();
    }

    void PointsManager::handleEvent(sofa::core::objectmodel::Event *event)
    {
        if (KeypressedEvent::checkEventType(event))
        {
            KeypressedEvent *ev = static_cast<KeypressedEvent *>(event);
            switch (ev->getKey())
            {
            case 'S':
            case 's':
                printf("A point is created \n");
                addNewPointToState();
                break;
            case 'L':
            case 'l':
                printf("Remove point from state \n");
                removeLastePointfromState();
                break;
            }
        }
    }

    // void PointsManager::draw(const core::visual::VisualParams *vparams)
    // {

    //     helper::ReadAccessor<Data<VecCoord>> x = *this->getMstate()->read(core::VecCoordId::position());
    //     if (!x.size())
    //         return; // if no points return
    //     glDisable(GL_LIGHTING);
    //     for (unsigned int j = 0; j < x.size(); j++)
    //     {
    //         glColor3f(1.0, 1.0, 0.0);
    //         vparams->drawTool()->drawSphere(x[j], d_radius.getValue() * 0.001);
    //     }
    //     glEnable(GL_LIGHTING);
    // }

} // Sofa
