import React from 'react';
import { useLocation } from 'wouter';
import { useUser } from '@/contexts/UserContext';
import { Button } from '@/components/ui/button';
import { Building, User, Settings, LogOut, Home, FileText } from 'lucide-react';

export function Navigation() {
  const { user, logout } = useUser();
  const [location, setLocation] = useLocation();

  if (!user) {
    return null;
  }

  const handleLogout = () => {
    logout();
    setLocation('/login');
  };

  const isCompany = user.userType === 'company';
  const isCandidate = user.userType === 'candidate';

  return (
    <nav className="bg-white border-b border-gray-200 px-4 py-3">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Logo and Brand */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 cursor-pointer" onClick={() => setLocation('/')}>
            <img src="/logo.svg" alt="HopeLoom" className="h-8 w-8" />
            <span className="text-xl font-bold text-gray-900">HopeLoom</span>
          </div>
          
          {/* User Type Badge */}
          <div className="flex items-center space-x-2">
            {isCompany ? (
              <Building className="w-4 h-4 text-blue-600" />
            ) : (
              <User className="w-4 h-4 text-green-600" />
            )}
            <span className="text-sm font-medium text-gray-600">
              {isCompany ? 'Company' : 'Candidate'}
            </span>
          </div>
        </div>

        {/* Navigation Links */}
        <div className="flex items-center space-x-4">
          {/* Dashboard Link */}
          <Button
            variant="ghost"
            onClick={() => setLocation(isCompany ? '/company-dashboard' : '/candidate-dashboard')}
            className="flex items-center space-x-2"
          >
            <Home className="w-4 h-4" />
            <span>Dashboard</span>
          </Button>

          {/* Configuration Link */}
          <Button
            variant="ghost"
            onClick={() => setLocation('/configure')}
            className="flex items-center space-x-2"
          >
            <Settings className="w-4 h-4" />
            <span>Configure</span>
          </Button>

          {/* Profile Link */}
          <Button
            variant="ghost"
            onClick={() => setLocation(isCompany ? '/company-dashboard' : '/candidate-dashboard')}
            className="flex items-center space-x-2"
          >
            <FileText className="w-4 h-4" />
            <span>Profile</span>
          </Button>

          {/* User Info and Logout */}
          <div className="flex items-center space-x-3 ml-4 pl-4 border-l border-gray-200">
            <div className="text-right">
              <p className="text-sm font-medium text-gray-900">{user.name}</p>
              <p className="text-xs text-gray-500">{user.email}</p>
            </div>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleLogout}
              className="flex items-center space-x-2"
            >
              <LogOut className="w-4 h-4" />
              <span>Logout</span>
            </Button>
          </div>
        </div>
      </div>
    </nav>
  );
}
