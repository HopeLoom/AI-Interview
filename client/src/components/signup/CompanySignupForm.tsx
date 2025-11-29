import React, { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { 
  Building, 
  CheckCircle, 
  RefreshCw, 
  Globe,
  MapPin,
  Phone,
  User
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { CompanyService, CompanySignupData } from "@/services/companyService";

interface CompanySignupFormProps {
  onSignupSuccess: (userData: any) => void;
  onBackToLogin: () => void;
}

export default function CompanySignupForm({ onSignupSuccess, onBackToLogin }: CompanySignupFormProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState<'form' | 'processing' | 'success'>('form');
  
  // Form state
  const [companyName, setCompanyName] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [location, setLocation] = useState("");
  
  // Company-specific fields
  const [industry, setIndustry] = useState("");
  const [companySize, setCompanySize] = useState("");
  const [website, setWebsite] = useState("");
  const [description, setDescription] = useState("");
  
  // Options from service
  const [industryOptions, setIndustryOptions] = useState<string[]>([]);
  const [companySizeOptions, setCompanySizeOptions] = useState<string[]>([]);
  
  const { toast } = useToast();

  // Fetch industry and company size options when component mounts
  useEffect(() => {
    const fetchOptions = async () => {
      try {
        const [industries, sizes] = await Promise.all([
                  CompanyService.getIndustryOptions(),
        CompanyService.getCompanySizeOptions()
        ]);
        setIndustryOptions(industries);
        setCompanySizeOptions(sizes);
      } catch (error) {
        console.error('Failed to fetch options:', error);
        // Fallback to default options
        setIndustryOptions(['Technology', 'Healthcare', 'Finance', 'Education', 'Other']);
        setCompanySizeOptions(['1-10', '11-50', '51-200', '201-500', '500+']);
      }
    };

    fetchOptions();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!companyName || !name || !email || !phone || !location || !industry || !companySize) {
      toast({
        title: "Missing Information",
        description: "Please fill in all required fields.",
        variant: "destructive"
      });
      return;
    }
    
    setIsLoading(true);
    
    try {
      // Create company signup data
      const companyData: CompanySignupData = {
        name: companyName,
        email,
        userType: 'company',
        industry,
        size: companySize,
        location,
        website,
        description
      };

      // Use the CompanySignupService to register the company
      const result = await CompanyService.completeCompanySignup(companyData);
      
      if (result.success) {
        // Show success and call the callback
        setCurrentStep('success');
        onSignupSuccess({ 
          name: companyName, 
          email, 
          userType: 'company',
          companyId: result.company_id 
        });
      } else {
        throw new Error(result.message || 'Company signup failed');
      }
      
    } catch (error) {
      toast({
        title: "Signup Error",
        description: "An unexpected error occurred. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (currentStep === 'processing') {
    return (
      <Card className="w-full max-w-md mx-auto border-0 shadow-2xl bg-slate-800/80 backdrop-blur-sm border-slate-600">
        <CardHeader className="text-center">
          <div className="mx-auto w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center mb-4 shadow-lg">
            <RefreshCw className="h-8 w-8 text-white animate-spin" />
          </div>
          <CardTitle className="text-2xl font-bold bg-gradient-to-r from-white to-blue-200 bg-clip-text text-transparent">Creating Your Account</CardTitle>
          <p className="text-slate-300">Please wait while we process your information...</p>
        </CardHeader>
        
        <CardContent className="text-center">
          <div className="space-y-4">
            <div className="flex items-center justify-center space-x-2">
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
            <p className="text-sm text-slate-400">
              Setting up company account and workspace...
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (currentStep === 'success') {
    return (
      <Card className="w-full max-w-md mx-auto border-0 shadow-2xl bg-slate-800/80 backdrop-blur-sm border-slate-600">
        <CardHeader className="text-center">
          <div className="mx-auto w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center mb-4 shadow-lg">
            <CheckCircle className="h-8 w-8 text-white" />
          </div>
          <CardTitle className="text-2xl font-bold bg-gradient-to-r from-green-300 to-emerald-200 bg-clip-text text-transparent">Account Created!</CardTitle>
          <p className="text-green-300">Welcome to HopeLoom!</p>
        </CardHeader>
        
        <CardContent className="text-center">
          <p className="text-slate-300 mb-4">
            Your company account has been created successfully. You can now sign in with your email and name.
          </p>
          <div className="bg-slate-700/50 p-4 rounded-lg border border-slate-600">
            <p className="text-sm font-medium text-green-300">Next Steps:</p>
            <p className="text-sm text-slate-200 mt-1">
              Begin screening candidates with custom interview configurations
            </p>
          </div>
        </CardContent>
        
        <CardFooter>
          <Button
            onClick={onBackToLogin}
            className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white"
          >
            Go to Sign In
          </Button>
        </CardFooter>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-2xl mx-auto border-0 shadow-2xl bg-slate-800/80 backdrop-blur-sm border-slate-600">
      <CardHeader className="text-center">
        <div className="mx-auto w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center mb-4 shadow-lg">
          <Building className="h-8 w-8 text-white" />
        </div>
        <CardTitle className="text-3xl font-bold bg-gradient-to-r from-white to-blue-200 bg-clip-text text-transparent">Create Company Account</CardTitle>
        <p className="text-slate-300">
          Set up your company workspace to screen candidates efficiently
        </p>
      </CardHeader>
      
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="company-name" className="text-slate-200 font-semibold text-sm">Company Name *</Label>
            <Input
              id="company-name"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="Enter your company name"
              required
              className="h-12 border-slate-600 bg-slate-700 text-white placeholder:text-slate-400 focus:border-blue-400 focus:ring-blue-400/20 focus:bg-slate-600 transition-all duration-200 text-base"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name" className="text-slate-200 font-semibold text-sm">Your Name *</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter your full name"
                required
                className="h-12 border-slate-600 bg-slate-700 text-white placeholder:text-slate-400 focus:border-blue-400 focus:ring-blue-400/20 focus:bg-slate-600 transition-all duration-200 text-base"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="email" className="text-slate-200 font-semibold text-sm">Email Address *</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                required
                className="h-12 border-slate-600 bg-slate-700 text-white placeholder:text-slate-400 focus:border-blue-400 focus:ring-blue-400/20 focus:bg-slate-600 transition-all duration-200 text-base"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="phone" className="text-slate-200 font-semibold text-sm">Phone Number *</Label>
              <div className="relative">
                <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  id="phone"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="Enter your phone number"
                  required
                  className="pl-10 h-12 border-slate-600 bg-slate-700 text-white placeholder:text-slate-400 focus:border-blue-400 focus:ring-blue-400/20 focus:bg-slate-600 transition-all duration-200 text-base"
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="location" className="text-slate-200 font-semibold text-sm">Company Location *</Label>
              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  id="location"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="City, State/Country"
                  required
                  className="pl-10 h-12 border-slate-600 bg-slate-700 text-white placeholder:text-slate-400 focus:border-blue-400 focus:ring-blue-400/20 focus:bg-slate-600 transition-all duration-200 text-base"
                />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="industry" className="text-slate-200 font-semibold text-sm">Industry *</Label>
              <Select value={industry} onValueChange={setIndustry}>
                <SelectTrigger className="h-12 border-slate-600 bg-slate-700 text-white focus:border-blue-400 focus:ring-blue-400/20 focus:bg-slate-600">
                  <SelectValue placeholder="Select industry" />
                </SelectTrigger>
                <SelectContent className="bg-slate-700 border-slate-600">
                  {industryOptions.map((option) => (
                    <SelectItem key={option} value={option.toLowerCase()} className="text-white hover:bg-slate-600">
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="company-size" className="text-slate-200 font-semibold text-sm">Company Size *</Label>
              <Select value={companySize} onValueChange={setCompanySize}>
                <SelectTrigger className="h-12 border-slate-600 bg-slate-700 text-white focus:border-blue-400 focus:ring-blue-400/20 focus:bg-slate-600">
                  <SelectValue placeholder="Select company size" />
                </SelectTrigger>
                <SelectContent className="bg-slate-700 border-slate-600">
                  {companySizeOptions.map((option) => (
                    <SelectItem key={option} value={option} className="text-white hover:bg-slate-600">
                      {option} {option === '1-10' ? 'employees' : option === '5000+' ? 'employees' : 'employees'}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="company-website" className="text-slate-200 font-semibold text-sm">Company Website</Label>
              <div className="relative">
                <Globe className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  id="company-website"
                  type="url"
                  value={website}
                  onChange={(e) => setWebsite(e.target.value)}
                  placeholder="https://company.com"
                  className="pl-10 h-12 border-slate-600 bg-slate-700 text-white placeholder:text-slate-400 focus:border-blue-400 focus:ring-blue-400/20 focus:bg-slate-600 transition-all duration-200 text-base"
                />
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="company-description" className="text-slate-200 font-semibold text-sm">Company Description</Label>
            <textarea
              id="company-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of your company and what you do..."
              className="w-full px-3 py-2 border border-slate-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent bg-slate-700 text-white placeholder:text-slate-400"
              rows={3}
            />
          </div>

          <Button type="submit" className="w-full h-12 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold text-base shadow-lg hover:shadow-xl transition-all duration-200 transform hover:-translate-y-0.5" disabled={isLoading}>
            {isLoading ? (
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Building className="h-4 w-4 mr-2" />
            )}
            Create Company Account
          </Button>
        </form>
      </CardContent>
      
      <CardFooter className="flex flex-col space-y-4">
        <div className="text-center w-full">
          <Button
            onClick={onBackToLogin}
            className="w-full h-12 bg-slate-700 border border-slate-600 hover:border-blue-400 hover:bg-slate-600 text-slate-200 hover:text-white transition-all duration-200"
          >
            Back to Sign In
          </Button>
        </div>
        
        <div className="w-full pt-4 border-t border-slate-600">
          <div className="text-xs text-center text-slate-400 space-y-1">
            <p>By continuing, you agree to HopeLoom's Terms of Service and Privacy Policy.</p>
            <p>Need help? Contact <a href="mailto:info@hopeloom.com" className="text-blue-400 hover:text-blue-300 hover:underline font-medium">info@hopeloom.com</a></p>
          </div>
        </div>
      </CardFooter>
    </Card>
  );
}
