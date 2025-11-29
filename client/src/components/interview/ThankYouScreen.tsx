import { Button } from "@/components/ui/button";
import { CheckCircle, Home, Download, Share2 } from "lucide-react";
import { useLocation } from "wouter";
import { useInterview } from "@/contexts/InterviewContext";

interface ThankYouScreenProps {
  isVisible: boolean;
  onClose?: () => void;
  interviewDuration?: string;
  role?: string;
  company?: string;
}

export function ThankYouScreen({ 
  isVisible, 
  onClose, 
  interviewDuration,
  role,
  company
}: ThankYouScreenProps) {
  const [, setLocation] = useLocation();
  const { interviewDetails } = useInterview();

  if (!isVisible) return null;

  const handleGoHome = () => {
    setLocation("/login");
  };

  const handleShareFeedback = () => {
    // TODO: Implement feedback sharing functionality
    console.log("Sharing feedback...");
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-800 border border-slate-600 rounded-2xl shadow-2xl max-w-md w-full p-8 text-center">
        {/* Success Icon */}
        <div className="flex justify-center mb-6">
          <div className="bg-green-500/20 p-4 rounded-full border border-green-500/30">
            <CheckCircle className="h-12 w-12 text-green-400" />
          </div>
        </div>

        {/* Thank You Message */}
        <h1 className="text-3xl font-bold text-slate-100 mb-4">
          Thank You!
        </h1>
        
        <p className="text-slate-300 mb-6 leading-relaxed">
          Thank you for participating in your {role} interview with {company}. 
          Your interview has been completed successfully.
        </p>

        {/* Interview Details */}
        <div className="bg-slate-700 rounded-lg p-4 mb-6 border border-slate-600">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-slate-400 font-medium">Role</p>
              <p className="text-slate-100 font-semibold">{role}</p>
            </div>
            <div>
              <p className="text-slate-400 font-medium">Company</p>
              <p className="text-slate-100 font-semibold">{company}</p>
            </div>
            <div>
              <p className="text-slate-400 font-medium">Duration</p>
              <p className="text-slate-100 font-semibold">{interviewDuration}</p>
            </div>
            <div>
              <p className="text-slate-400 font-medium">Status</p>
              <p className="text-green-400 font-semibold">Completed</p>
            </div>
          </div>
        </div>

        {/* Next Steps */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-slate-100 mb-3">
            What's Next?
          </h3>
          <ul className="text-sm text-slate-300 space-y-2 text-left">
            <li className="flex items-start">
              <span className="w-2 h-2 bg-blue-400 rounded-full mt-2 mr-3 flex-shrink-0"></span>
              <span>We'll review your interview and provide feedback within 24-48 hours</span>
            </li>
            <li className="flex items-start">
              <span className="w-2 h-2 bg-blue-400 rounded-full mt-2 mr-3 flex-shrink-0"></span>
              <span>You'll receive an email with detailed evaluation and next steps</span>
            </li>
            <li className="flex items-start">
              <span className="w-2 h-2 bg-blue-400 rounded-full mt-2 mr-3 flex-shrink-0"></span>
              <span>Feel free to reach out if you have any questions</span>
            </li>
          </ul>
        </div>

        {/* Action Buttons */}
        <div className="space-y-3">
          <Button 
            onClick={handleGoHome}
            className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98] shadow-lg hover:shadow-xl"
          >
            <Home className="w-4 h-4 mr-2" />
            Return to Home
          </Button>
          
          <Button 
            variant="outline"
            onClick={handleShareFeedback}
            className="w-full border-slate-600 text-slate-300 hover:bg-slate-700 hover:border-slate-500 hover:text-slate-200"
          >
            <Share2 className="w-4 h-4 mr-2" />
            Share Feedback
          </Button>
        </div>

        {/* Footer */}
        <div className="mt-6 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            Thank you for choosing {company} for your interview experience.
          </p>
        </div>
      </div>
    </div>
  );
} 