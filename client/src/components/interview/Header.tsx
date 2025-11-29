import { useState } from "react";
import { Button } from "@/components/ui/button";
import { X, Clock, Code } from "lucide-react";
import { ExitConfirmationDialog } from "./ExitConfirmationDialog";

interface HeaderProps {
  title: string;
  interviewType: string;
  elapsedTime: string;
  onEndInterview: () => void;
  isTimerVisible?: boolean;
  showLiveCodingTimer?: boolean;
  liveCodingTimeRemaining?: string;
}

export function Header({ 
  title, 
  interviewType, 
  elapsedTime, 
  onEndInterview,
  isTimerVisible = false,
  showLiveCodingTimer = false,
  liveCodingTimeRemaining = "15:00"
}: HeaderProps) {
  const [showExitDialog, setShowExitDialog] = useState(false);
  
  const handleExitClick = () => {
    setShowExitDialog(true);
  };
  
  const handleCancelExit = () => {
    setShowExitDialog(false);
  };
  
  const handleConfirmExit = () => {
    setShowExitDialog(false);
    onEndInterview();
  };
  
  return (
    <>
      <header className="bg-slate-800/90 border-b border-slate-600 py-4 px-6 backdrop-blur-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <h1 className="text-2xl font-bold text-slate-100">{title}</h1>
            <div className="ml-4 px-4 py-2 bg-gradient-to-r from-blue-500/20 to-indigo-500/20 text-blue-300 rounded-full text-sm font-medium border border-blue-500/30">
              {interviewType}
            </div>
          </div>
          <div className="flex items-center space-x-4">
            {showLiveCodingTimer && (
              <div className="flex items-center bg-amber-500/20 rounded-full px-4 py-2 border border-amber-500/30 animate-pulse">
                <Code className="w-4 h-4 text-amber-400 mr-2" />
                <span className="text-sm font-medium tabular-nums text-amber-300">
                  Live Coding — {liveCodingTimeRemaining}
                </span>
              </div>
            )}
            
            {isTimerVisible && !showLiveCodingTimer && (
              <div className="flex items-center bg-slate-700/50 rounded-full px-4 py-2 border border-slate-500/50">
                <Clock className="w-4 h-4 text-slate-300 mr-2" />
                <span className="text-sm font-medium tabular-nums text-slate-200" id="interview-timer">{elapsedTime}</span>
              </div>
            )}
            
            {/* Exit button */}
            <Button 
              variant="ghost" 
              size="icon" 
              className="bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30 hover:border-red-500/50 transition-all duration-200" 
              title="End Interview" 
              onClick={handleExitClick}
            >
              <X className="w-5 h-5" />
            </Button>
          </div>
        </div>
      </header>
      
      {/* Exit Confirmation Dialog */}
      <ExitConfirmationDialog
        isOpen={showExitDialog}
        onClose={handleCancelExit}
        onConfirm={handleConfirmExit}
      />
    </>
  );
}
