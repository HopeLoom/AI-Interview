import React, { createContext, useContext, useState, ReactNode } from 'react';

export interface CompanyProfile {
  id: string;
  name: string;
  email: string;
  userType: 'company';
  isLoggedIn: boolean;
  createdAt: Date;
  // Company-specific fields
  companyDetails: {
    id: string;           // Company ID for API calls
    name: string;         // Company name for display
    industry: string;
    size: string;
    location: string;
    website?: string;
    description?: string;
  };
}

interface CompanyContextType {
  user: CompanyProfile | null;
  isLoading: boolean;
  login: (name: string, email: string, userType?: string) => Promise<void>;
  signup: (name: string, email: string, additionalData?: any) => Promise<void>;
  logout: () => void;
  updateProfile: (updates: Partial<CompanyProfile>) => void;
  isLoggedIn: () => boolean;
  switchToMockUser: () => void; // Add testing helper
  clearMockUser: () => void; // Add testing helper to clear user
}

const CompanyContext = createContext<CompanyContextType | undefined>(undefined);

export const useCompany = () => {
  const context = useContext(CompanyContext);
  if (!context) {
    throw new Error('useCompany must be used within a CompanyProvider');
  }
  return context;
};

interface CompanyProviderProps {
  children: ReactNode;
}

export const CompanyProvider: React.FC<CompanyProviderProps> = ({ children }) => {
  const [user, setUser] = useState<CompanyProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const login = async (name: string, email: string) => {
    try {
      const response = await fetch(`${window.location.protocol}//${import.meta.env.VITE_API_BASE_URL || 'localhost:8000'}/api/companies/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, name }),
      });

      if (!response.ok) {
        throw new Error('Company login failed');
      }

      const data = await response.json();

      if (data.success && data.company) {
        const company = data.company;

        // Create user profile from backend data
        const userProfile: CompanyProfile = {
          id: company.id,
          name: company.name,
          email: company.email,
          userType: 'company',
          isLoggedIn: true,
          createdAt: new Date(company.createdAt || new Date()),
          companyDetails: {
            id: company.companyId || company.id,
            name: company.companyName || company.name,
            industry: company.industry || '',
            size: company.size || '',
            location: company.location || '',
            website: company.website,
            description: company.description
          }
        };

        setUser(userProfile);
        localStorage.setItem('companyProfile', JSON.stringify(userProfile));
        console.log('CompanyContext: Company profile loaded from backend');
        return;
      }

      throw new Error('Login failed - invalid response from server');

    } catch (error) {
      console.error('Login error:', error);
      throw new Error(error instanceof Error ? error.message : 'Login failed');
    }
  };

  const signup = async (name: string, email: string, additionalData?: any) => {
    try {
      const id = `company_${Date.now()}`;
      const userProfile: CompanyProfile = {
        id,
        name,
        email,
        userType: 'company',
        isLoggedIn: true,
        createdAt: new Date(),
        companyDetails: {
          id: `company_${Date.now()}`,  // Generate unique company ID
          name: name,                   // Use company name from signup
          industry: additionalData?.industry || '',
          size: additionalData?.size || '',
          location: additionalData?.location || ''
        }
      };
      
      setUser(userProfile);
      
      // Persist company user data for global access
      localStorage.setItem('companyProfile', JSON.stringify(userProfile));
      console.log('CompanyContext: Company user profile saved to localStorage');
      
    } catch (error) {
      throw new Error('Company signup failed');
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('companyProfile');
    console.log('CompanyContext: Company user logged out, localStorage cleared');
  };

  const updateProfile = (updates: Partial<CompanyProfile>) => {
    if (user) {
      const updatedUser = { ...user, ...updates };
      setUser(updatedUser);
      localStorage.setItem('companyProfile', JSON.stringify(updatedUser));
      console.log('CompanyContext: Company user profile updated in localStorage');
    }
  };

  const isLoggedIn = () => user?.isLoggedIn || false;

  // Testing helper: Switch to mock company user
  const switchToMockUser = () => {
    const mockUser: CompanyProfile = {
      id: `mock_company_${Date.now()}`,
      name: 'Test Company',
      email: 'test.company@example.com',
      userType: 'company',
      isLoggedIn: true,
      createdAt: new Date(),
      companyDetails: {
        id: `mock_company_${Date.now()}`,
        name: 'Test Company',
        industry: 'Technology',
        size: '100-500',
        location: 'San Francisco, CA'
      }
    };
    
    console.log('CompanyContext: Switching to mock company user:', mockUser);
    setUser(mockUser);
    localStorage.setItem('companyProfile', JSON.stringify(mockUser));
    console.log('CompanyContext: Mock company user saved to localStorage');
  };

  // Testing helper: Clear mock user and start fresh
  const clearMockUser = () => {
    console.log('CompanyContext: Clearing mock company user');
    setUser(null);
    localStorage.removeItem('companyProfile');
  };

  // Load user from localStorage on mount
  React.useEffect(() => {
    console.log('CompanyContext: Loading company user from localStorage...');
    
    const savedUser = localStorage.getItem('companyProfile');
    console.log('CompanyContext: Saved user from localStorage:', savedUser ? 'Found' : 'Not found');
    
    if (savedUser) {
      try {
        const parsedUser = JSON.parse(savedUser);
        
        // Only restore if it's a company user
        if (parsedUser.userType === 'company') {
          parsedUser.createdAt = new Date(parsedUser.createdAt);
          console.log('CompanyContext: Restored company user:', parsedUser);
          setUser(parsedUser);
        } else {
          console.log('CompanyContext: Found non-company user in localStorage - clearing');
          localStorage.removeItem('companyProfile');
        }
      } catch (error) {
        console.error('CompanyContext: Failed to parse saved user profile');
        localStorage.removeItem('companyProfile');
      }
    } else {
      console.log('CompanyContext: No saved company user found in localStorage');
    }
    
    setIsLoading(false);
    console.log('CompanyContext: Loading complete, isLoading set to false');
  }, []);

  return (
    <CompanyContext.Provider value={{ 
      user, 
      isLoading,
      login, 
      signup, 
      logout, 
      updateProfile,
      isLoggedIn,
      switchToMockUser,
      clearMockUser
    }}>
      {children}
    </CompanyContext.Provider>
  );
};
