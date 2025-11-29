import React, { useState, useRef, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { 
  User, 
  Upload, 
  FileText, 
  CheckCircle, 
  AlertCircle, 
  RefreshCw, 
  ArrowRight,
  Briefcase,
  MapPin,
  Phone,
  Linkedin,
  Github,
  ExternalLink
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { CandidateService, CandidateSignupData } from "@/services/candidateService";

interface CandidateSignupFormProps {
  onSignupSuccess: (userData: any) => void;
  onBackToLogin: () => void;
}

export default function CandidateSignupForm({ onSignupSuccess, onBackToLogin }: CandidateSignupFormProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState<'form' | 'resume' | 'processing' | 'success'>('form');
  
  // Form state
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [location, setLocation] = useState("");
  
  // Candidate-specific fields
  const [skills, setSkills] = useState<string[]>([]);
  const [experience, setExperience] = useState(0);
  const [linkedinUrl, setLinkedinUrl] = useState("");
  const [githubUrl, setGithubUrl] = useState("");
  const [portfolioUrl, setPortfolioUrl] = useState("");
  
  // Resume handling
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [resumePreview, setResumePreview] = useState<string>("");
  const [extractedInfo, setExtractedInfo] = useState<any>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

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

  const handleResumeUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Validate file type
      if (!file.name.toLowerCase().endsWith('.pdf') && !file.name.toLowerCase().endsWith('.docx') && !file.name.toLowerCase().endsWith('.doc')) {
        toast({
          title: "Invalid File Type",
          description: "Please upload a PDF, DOCX, or DOC file.",
          variant: "destructive"
        });
        return;
      }
      
      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        toast({
          title: "File Too Large",
          description: "Please upload a file smaller than 10MB.",
          variant: "destructive"
        });
        return;
      }
      
      setResumeFile(file);
      
      // Create preview URL
      const reader = new FileReader();
      reader.onload = (e) => {
        setResumePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
      
      // Extract information from resume
      extractResumeInfo(file);
    }
  };

  const extractResumeInfo = async (file: File) => {
    try {
      const formData = new FormData();
      formData.append('resume', file);
      
      // Simulate resume parsing (replace with actual API call)
      setExtractedInfo({
        skills: ['JavaScript', 'React', 'Node.js'],
        experience: 3,
        education: 'Bachelor\'s in Computer Science'
      });
      
      toast({
        title: "Resume Processed",
        description: "Information extracted successfully!",
      });
    } catch (error) {
      toast({
        title: "Resume Processing Failed",
        description: "Could not extract information from resume.",
        variant: "destructive"
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!name || !email || !phone || !location) {
      toast({
        title: "Missing Information",
        description: "Please fill in all required fields.",
        variant: "destructive"
      });
      return;
    }
    
    setIsLoading(true);
    
    try {
      const signupData: CandidateSignupData = {
        name,
        email,
        userType: 'candidate',
        phone,
        location,
        skills,
        experience,
        linkedinUrl,
        githubUrl,
        portfolioUrl,
        resumeFile: resumeFile || undefined
      };
      
      const result = await CandidateService.completeCandidateSignup(signupData);
      
      if (result.success) {
        setCurrentStep('success');
        onSignupSuccess(result.profile);
      } else {
        toast({
          title: "Signup Failed",
          description: result.message || "Something went wrong. Please try again.",
          variant: "destructive"
        });
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

  if (currentStep === 'resume') {
    return (
      <Card className="w-full max-w-md mx-auto border-0 shadow-2xl bg-slate-800/80 backdrop-blur-sm border-slate-600">
        <CardHeader className="text-center">
          <div className="mx-auto w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center mb-4 shadow-lg">
            <FileText className="h-8 w-8 text-white" />
          </div>
          <CardTitle className="text-2xl font-bold bg-gradient-to-r from-white to-blue-200 bg-clip-text text-transparent">Upload Your Resume</CardTitle>
          <p className="text-slate-300">Help us understand your background better</p>
        </CardHeader>
        
        <CardContent className="space-y-6">
          <div className="space-y-4">
            <div className="border-2 border-dashed border-slate-600 rounded-lg p-6 text-center hover:border-blue-400 transition-colors">
              <Upload className="mx-auto h-12 w-12 text-slate-400 mb-4" />
              <p className="text-slate-300 mb-2">Drop your resume here, or click to browse</p>
              <p className="text-sm text-slate-400">PDF, DOCX, or DOC (max 10MB)</p>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleResumeUpload}
                accept=".pdf,.docx,.doc"
                className="hidden"
              />
              <Button
                onClick={() => fileInputRef.current?.click()}
                className="mt-4 bg-blue-600 hover:bg-blue-700"
              >
                Choose File
              </Button>
            </div>
            
            {resumeFile && (
              <div className="bg-slate-700/50 p-4 rounded-lg border border-slate-600">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <FileText className="h-5 w-5 text-blue-400" />
                    <span className="text-slate-200 font-medium">{resumeFile.name}</span>
                  </div>
                  <Badge variant="secondary" className="bg-green-600 text-white">
                    {(resumeFile.size / 1024 / 1024).toFixed(2)} MB
                  </Badge>
                </div>
              </div>
            )}
          </div>
          
          {extractedInfo && (
            <div className="bg-slate-700/50 p-4 rounded-lg border border-slate-600">
              <h4 className="font-semibold text-slate-200 mb-2">Extracted Information:</h4>
              <div className="space-y-2 text-sm">
                <p><span className="text-slate-400">Skills:</span> {extractedInfo.skills.join(', ')}</p>
                <p><span className="text-slate-400">Experience:</span> {extractedInfo.experience} years</p>
                <p><span className="text-slate-400">Education:</span> {extractedInfo.education}</p>
              </div>
            </div>
          )}
        </CardContent>
        
        <CardFooter className="flex space-x-3">
          <Button
            onClick={() => setCurrentStep('form')}
            className="flex-1 bg-slate-700 border border-slate-600 hover:border-blue-400 hover:bg-slate-600"
          >
            Back
          </Button>
          <Button
            onClick={() => setCurrentStep('processing')}
            className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
            disabled={!resumeFile}
          >
            Continue
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </CardFooter>
      </Card>
    );
  }

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
              Processing resume and creating candidate profile...
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
            Your account has been created successfully. You can now sign in with your email and name.
          </p>
          <div className="bg-slate-700/50 p-4 rounded-lg border border-slate-600">
            <p className="text-sm font-medium text-green-300">Next Steps:</p>
            <p className="text-sm text-slate-200 mt-1">
              Start practicing interviews with AI-powered simulations
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
          <User className="h-8 w-8 text-white" />
        </div>
        <CardTitle className="text-3xl font-bold bg-gradient-to-r from-white to-blue-200 bg-clip-text text-transparent">Create Your Account</CardTitle>
        <p className="text-slate-300">
          Join HopeLoom to practice interviews and improve your skills
        </p>
      </CardHeader>
      
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name" className="text-slate-200 font-semibold text-sm">Full Name *</Label>
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
              <Label htmlFor="location" className="text-slate-200 font-semibold text-sm">Location *</Label>
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
              <Label htmlFor="experience" className="text-slate-200 font-semibold text-sm">Years of Experience</Label>
              <Select value={experience.toString()} onValueChange={(value) => setExperience(parseInt(value))}>
                <SelectTrigger className="h-12 border-slate-600 bg-slate-700 text-white focus:border-blue-400 focus:ring-blue-400/20 focus:bg-slate-600">
                  <SelectValue placeholder="Select experience level" />
                </SelectTrigger>
                <SelectContent className="bg-slate-700 border-slate-600">
                  <SelectItem value="0" className="text-white hover:bg-slate-600">0-1 years (Entry Level)</SelectItem>
                  <SelectItem value="1" className="text-white hover:bg-slate-600">1-3 years (Junior)</SelectItem>
                  <SelectItem value="3" className="text-white hover:bg-slate-600">3-5 years (Mid Level)</SelectItem>
                  <SelectItem value="5" className="text-white hover:bg-slate-600">5-8 years (Senior)</SelectItem>
                  <SelectItem value="8" className="text-white hover:bg-slate-600">8+ years (Expert)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="skills" className="text-slate-200 font-semibold text-sm">Skills</Label>
              <div className="space-y-2">
                <div className="flex space-x-2">
                  <Input
                    id="skillInput"
                    placeholder="Add a skill"
                    className="flex-1 h-12 border-slate-600 bg-slate-700 text-white placeholder:text-slate-400 focus:border-blue-400 focus:ring-blue-400/20 focus:bg-slate-600"
                  />
                  <Button
                    type="button"
                    onClick={addSkill}
                    className="h-12 px-4 bg-blue-600 hover:bg-blue-700"
                  >
                    Add
                  </Button>
                </div>
                {skills.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {skills.map((skill, index) => (
                      <Badge
                        key={index}
                        variant="secondary"
                        className="bg-blue-600 text-white hover:bg-blue-700"
                      >
                        {skill}
                        <button
                          type="button"
                          onClick={() => removeSkill(index)}
                          className="ml-2 hover:text-red-200"
                        >
                          ×
                        </button>
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="linkedin" className="text-slate-200 font-semibold text-sm">LinkedIn Profile</Label>
              <div className="relative">
                <Linkedin className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  id="linkedin"
                  type="url"
                  value={linkedinUrl}
                  onChange={(e) => setLinkedinUrl(e.target.value)}
                  placeholder="https://linkedin.com/in/username"
                  className="pl-10 h-12 border-slate-600 bg-slate-700 text-white placeholder:text-slate-400 focus:border-blue-400 focus:ring-blue-400/20 focus:bg-slate-600 transition-all duration-200 text-base"
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="github" className="text-slate-200 font-semibold text-sm">GitHub Profile</Label>
              <div className="relative">
                <Github className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  id="github"
                  type="url"
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
                  placeholder="https://github.com/username"
                  className="pl-10 h-12 border-slate-600 bg-slate-700 text-white placeholder:text-slate-400 focus:border-blue-400 focus:ring-blue-400/20 focus:bg-slate-600 transition-all duration-200 text-base"
                />
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="portfolio" className="text-slate-200 font-semibold text-sm">Portfolio Website</Label>
            <div className="relative">
              <ExternalLink className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                id="portfolio"
                type="url"
                value={portfolioUrl}
                onChange={(e) => setPortfolioUrl(e.target.value)}
                placeholder="https://yourportfolio.com"
                className="pl-10 h-12 border-slate-600 bg-slate-700 text-white placeholder:text-slate-400 focus:border-blue-400 focus:ring-blue-400/20 focus:bg-slate-600 transition-all duration-200 text-base"
              />
            </div>
          </div>

          <Button type="submit" className="w-full h-12 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold text-base shadow-lg hover:shadow-xl transition-all duration-200 transform hover:-translate-y-0.5" disabled={isLoading}>
            {isLoading ? (
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <User className="h-4 w-4 mr-2" />
            )}
            Create Candidate Account
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
