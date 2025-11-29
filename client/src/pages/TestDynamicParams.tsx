import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";
import { useLocation } from "wouter";

export default function TestDynamicParams() {
  const [selectedRole, setSelectedRole] = useState('ml-engineer');
  const [candidateName, setCandidateName] = useState('Varsha');
  const [company, setCompany] = useState('Acme Corp');
  const { toast } = useToast();
  const [, setLocation] = useLocation();

  // Function to update URL and go to login page
  const goToLogin = () => {
    // Construct params
    const params = new URLSearchParams();
    if (candidateName) params.append('name', candidateName);
    if (selectedRole) params.append('role', selectedRole);
    if (company) params.append('company', company);

    // Show toast with the URL we're constructing
    toast({
      title: "Testing Interview Details",
      description: `Loading login with: name=${candidateName}, role=${selectedRole}, company=${company}`,
      duration: 3000,
    });

    // Navigate to login page with params
    const queryString = params.toString();
    setLocation(`/login?${queryString}`);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-6 bg-neutral-50">
      <div className="max-w-md w-full bg-white p-6 rounded-xl shadow-md space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-neutral-800">Test Dynamic Parameters</h1>
          <p className="text-neutral-600 mt-1">
            Select options to test different interview configurations
          </p>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">
              Candidate Name
            </label>
            <input
              type="text"
              value={candidateName}
              onChange={(e) => setCandidateName(e.target.value)}
              className="w-full p-2 border border-neutral-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              placeholder="Enter candidate name"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">
              Company
            </label>
            <input
              type="text"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              className="w-full p-2 border border-neutral-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              placeholder="Enter company name"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">
              Interview Role
            </label>
            
            <Tabs defaultValue={selectedRole} onValueChange={setSelectedRole} className="w-full">
              <TabsList className="grid grid-cols-2 mb-2">
                <TabsTrigger value="ml-engineer">ML Engineer</TabsTrigger>
                <TabsTrigger value="data-scientist">Data Scientist</TabsTrigger>
              </TabsList>
              <TabsList className="grid grid-cols-2 mb-2">
                <TabsTrigger value="frontend-engineer">Frontend Dev</TabsTrigger>
                <TabsTrigger value="backend-engineer">Backend Dev</TabsTrigger>
              </TabsList>
              <TabsList className="grid grid-cols-2">
                <TabsTrigger value="devops-engineer">DevOps</TabsTrigger>
                <TabsTrigger value="product-manager">Product</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </div>

        <Button 
          onClick={goToLogin}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-md"
        >
          Test Login Page
        </Button>
      </div>
    </div>
  );
}