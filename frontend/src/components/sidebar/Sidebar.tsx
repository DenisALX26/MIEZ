import React from 'react'
import { useAuth } from '../../context/AuthContext'
import HrSidebar from './HrSidebar';
import ItSidebar from './ItSidebar';
import SalesInventory from './SalesSidebar';
import InventorySidebar from './InventorySidebar';
import SalesSidebar from './SalesSidebar';

const Sidebar = () => {
  const { user, logout } = useAuth();
  return (
    <>
      <div >
        {user && user.role === 'HR' && (
          <HrSidebar />
        )}
        {user && user.role === 'IT' && (
          <ItSidebar />
        )}
        {user && user.role === 'SALES' && (
          <SalesSidebar />
        )}
        {user && user.role === 'INVENTORY' && (
          <InventorySidebar />
        )}
        <button onClick={logout} className='bg-[var(--primary)] p-2 rounded-lg text-white hover:cursor-pointer'>Logout</button>
      </div>
    </>
  )
}

export default Sidebar