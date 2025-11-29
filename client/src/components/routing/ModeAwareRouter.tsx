import React, { useEffect, useMemo, useState } from 'react';
import { Switch, Route, useLocation } from 'wouter';
import { getModeConfig, isRouteAllowed, getDefaultRoute } from '@/lib/modeConfig';
import { useUser } from '@/contexts/UserContext';
import { Toaster } from '@/components/ui/toaster';
import { TooltipProvider } from '@/components/ui/tooltip';
import { UserProvider } from '@/contexts/UserContext';
import { InterviewProvider } from '@/contexts/InterviewContext';
import { ConfigurationProvider } from '@/contexts/ConfigurationContext';
import { CameraProvider } from '@/contexts/CameraContext';
import { ErrorBoundary } from '@/components/ErrorBoundary';

// Pages
import NotFound from '@/pages/not-found';
import Home from '@/pages/Home';
import CandidateLogin from '@/pages/CandidateLogin';
import CompanyLogin from '@/pages/CompanyLogin';
import CompanyCandidateLogin from '@/pages/CompanyCandidateLogin';
import TestDynamicParams from '@/pages/TestDynamicParams';
import TutorialDemo from '@/pages/TutorialDemo';
import ConfigureInterview from '@/pages/ConfigureInterview';

// Mode-specific login component
function ModeSpecificLogin() {
  // Use useMemo to ensure stable mode detection
  const config = useMemo(() => getModeConfig(), []);
  const mode = useMemo(() => config.mode, [config.mode]);
  console.log("ModeSpecificLogin: Mode:", mode);
  // Use a stable component reference
  const LoginComponent = useMemo(() => {
    if (mode === 'candidate-practice') {
      return CandidateLogin;
    } else if (mode === 'company-interviewing') {
      return CompanyLogin;
    } else if (mode === 'company-candidate-interview') {
      return CompanyCandidateLogin;
    } else {
      // Default to candidate practice if mode is not recognized
      return CandidateLogin;
    }
  }, [mode]);
  
  return <LoginComponent />;
}

// Dashboard Components
import { CompanyDashboard } from '@/pages/CompanyDashboard';
import CandidateDashboard from '@/components/configuration/CandidateDashboard';
import CandidateEvaluationReport from '@/components/evaluation/CandidateEvaluationReport';
import InterviewConfigurationResults from '@/components/configuration/InterviewConfigurationResults';
import InterviewResultsPage from '@/components/interview/InterviewResultsPage';
import { InterviewLayout } from '@/components/interview/InterviewLayout';

// Protected Route Component
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user } = useUser();
  const [, setLocation] = useLocation();

  // Debug logging
  console.log("ProtectedRoute: User:", user);
  console.log("ProtectedRoute: User type:", user?.userType);

  useEffect(() => {
    if (!user) {
      console.log("No user logged in, redirecting to login");
      setLocation("/login");
    }
  }, [user, setLocation]);

  if (!user) {
    console.log("ProtectedRoute: No user, returning null");
    return null;
  }

  console.log("ProtectedRoute: User authenticated, rendering children");
  return <>{children}</>;
}

// User Type Route Guard
function UserTypeRoute({ 
  children, 
  allowedUserType 
}: { 
  children: React.ReactNode;
  allowedUserType: 'company' | 'candidate';
}) {
  const { user } = useUser();
  const [, setLocation] = useLocation();
  const config = getModeConfig();

  useEffect(() => {
    if (user && user.userType !== allowedUserType) {
      // Redirect to appropriate dashboard based on user type and mode
      if (user.userType === 'company' && config.features.companyDashboard) {
        setLocation("/company-dashboard");
      } else if (config.features.candidateDashboard) {
        setLocation("/candidate-dashboard");
      } else {
        setLocation("/login");
      }
    }
  }, [user, allowedUserType, setLocation, config]);

  if (!user || user.userType !== allowedUserType) {
    return null;
  }

  return <>{children}</>;
}

// Mode Route Guard
function ModeRoute({ 
  children, 
  requiredMode 
}: { 
  children: React.ReactNode;
  requiredMode: 'candidate-practice' | 'company-interviewing';
}) {
  const config = getModeConfig();
  
  if (config.mode !== requiredMode) {
    return <NotFound />;
  }

  return <>{children}</>;
}

export function ModeAwareRouter() {
  const [isInitialized, setIsInitialized] = useState(false);
  const config = getModeConfig();
  const [, setLocation] = useLocation();

  // Debug logging
  console.log('ModeAwareRouter: Current mode config:', config);
  console.log('ModeAwareRouter: Current location:', window.location.pathname);

  // Wait for initialization to complete
  useEffect(() => {
    // Small delay to ensure all contexts are ready
    const timer = setTimeout(() => {
      setIsInitialized(true);
    }, 100);
    
    return () => clearTimeout(timer);
  }, []);

  // Redirect to login page if on root (since login is the entry point)
  useEffect(() => {
    if (window.location.pathname === '/') {
      setLocation('/login');
    }
  }, [setLocation]);

  // Don't render until initialized
  if (!isInitialized) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-center text-white">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p>Initializing...</p>
        </div>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <UserProvider>
        <InterviewProvider>
          <ConfigurationProvider>
            <CameraProvider>
              <ErrorBoundary>
                <Switch>
                  {/* Public Routes - Mode-specific login pages */}
                  <Route path="/login" component={ModeSpecificLogin} />
                
                {/* Candidate Dashboard - Available in both modes */}
                {config.features.candidateDashboard && (
                  <Route path="/candidate-dashboard">
                    <ProtectedRoute>
                      <UserTypeRoute allowedUserType="candidate">
                        <CandidateDashboard />
                      </UserTypeRoute>
                    </ProtectedRoute>
                  </Route>
                )}
                
                {/* Company Dashboard - Only in company-interviewing mode */}
                {config.features.companyDashboard && (
                  <>
                    <Route path="/company-dashboard">
                      <ProtectedRoute>
                        <UserTypeRoute allowedUserType="company">
                          <CompanyDashboard />
                        </UserTypeRoute>
                      </ProtectedRoute>
                    </Route>
                    <Route path="/company-dashboard/candidates">
                      <ProtectedRoute>
                        <UserTypeRoute allowedUserType="company">
                          <CompanyDashboard />
                        </UserTypeRoute>
                      </ProtectedRoute>
                    </Route>
                    <Route path="/company-dashboard/analytics">
                      <ProtectedRoute>
                        <UserTypeRoute allowedUserType="company">
                          <CompanyDashboard />
                        </UserTypeRoute>
                      </ProtectedRoute>
                    </Route>
                  </>
                )}
                
                {/* Interview Configuration - Available in both modes */}
                {config.features.interviewConfiguration && (
                  <Route path="/configure">
                    <ProtectedRoute>
                      <ConfigureInterview />
                    </ProtectedRoute>
                  </Route>
                )}
                
                {/* Interview Session - Available in both modes */}
                <Route path="/interview">
                  <ProtectedRoute>
                    <InterviewLayout />
                  </ProtectedRoute>
                </Route>
                
                {/* Candidate Evaluation Report - Available in company mode */}
                {config.features.companyDashboard && (
                  <Route path="/evaluation/:id">
                    <ProtectedRoute>
                      <UserTypeRoute allowedUserType="company">
                        <CandidateEvaluationReport />
                      </UserTypeRoute>
                    </ProtectedRoute>
                  </Route>
                )}
                
                {/* Tutorial Demo - Available in both modes */}
                <Route path="/tutorial">
                  <ProtectedRoute>
                    <TutorialDemo />
                  </ProtectedRoute>
                </Route>

                {/* Interview Results - Available for candidates */}
                <Route path="/results/:sessionId">
                  <ProtectedRoute>
                    <UserTypeRoute allowedUserType="candidate">
                      <InterviewResultsPage />
                    </UserTypeRoute>
                  </ProtectedRoute>
                </Route>

                {/* Test Routes - Development only */}
                {import.meta.env.DEV && (
                  <>
                    <Route path="/test-dynamic-params/:param1/:param2">
                      <ProtectedRoute>
                        <TestDynamicParams />
                      </ProtectedRoute>
                    </Route>
                  </>
                )}
                
                {/* Catch all - redirect to login */}
                <Route path="*">
                  {() => {
                    useEffect(() => {
                      setLocation('/login');
                    }, [setLocation]);
                    return null;
                  }}
                </Route>
              </Switch>
              </ErrorBoundary>
              
              <Toaster />
            </CameraProvider>
          </ConfigurationProvider>
        </InterviewProvider>
      </UserProvider>
    </TooltipProvider>
  );
}
