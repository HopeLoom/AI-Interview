import { useEffect } from "react";
import { useLocation } from "wouter";
import { useUser } from "@/contexts/UserContext";

export default function Home() {
  const { user } = useUser();
  const [, setLocation] = useLocation();

  useEffect(() => {
    if (user) {
      // Redirect based on user type
      if (user.userType === 'company') {
        setLocation("/company-dashboard");
      } else {
        setLocation("/candidate-dashboard");
      }
    } else {
      // If no user, redirect to login
      setLocation("/login");
    }
  }, [user, setLocation]);

  // Show loading while redirecting
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
      <div className="text-center">
        <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-white text-lg">Redirecting to your dashboard...</p>
      </div>
    </div>
  );
}
