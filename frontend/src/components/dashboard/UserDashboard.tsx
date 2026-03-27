import { useAuth } from '../../context/AuthContext'
import HrDashboard from '../hr/HrDashboard'
import ItDashboard from './ItDashboard'
import SalesDashboard from './SalesDashboard'
import InventoryDashboard from './InventoryDashboard'

const UserDashboard = () => {
  const { user } = useAuth()
  return (
    <div>
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
      </div>
  )
}

export default UserDashboard