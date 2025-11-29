import React, { useState, useEffect } from 'react';
import { useLocation } from 'wouter';
import { useUser } from '@/contexts/UserContext';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import CompanySignupForm from '@/components/signup/CompanySignupForm';
import { 
  Building, 
  Mail, 
  MapPin, 
  Users, 
  ArrowRight, 
  RefreshCw, 
  Sparkles,
  CheckCircle
} from 'lucide-react';

import { CompanyService } from '@/services/companyService';

export default function CompanyLogin() {
  const [, setLocation] = useLocation();
  const { user, login, updateProfile, clearMockUser } = useUser();
  const { toast } = useToast();
  
  const [companyName, setCompanyName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [industry, setIndustry] = useState('');
  const [companySize, setCompanySize] = useState('');
  const [userLocation, setUserLocation] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isApiAvailable, setIsApiAvailable] = useState(true);

  const [activeTab, setActiveTab] = useState('login');

  // Check if user is already logged in and redirect if needed
  useEffect(() => {
    if (user && user.isLoggedIn) {
      console.log('CompanyLogin: User already logged in, redirecting to dashboard');
      setLocation('/company-dashboard');
    }
  }, [user, setLocation]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email || !password) {
      toast({
        title: "Missing Information",
        description: "Please enter both email and password.",
        variant: "destructive"
      });
      return;
    }
    
    setIsLoading(true);
    
    try {
      // Try to login using the company service (API first, then mock data)
      const loginResponse = await CompanyService.login({ email, password });
      
      if (loginResponse.success) {
        // Update API availability status - assuming API is available if login succeeds
        setIsApiAvailable(true);
        
        // Create user profile from company service response
        await login(
          loginResponse.company.name,
          loginResponse.company.email
        );
        
        // Update user profile with company details
          updateProfile({
                    companyDetails: {
                      id: loginResponse.company.id,
                      name: loginResponse.company.name,
                      industry: loginResponse.company.industry,
                      size: loginResponse.company.size,
                      location: loginResponse.company.location
                    }
                  });
        
        // Show success toast
        const modeText = !isApiAvailable ? " (Offline Mode)" : "";
        toast({
          title: "Login Successful",
          description: `Welcome back!${modeText} Redirecting to dashboard...`,
        });
        
        // Navigate to company dashboard
        console.log('CompanyLogin: Navigating to /company-dashboard');
        setLocation('/company-dashboard');
        
      } else {
        throw new Error('Login failed');
      }
      
    } catch (error) {
      console.error('Login failed:', error);
      
      // Check if we should fall back to mock user creation
      if (!isApiAvailable) {
        try {
          // Create mock user as fallback
          await login(
            companyName || 'Test Company',
            email
          );
          
          toast({
            title: "Offline Mode",
            description: "Using offline mode. Redirecting to dashboard...",
          });
          
          setLocation('/company-dashboard');
          return;
        } catch (mockError) {
          console.error('Mock user creation failed:', mockError);
        }
      }
      
      toast({
        title: "Login Failed",
        description: "Please check your credentials and try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignupSuccess = (userData: any) => {
    console.log('CompanyLogin: Signup success, user data:', userData);
    toast({
      title: "Account Created",
      description: "Your company account has been created successfully!",
    });
    
    // Navigate to company dashboard
    setLocation('/company-dashboard');
  };

  const handleBackToLogin = () => {
    setActiveTab('login');
  };

  const resetForm = () => {
    setCompanyName('');
    setEmail('');
    setPassword('');
    setIndustry('');
    setCompanySize('');
    setUserLocation('');
    clearMockUser?.();
    toast({
      title: "Form Reset",
      description: "All fields have been cleared.",
    });
  };

  const clearSession = () => {
    console.log('CompanyLogin: Clearing session data');
    clearMockUser?.();
    localStorage.removeItem('userProfile');
    toast({
      title: "Session Cleared",
      description: "All user data has been cleared. You can now log in fresh.",
    });
  };

  // If user is already logged in, redirect to dashboard
  useEffect(() => {
    if (user && user.isLoggedIn) {
      console.log('CompanyLogin: User already logged in, redirecting to dashboard');
      setLocation('/company-dashboard');
    }
  }, [user, setLocation]);

  // If user is already logged in, show a loading state while redirecting
  if (user && user.isLoggedIn) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <Card className="w-full max-w-md bg-slate-800 border-slate-700">
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-slate-200">Redirecting to dashboard...</p>
              <p className="text-sm text-slate-400 mt-2">Please wait while we load your company dashboard.</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 relative overflow-hidden">
      {/* Background decorative elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-tr from-indigo-500/20 to-pink-500/20 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-gradient-to-r from-cyan-500/10 to-blue-500/10 rounded-full blur-3xl"></div>
      </div>

      <div className="relative z-10 min-h-screen flex flex-col items-center justify-center p-4">
        <div className="w-full max-w-7xl mx-auto flex flex-col items-center">
          {/* Enhanced Header with animations */}
          <div className="flex items-center mb-8 group cursor-pointer transition-all duration-300 hover:scale-105">
            <div className="relative">
              <img 
                src="/logo.svg" 
                alt="HopeLoom Logo" 
                className="h-20 w-20 mr-4 drop-shadow-lg transition-all duration-300 group-hover:drop-shadow-xl" 
              />
              <div className="absolute -inset-2 bg-gradient-to-r from-blue-500/30 to-purple-500/30 rounded-full blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            </div>
            <div>
              <h1 className="text-5xl font-bold bg-gradient-to-r from-white via-blue-200 to-indigo-200 bg-clip-text text-transparent">
                {/* modeConfig.title is removed as per new_code, assuming it's no longer needed */}
                HopeLoom
              </h1>
              <p className="text-slate-300 text-lg font-medium">Your AI-powered hiring assistant</p>
            </div>
          </div>
          
          {/* Main content with enhanced layout */}
          <div className="w-full flex flex-col lg:flex-row gap-12 items-center lg:items-start">
            {/* Enhanced Login/Signup form */}
            <div className="w-full lg:w-2/5 max-w-lg order-2 lg:order-1">
              <Card className="border-0 shadow-2xl bg-slate-800/80 backdrop-blur-sm border-slate-600">
                <CardHeader className="space-y-3 pb-6">
                  <div className="text-center space-y-2">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl mb-4 shadow-lg">
                      <Building className="h-8 w-8 text-white" />
                    </div>
                    <CardTitle className="text-3xl font-bold bg-gradient-to-r from-white to-blue-200 bg-clip-text text-transparent">
                      {activeTab === 'login' ? 'Welcome Back' : 'Join HopeLoom'}
                    </CardTitle>
                    <p className="text-slate-300 text-base">
                      {activeTab === 'login' 
                        ? 'Sign in to access your company dashboard and candidate screening tools'
                        : 'Create your company account and start screening candidates with AI'
                      }
                    </p>
                    {/* Connection Status Indicator */}
                    {activeTab === 'login' && (
                      <div className="flex items-center justify-center gap-2 mt-3">
                        <div className={`w-2 h-2 rounded-full ${isApiAvailable ? 'bg-green-400' : 'bg-orange-400'}`}></div>
                        <span className={`text-xs ${isApiAvailable ? 'text-green-400' : 'text-orange-400'}`}>
                          {isApiAvailable ? 'Connected to Server' : 'Offline Mode'}
                        </span>
                      </div>
                    )}
                  </div>
                </CardHeader>
                
                <CardContent>
                  <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as 'login' | 'signup')} className="w-full">
                    <TabsList className="grid w-full grid-cols-2 mb-6">
                      <TabsTrigger value="login">Sign In</TabsTrigger>
                      <TabsTrigger value="signup">Sign Up</TabsTrigger>
                    </TabsList>

                    {/* Login Tab */}
                    <TabsContent value="login" className="space-y-6">
                      <form onSubmit={handleLogin} className="space-y-6">
                        <div className="space-y-3">
                          <Label htmlFor="companyName" className="text-slate-200 font-semibold text-sm">
                            Company Name
                          </Label>
                          <div className="relative">
                            <Input 
                              id="companyName"
                              placeholder="Enter your company name" 
                              value={companyName}
                              onChange={(e) => setCompanyName(e.target.value)}
                              required
                              className="h-12 border-slate-600 bg-slate-700 text-white placeholder:text-slate-400 focus:border-blue-400 focus:ring-blue-400/20 focus:bg-slate-600 transition-all duration-200 text-base pl-4 pr-4"
                            />
                            <div className="absolute inset-y-0 right-0 w-1 bg-gradient-to-b from-blue-400 to-indigo-500 rounded-r-md opacity-0 transition-opacity duration-200 focus-within:opacity-100"></div>
                          </div>
                        </div>

                        <div className="space-y-3">
                          <Label htmlFor="email" className="text-slate-200 font-semibold text-sm">
                            Email Address
                          </Label>
                          <div className="relative">
                            <Input 
                              id="email"
                              type="email"
                              placeholder="Enter your email address" 
                              value={email}
                              onChange={(e) => setEmail(e.target.value)}
                              required
                              className="h-12 border-slate-600 bg-slate-700 text-white placeholder:text-slate-400 focus:border-blue-400 focus:ring-blue-400/20 focus:bg-slate-600 transition-all duration-200 text-base pl-4 pr-4"
                            />
                            <div className="absolute inset-y-0 right-0 w-1 bg-gradient-to-b from-blue-400 to-indigo-500 rounded-r-md opacity-0 transition-opacity duration-200 focus-within:opacity-100"></div>
                          </div>
                        </div>

                        <div className="space-y-3">
                          <Label htmlFor="password" className="text-slate-200 font-semibold text-sm">
                            Password
                          </Label>
                          <div className="relative">
                            <Input 
                              id="password"
                              type="password"
                              placeholder="Enter your password" 
                              value={password}
                              onChange={(e) => setPassword(e.target.value)}
                              required
                              className="h-12 border-slate-600 bg-slate-700 text-white placeholder:text-slate-400 focus:border-blue-400 focus:ring-blue-400/20 focus:bg-slate-600 transition-all duration-200 text-base pl-4 pr-4"
                            />
                            <div className="absolute inset-y-0 right-0 w-1 bg-gradient-to-b from-blue-400 to-indigo-500 rounded-r-md opacity-0 transition-opacity duration-200 focus-within:opacity-100"></div>
                          </div>
                        </div>

                        <Button 
                          type="submit" 
                          disabled={isLoading || !email || !password}
                          className="w-full h-12 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold text-base transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98] shadow-lg hover:shadow-xl"
                        >
                          {isLoading ? (
                            <span className="flex items-center">
                              <RefreshCw className="w-5 h-5 mr-2 animate-spin" />
                              Signing In...
                            </span>
                          ) : (
                            <span className="flex items-center group">
                              {isApiAvailable ? 'Sign In' : 'Sign In (Offline)'}
                              <ArrowRight className="ml-2 h-5 w-5 transition-transform duration-200 group-hover:translate-x-1" />
                            </span>
                          )}
                        </Button>
                      </form>
                    </TabsContent>

                    {/* Signup Tab */}
                    <TabsContent value="signup" className="space-y-6">
                      <CompanySignupForm 
                        onSignupSuccess={handleSignupSuccess}
                        onBackToLogin={handleBackToLogin}
                      />
                    </TabsContent>
                  </Tabs>
                </CardContent>
                
                <CardFooter className="flex flex-col space-y-4 pt-6">
                  <div className="w-full pt-4 border-t border-slate-100">
                    <div className="text-xs text-center text-slate-500 space-y-1">
                      <p>By continuing, you agree to HopeLoom's Terms of Service and Privacy Policy.</p>
                      <p>Need help? Contact <a href="mailto:info@hopeloom.com" className="text-blue-600 hover:text-blue-700 hover:underline font-medium">info@hopeloom.com</a></p>
                    </div>
                  </div>
                </CardFooter>
              </Card>
            </div>
            
            {/* Right side content - Company Screening Features */}
            <div className="w-full lg:w-3/5 order-1 lg:order-2">
              <div className="space-y-8">
                {/* Feature highlights */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-600 rounded-2xl p-6 hover:border-blue-400/50 transition-all duration-300 group">
                    <div className="flex items-center mb-4">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center mr-4 group-hover:scale-110 transition-transform duration-300">
                        <Users className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="text-xl font-semibold text-white">AI Candidate Screening</h3>
                    </div>
                    <p className="text-slate-300 text-sm leading-relaxed">
                      Automatically screen candidates with AI-powered interviews that assess technical skills and cultural fit.
                    </p>
                  </div>

                  <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-600 rounded-2xl p-6 hover:border-blue-400/50 transition-all duration-300 group">
                    <div className="flex items-center mb-4">
                      <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center mr-4 group-hover:scale-110 transition-transform duration-300">
                        <CheckCircle className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="text-xl font-semibold text-white">Custom Interview Design</h3>
                    </div>
                    <p className="text-slate-300 text-sm leading-relaxed">
                      Design tailored interview experiences that match your company's specific requirements and culture.
                    </p>
                  </div>

                  <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-600 rounded-2xl p-6 hover:border-blue-400/50 transition-all duration-300 group">
                    <div className="flex items-center mb-4">
                      <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl flex items-center justify-center mr-4 group-hover:scale-110 transition-transform duration-300">
                        <Sparkles className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="text-xl font-semibold text-white">Real-time Analytics</h3>
                    </div>
                    <p className="text-slate-300 text-sm leading-relaxed">
                      Get detailed insights into candidate performance with comprehensive analytics and reporting.
                    </p>
                  </div>

                  <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-600 rounded-2xl p-6 hover:border-blue-400/50 transition-all duration-300 group">
                    <div className="flex items-center mb-4">
                      <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-red-600 rounded-xl flex items-center justify-center mr-4 group-hover:scale-110 transition-transform duration-300">
                        <Sparkles className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="text-xl font-semibold text-white">Talent Pipeline Management</h3>
                    </div>
                    <p className="text-slate-300 text-sm leading-relaxed">
                      Build and manage your talent pipeline with advanced candidate tracking and communication tools.
                    </p>
                  </div>
                </div>

                {/* Call to action */}
                <div className="text-center">
                  <h2 className="text-3xl font-bold text-white mb-4">
                    Transform Your Hiring Process
                  </h2>
                  <p className="text-slate-300 text-lg mb-6 max-w-2xl mx-auto">
                    Join leading companies that have revolutionized their hiring with AI-powered candidate screening and interview automation.
                  </p>
                  <div className="flex flex-col sm:flex-row gap-4 justify-center">
                    <Button 
                      onClick={() => setActiveTab('signup')}
                      className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-8 py-3 text-lg font-semibold"
                    >
                      Start Screening Today
                    </Button>
                    <Button 
                      variant="outline" 
                      className="border-slate-400 text-slate-300 hover:border-blue-400 hover:text-blue-400 px-8 py-3 text-lg"
                    >
                      Learn More
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
