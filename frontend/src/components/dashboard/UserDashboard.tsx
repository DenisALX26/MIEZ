import React from 'react'
import { useAuth } from '../../context/AuthContext'
import HrDashboard from '../hr/HrDashboard'
import InventorySidebar from '../sidebar/InventorySidebar';
import ItDashboard from './ItDashboard';
import SalesDashboard from './SalesDashboard';
import InventoryDashboard from './InventoryDashboard';

const UserDashboard = () => {
  const { user, logout } = useAuth();
  return (
    <>
      <div >
        {user && user.role === 'HR' && (
          <HrDashboard />
        )}
        {user && user.role === 'IT' && (
          <ItDashboard />
        )}
        {user && user.role === 'SALES' && (
          <SalesDashboard />
        )}
        {user && user.role === 'INVENTORY' && (
          <InventoryDashboard />
        )}
        <button onClick={logout} className='bg-[var(--primary)] p-2 rounded-lg text-white hover:cursor-pointer'>Logout</button>
      </div>
    </>
  )
}

export default UserDashboard