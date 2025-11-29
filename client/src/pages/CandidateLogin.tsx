import { useState, useEffect } from "react";
import { useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Clock, Calendar, Info, CheckCircle, ArrowRight, RefreshCw, Building, Sparkles, Shield, Users, Zap, Target, Award, Star, ArrowUpRight, User, Briefcase } from "lucide-react";
import { AutomatedReminder } from "@/components/interview/AutomatedReminder";
import { useToast } from "@/hooks/use-toast";
import webSocketService from "@/lib/websocketService";
import { WebSocketMessageTypeToServer, WebSocketMessageTypeFromServer, UserLoginDataToServer } from "@/lib/common";
import { useUser } from "@/contexts/UserContext";
import { useInterview } from '@/contexts/InterviewContext';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import CandidateSignupForm from "@/components/signup/CandidateSignupForm";
import { getModeConfig } from "@/lib/modeConfig";

export default function CandidateLogin() {
  const modeConfig = getModeConfig();
  const [activeTab, setActiveTab] = useState<'login' | 'signup'>('login');
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [userLocation, setUserLocation] = useState("");
  const [phone, setPhone] = useState("");
  const [skills, setSkills] = useState<string[]>([]);
  const [experience, setExperience] = useState(0);
  const [linkedinUrl, setLinkedinUrl] = useState("");
  const [githubUrl, setGithubUrl] = useState("");
  const [portfolioUrl, setPortfolioUrl] = useState("");
  
  const [, setLocation] = useLocation();
  const [isLoading, setIsLoading] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const { toast } = useToast();
  const { login, signup } = useUser();
  const { interviewDetails, setInterviewDetails } = useInterview();

  const handleSignupSuccess = (userData: any) => {
    // Store user data and redirect
    localStorage.setItem('userProfile', JSON.stringify(userData));
    toast({
      title: "Account Created Successfully!",
      description: "You can now sign in with your email and name.",
    });
    setActiveTab('login');
  };

  const handleBackToLogin = () => {
    setActiveTab('login');
  };

  // Reset form state when component mounts or when navigating back to login
  useEffect(() => {
    // Clear any existing user data from localStorage when on login page
    localStorage.removeItem('userProfile');
    
    // Reset all form state
    setActiveTab('login');
    setName("");
    setEmail("");
    setUserLocation("");
    setPhone("");
    setSkills([]);
    setExperience(0);
    setLinkedinUrl("");
    setGithubUrl("");
    setPortfolioUrl("");
  }, []); // Empty dependency array means this runs once on mount

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      // For candidate login, we'll use the existing login logic
      await login(name, email);
      
      toast({
        title: "Welcome Back!",
        description: `Welcome back, ${name}!`,
      });
      
      // Navigate to candidate dashboard
      setLocation("/candidate-dashboard");
    } catch (error) {
      toast({
        title: "Login Failed",
        description: "Please check your credentials and try again.",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const addSkill = () => {
    const skillInput = document.getElementById('skillInput') as HTMLInputElement;
    if (skillInput && skillInput.value.trim()) {
      setSkills([...skills, skillInput.value.trim()]);
      skillInput.value = '';
    }
  };

  const removeSkill = (index: number) => {
    setSkills(skills.filter((_, i) => i !== index));
  };

  const resetForm = () => {
    setActiveTab('login');
    setName("");
    setEmail("");
    setUserLocation("");
    setPhone("");
    setSkills([]);
    setExperience(0);
    setLinkedinUrl("");
    setGithubUrl("");
    setPortfolioUrl("");
    
    // Also clear localStorage
    localStorage.removeItem('userProfile');
  };

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
                {modeConfig.title}
              </h1>
              <p className="text-slate-300 text-lg font-medium">{modeConfig.description}</p>
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
                      <Users className="h-8 w-8 text-white" />
                    </div>
                    <CardTitle className="text-3xl font-bold bg-gradient-to-r from-white to-blue-200 bg-clip-text text-transparent">
                      {activeTab === 'login' ? 'Welcome Back' : 'Join HopeLoom'}
                    </CardTitle>
                    <p className="text-slate-300 text-base">
                      {activeTab === 'login' 
                        ? 'Sign in to access your personalized interview experience'
                        : 'Create your account and start your interview journey'
                      }
                    </p>
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
                          <Label htmlFor="name" className="text-slate-200 font-semibold text-sm">
                            Full Name
                          </Label>
                          <div className="relative">
                            <Input 
                              id="name"
                              placeholder="Enter your full name" 
                              value={name}
                              onChange={(e) => setName(e.target.value)}
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

                        <Button 
                          type="submit" 
                          disabled={isLoading || !name || !email}
                          className="w-full h-12 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold text-base transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98] shadow-lg hover:shadow-xl"
                        >
                          {isLoading ? (
                            <span className="flex items-center">
                              <RefreshCw className="w-5 h-5 mr-2 animate-spin" />
                              Signing In...
                            </span>
                          ) : (
                            <span className="flex items-center group">
                              Sign In
                              <ArrowRight className="ml-2 h-5 w-5 transition-transform duration-200 group-hover:translate-x-1" />
                            </span>
                          )}
                        </Button>
                      </form>
                    </TabsContent>

                    {/* Signup Tab */}
                    <TabsContent value="signup" className="space-y-6">
                      <CandidateSignupForm 
                        onSignupSuccess={handleSignupSuccess}
                        onBackToLogin={handleBackToLogin}
                      />
                    </TabsContent>
                  </Tabs>
                </CardContent>
                
                <CardFooter className="flex flex-col space-y-4 pt-6">
                  <div className="text-center w-full">
                    <Button
                      variant="outline"
                                              onClick={() => {
                          // Create a mock candidate user for testing
                          const mockUser = {
                            id: `mock-candidate-${Date.now()}`,
                            name: name || `Test Candidate`,
                            email: email || `test.candidate@example.com`,
                            userType: 'candidate' as const,
                            isLoggedIn: true,
                            createdAt: new Date(),
                            candidateDetails: {
                              skills: skills.length > 0 ? skills : ['React', 'TypeScript', 'Node.js'],
                              experience: experience || 3,
                              location: userLocation || 'San Francisco, CA',
                              phone: phone || '+1-555-0123',
                              linkedinUrl: linkedinUrl || 'https://linkedin.com/in/test-candidate',
                              githubUrl: githubUrl || 'https://github.com/test-candidate',
                              portfolioUrl: portfolioUrl || 'https://test-candidate.dev'
                            }
                          };
                          
                          // Store the mock user in localStorage
                          localStorage.setItem('userProfile', JSON.stringify(mockUser));
                          
                          // Show confirmation toast
                          toast({
                            title: "Configuration Mode Set",
                            description: "Creating interview configuration in Candidate mode",
                          });
                          
                          // Navigate to configure page
                          setLocation("/configure");
                        }}
                      className="w-full h-12 border-slate-200 hover:border-blue-300 hover:bg-blue-50 transition-all duration-200 group"
                      onMouseEnter={() => setIsHovered(true)}
                      onMouseLeave={() => setIsHovered(false)}
                    >
                      <div className="flex items-center justify-center space-x-2">
                        <Sparkles className={`w-5 h-5 transition-all duration-200 ${isHovered ? 'text-blue-600 scale-110' : 'text-slate-600'}`} />
                        <span>Create New Interview Configuration</span>
                        <ArrowUpRight className={`w-4 h-4 transition-all duration-200 ${isHovered ? 'translate-x-1 -translate-y-1' : ''}`} />
                      </div>
                    </Button>
                    <p className="text-xs text-slate-500 mt-2">
                      Set up a custom interview with your own questions and AI interviewers
                    </p>
                    
                    {/* Reset Button for Testing */}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={resetForm}
                      className="mt-2 text-xs text-slate-400 hover:text-slate-300 hover:bg-slate-700/50"
                    >
                      Reset Form
                    </Button>
                  </div>
                  
                  <div className="w-full pt-4 border-t border-slate-100">
                    <div className="text-xs text-center text-slate-500 space-y-1">
                      <p>By continuing, you agree to HopeLoom's Terms of Service and Privacy Policy.</p>
                      <p>Need help? Contact <a href="mailto:info@hopeloom.com" className="text-blue-600 hover:text-blue-700 hover:underline font-medium">info@hopeloom.com</a></p>
                    </div>
                  </div>
                </CardFooter>
              </Card>
            </div>
            
            {/* Right side content - Candidate Practice Features */}
            <div className="w-full lg:w-3/5 order-1 lg:order-2">
              <div className="space-y-8">
                {/* Feature highlights */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-600 rounded-2xl p-6 hover:border-blue-400/50 transition-all duration-300 group">
                    <div className="flex items-center mb-4">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center mr-4 group-hover:scale-110 transition-transform duration-300">
                        <Target className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="text-xl font-semibold text-white">Practice Interviews</h3>
                    </div>
                    <p className="text-slate-300 text-sm leading-relaxed">
                      Practice with AI-powered interviewers in realistic scenarios tailored to your skills and experience level.
                    </p>
                  </div>

                  <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-600 rounded-2xl p-6 hover:border-blue-400/50 transition-all duration-300 group">
                    <div className="flex items-center mb-4">
                      <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center mr-4 group-hover:scale-110 transition-transform duration-300">
                        <Award className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="text-xl font-semibold text-white">Skill Development</h3>
                    </div>
                    <p className="text-slate-300 text-sm leading-relaxed">
                      Improve your interview skills with detailed feedback and performance analytics.
                    </p>
                  </div>

                  <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-600 rounded-2xl p-6 hover:border-blue-400/50 transition-all duration-300 group">
                    <div className="flex items-center mb-4">
                      <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl flex items-center justify-center mr-4 group-hover:scale-110 transition-transform duration-300">
                        <Zap className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="text-xl font-semibold text-white">AI-Powered Feedback</h3>
                    </div>
                    <p className="text-slate-300 text-sm leading-relaxed">
                      Get instant, intelligent feedback on your responses and body language.
                    </p>
                  </div>

                  <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-600 rounded-2xl p-6 hover:border-blue-400/50 transition-all duration-300 group">
                    <div className="flex items-center mb-4">
                      <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-red-600 rounded-xl flex items-center justify-center mr-4 group-hover:scale-110 transition-transform duration-300">
                        <Clock className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="text-xl font-semibold text-white">Flexible Scheduling</h3>
                    </div>
                    <p className="text-slate-300 text-sm leading-relaxed">
                      Practice anytime, anywhere with 24/7 availability and customizable interview durations.
                    </p>
                  </div>
                </div>

                {/* Call to action */}
                <div className="text-center">
                  <h2 className="text-3xl font-bold text-white mb-4">
                    Ready to Ace Your Next Interview?
                  </h2>
                  <p className="text-slate-300 text-lg mb-6 max-w-2xl mx-auto">
                    Join thousands of candidates who have improved their interview skills and landed their dream jobs with HopeLoom's AI-powered practice platform.
                  </p>
                  <div className="flex flex-col sm:flex-row gap-4 justify-center">
                    <Button 
                      onClick={() => setActiveTab('signup')}
                      className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-8 py-3 text-lg font-semibold"
                    >
                      Start Practicing Today
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
