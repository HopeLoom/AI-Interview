import { useState, useEffect } from "react";
import { useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowRight, RefreshCw, User, Mail, Lock, Target, Shield, Users, Zap, Info } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useUser } from "@/contexts/UserContext";
import { useInterview } from '@/contexts/InterviewContext';
import { getModeConfig } from "@/lib/modeConfig";
import webSocketService from "@/lib/websocketService";
import { WebSocketMessageTypeToServer, WebSocketMessageTypeFromServer, UserLoginDataToServer } from "@/lib/common";

export default function CompanyCandidateLogin() {
  const modeConfig = getModeConfig();
  const [email, setEmail] = useState("");
  const [interviewCode, setInterviewCode] = useState("");
  
  const [, setLocation] = useLocation();
  const [isLoading, setIsLoading] = useState(false);
  const [isWebSocketConnected, setIsWebSocketConnected] = useState(false);
  const [loginResponse, setLoginResponse] = useState<any>(null);
  const { toast } = useToast();
  const { login } = useUser();
  const { interviewDetails, setInterviewDetails } = useInterview();

  // Check websocket connection status and handle login responses
  useEffect(() => {
    // Check if websocket is connected
    const checkConnection = () => {
      // We'll check connection status when needed
      setIsWebSocketConnected(true); // For now, assume connected
    };

    // Listen for websocket connection events
    const handleConnection = () => {
      setIsWebSocketConnected(true);
    };

    const handleError = () => {
      setIsWebSocketConnected(false);
    };

    // Set up websocket event listeners
    webSocketService.on(WebSocketMessageTypeFromServer.CONNECTION, handleConnection);
    webSocketService.on(WebSocketMessageTypeFromServer.ERROR, handleError);

    // Check initial connection status
    checkConnection();

    // Cleanup
    return () => {
      webSocketService.off(WebSocketMessageTypeFromServer.CONNECTION, handleConnection);
      webSocketService.off(WebSocketMessageTypeFromServer.ERROR, handleError);
    };
  }, []);

  // Reset form state when component mounts
  useEffect(() => {
    // Reset form state
    setEmail("");
    setInterviewCode("");
  }, []); // Empty dependency array means this runs once on mount

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email || !interviewCode) {
      toast({
        title: "Missing Information",
        description: "Please enter both your email and interview code.",
        variant: "destructive"
      });
      return;
    }

    setIsLoading(true);

    try {
      // Step 1: Validate interview code with backend
      toast({
        title: "Validating Code...",
        description: "Verifying your interview code with the company.",
      });

      const apiClient = (await import("@/services/apiClient")).apiClient;

      // Call join-by-code endpoint to validate code and get company details
      const response = await apiClient.post("/api/configurations/join-by-code", {
        invitation_code: interviewCode.trim().toUpperCase(),
        candidate_id: email, // Using email as candidate ID for now
        candidate_email: email
      });

      if (!response.data.success) {
        throw new Error(response.data.message || "Invalid invitation code");
      }

      const { configuration, company, session_id } = response.data;

      // Extract company details from response
      const companyId = company?.id || 'unknown_company';
      const companyName = company?.name || 'Unknown Company';
      const configurationId = configuration?.id || response.data.configuration_id;

      console.log("Interview code validated successfully", { companyId, companyName, configurationId });

      // Step 2: Send WebSocket login if connected
      if (isWebSocketConnected) {
        console.log("WebSocket connected, sending login message to backend...");

        const loginData: UserLoginDataToServer = {
          name: email, // Using email as name for simplicity
          email: email,
          id: email
        };

        // Send login message to backend
        webSocketService.sendMessage(email, WebSocketMessageTypeToServer.USER_LOGIN, loginData);
      }

      // Step 3: Login with real company data
      await login(email, email, {
        companyId,
        companyName,
        interviewSessionId: session_id,
        configurationId
      });

      toast({
        title: "Login Successful!",
        description: `Welcome to ${companyName}'s interview!`,
      });

      // Step 4: Navigate to tutorial
      setTimeout(() => {
        console.log('Navigating to tutorial...');
        setLocation("/tutorial");
      }, 100);

    } catch (error: any) {
      console.error('Login failed:', error);

      const errorMessage = error.response?.data?.detail || error.message || "Invalid invitation code";

      toast({
        title: "Login Failed",
        description: errorMessage,
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const resetForm = () => {
    setEmail("");
    setInterviewCode("");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-6xl mx-auto flex flex-col lg:flex-row gap-8 items-center">
        
        {/* Left side - Login Form */}
        <div className="w-full lg:w-2/5 order-2 lg:order-1">
          <Card className="w-full max-w-md mx-auto border-0 shadow-2xl bg-slate-800/80 backdrop-blur-sm border-slate-600">
            <CardHeader className="text-center">
              <div className="mx-auto w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center mb-4 shadow-lg">
                <User className="h-8 w-8 text-white" />
              </div>
              <CardTitle className="text-3xl font-bold bg-gradient-to-r from-white to-blue-200 bg-clip-text text-transparent">
                Company Interview Login
              </CardTitle>
              <p className="text-slate-300">
                Enter your credentials to access your scheduled interview
              </p>
              {/* Connection Status Indicator */}
              <div className="flex items-center justify-center gap-2 mt-2">
                <div className={`w-2 h-2 rounded-full ${isWebSocketConnected ? 'bg-green-400' : 'bg-red-400'}`}></div>
                <span className={`text-xs ${isWebSocketConnected ? 'text-green-400' : 'text-red-400'}`}>
                  {isWebSocketConnected ? 'Connected to Server' : 'Offline Mode'}
                </span>
              </div>
            </CardHeader>
            
            <CardContent>
              <form onSubmit={handleLogin} className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-slate-200 font-semibold text-sm">Email Address *</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <Input
                      id="email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="Enter your email address"
                      required
                      className="pl-10 h-12 border-slate-600 bg-slate-700 text-white placeholder:text-slate-400 focus:border-blue-400 focus:ring-blue-400/20 focus:bg-slate-600 transition-all duration-200 text-base"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="interview-code" className="text-slate-200 font-semibold text-sm">Interview Code *</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <Input
                      id="interview-code"
                      value={interviewCode}
                      onChange={(e) => setInterviewCode(e.target.value)}
                      placeholder="Enter your interview code"
                      required
                      className="pl-10 h-12 border-slate-600 bg-slate-700 text-white placeholder:text-slate-400 focus:border-blue-400 focus:ring-blue-400/20 focus:bg-slate-600 transition-all duration-200 text-base"
                    />
                  </div>
                </div>

                <Button type="submit" className="w-full h-12 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold text-base shadow-lg hover:shadow-xl transition-all duration-200 transform hover:-translate-y-0.5" disabled={isLoading}>
                  {isLoading ? (
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <ArrowRight className="h-4 w-4 mr-2" />
                  )}
                  {isWebSocketConnected ? 'Authenticate & Start Interview' : 'Start Interview (Offline)'}
                </Button>
              </form>
            </CardContent>
            
            <CardFooter className="flex flex-col space-y-4">
              <div className="text-center w-full">
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
        
        {/* Right side content - Company Interview Features */}
        <div className="w-full lg:w-3/5 order-1 lg:order-2">
          <div className="space-y-8">
            {/* Feature highlights */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10 hover:border-blue-400/30 transition-all duration-300 group">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                  <Target className="h-6 w-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">Focused Interview Experience</h3>
                <p className="text-slate-300 text-sm">
                  Take your scheduled company interview with a streamlined, professional interface designed for real screening sessions.
                </p>
              </div>
              
              <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10 hover:border-blue-400/30 transition-all duration-300 group">
                <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                  <Shield className="h-6 w-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">Secure & Professional</h3>
                <p className="text-slate-300 text-sm">
                  Your interview session is secure and monitored, ensuring a fair and professional screening process.
                </p>
              </div>
              
              <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10 hover:border-blue-400/30 transition-all duration-300 group">
                <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                  <Users className="h-6 w-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">Company-Specific Questions</h3>
                <p className="text-slate-300 text-sm">
                  Answer questions tailored to the specific role and company you're interviewing for.
                </p>
              </div>
              
              <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10 hover:border-blue-400/30 transition-all duration-300 group">
                <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-red-600 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                  <Zap className="h-6 w-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">Real-Time Evaluation</h3>
                <p className="text-slate-300 text-sm">
                  Get immediate feedback and evaluation from AI interviewers trained on company-specific criteria.
                </p>
              </div>
            </div>
            
            {/* How it works */}
            <div className="bg-white/5 backdrop-blur-sm rounded-xl p-8 border border-white/10">
              <h2 className="text-2xl font-bold text-white mb-6 text-center">How Your Company Interview Works</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center mx-auto mb-4">
                    <span className="text-2xl font-bold text-white">1</span>
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">Enter Credentials</h3>
                  <p className="text-slate-300 text-sm">
                    Use your email and the interview code provided by the company to access your session.
                  </p>
                </div>
                
                <div className="text-center">
                  <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4">
                    <span className="text-2xl font-bold text-white">2</span>
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">Take Your Interview</h3>
                  <p className="text-slate-300 text-sm">
                    Answer company-specific questions in a professional, AI-powered interview environment.
                  </p>
                </div>
                
                <div className="text-center">
                  <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full flex items-center justify-center mx-auto mb-4">
                    <span className="text-2xl font-bold text-white">3</span>
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">Get Evaluated</h3>
                  <p className="text-slate-300 text-sm">
                    Receive comprehensive evaluation and feedback based on company requirements.
                  </p>
                </div>
              </div>
            </div>
            
            {/* Important notes */}
            <div className="bg-gradient-to-r from-blue-500/10 to-indigo-500/10 backdrop-blur-sm rounded-xl p-6 border border-blue-400/20">
              <div className="flex items-start space-x-3">
                <Info className="h-6 w-6 text-blue-400 mt-1 flex-shrink-0" />
                <div>
                  <h3 className="text-lg font-semibold text-white mb-2">Important Information</h3>
                  <ul className="text-slate-300 text-sm space-y-1">
                    <li>• This is a professional screening interview - please treat it seriously</li>
                    <li>• Your responses will be evaluated and shared with the hiring company</li>
                    <li>• Ensure you have a stable internet connection and quiet environment</li>
                    <li>• The interview will be recorded for evaluation purposes</li>
                    <li>• Contact the company directly if you have any questions about the role</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
