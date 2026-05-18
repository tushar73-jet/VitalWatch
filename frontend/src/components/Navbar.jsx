import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const location = useLocation();
  const { user, logout } = useAuth();

  const links = [
    { name: '/monitor', label: 'Monitor' },
    { name: '/analytics', label: 'Analytics' },
    { name: '/performance', label: 'Performance' },
    { name: '/chatbot', label: 'Chatbot' },
  ];

  return (
    <nav className="fixed top-0 left-0 w-full z-50 bg-black border-b border-cyan-400/20 px-6 py-4 flex items-center justify-between">
      <div className="flex items-center space-x-12">
        <Link to="/" className="text-cyan-400 font-bold text-xl tracking-widest uppercase">
          VitalWatch
        </Link>
        <div className="flex space-x-8">
          {links.map(link => {
            const isActive = location.pathname.startsWith(link.name);
            return (
              <Link
                key={link.name}
                to={link.name}
                className={`transition uppercase tracking-widest text-xs h-full flex items-center ${
                  isActive ? 'text-cyan-400' : 'text-gray-400 hover:text-cyan-400'
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </div>
      </div>
      
      {user && (
        <div className="flex items-center space-x-6 border-l border-gray-800 pl-6">
          <div className="text-right">
            <div className="text-sm font-medium text-white">{user.full_name}</div>
            <div className="text-xs text-gray-500 font-mono uppercase">{user.role}</div>
          </div>
          <button 
            onClick={logout}
            className="text-xs text-gray-400 hover:text-cyan-400 transition uppercase tracking-widest border border-gray-800 hover:border-cyan-400 px-3 py-1.5 rounded"
          >
            Logout
          </button>
        </div>
      )}
    </nav>
  );
}

