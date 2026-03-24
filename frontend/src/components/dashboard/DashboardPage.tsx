import React from 'react'
import { useAuth } from '../../context/AuthContext'
import Sidebar from '../sidebar/Sidebar';
import UserDashboard from './UserDashboard';

const DashboardPage = () => {
  return (
    <div className='flex flex-row'>
      <div>
        <Sidebar />
      </div>
      <div>
        <UserDashboard />
      </div>

    </div>

  )
}

export default DashboardPage