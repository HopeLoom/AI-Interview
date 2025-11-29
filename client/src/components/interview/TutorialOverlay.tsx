import { useState, useEffect } from 'react';
import { 
  ChevronLeft, 
  ChevronRight, 
  X, 
  Video, 
  MessageSquare, 
  Mic, 
  Code, 
  Users,
  ArrowRight
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface TutorialStep {
  title: string;
  description: string;
  icon: React.ReactNode;
  targetElement?: string;
  position?: 'top' | 'bottom' | 'left' | 'right' | 'center';
}

interface TutorialOverlayProps {
  onComplete: () => void;
  userName?: string;
  role?: string;
}

export function TutorialOverlay({ onComplete, userName = 'Candidate', role = 'ML Engineer' }: TutorialOverlayProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isVisible, setIsVisible] = useState(true);

  const tutorialSteps: TutorialStep[] = [
    {
      title: 'Welcome to your AI-powered interview',
      description: `You'll be guided by a panel of AI agents through a live technical interview for the ${role} position. They'll ask questions, assign tasks, and respond to your answers in real time—just like real interviewers.`,
      icon: <Users className="h-8 w-8 text-blue-400" />,
      position: 'center'
    },
    {
      title: 'Meet your AI panelists',
      description: "You're speaking with AI panelists that specialize in technical assessments. They'll guide you through the entire process, ask questions, and provide feedback throughout your interview.",
      icon: <Users className="h-8 w-8 text-blue-400" />,
      targetElement: 'video-participants',
      position: 'top'
    },
    {
      title: 'Camera and audio controls',
      description: 'Click the microphone and camera buttons in the control bar below to manage your audio and video. The red icon indicates when a device is disabled.',
      icon: <Video className="h-8 w-8 text-blue-400" />,
      targetElement: 'media-controls',
      position: 'bottom'
    },
    {
      title: 'Interview transcript',
      description: 'Click the "Transcript" tab in the right panel to view your conversation history. All questions and answers are saved here for your reference.',
      icon: <MessageSquare className="h-8 w-8 text-blue-400" />,
      targetElement: 'transcript-panel',
      position: 'left'
    },
    {
      title: 'Taking notes',
      description: 'Click the "Notes" tab in the right panel or use the notepad button in the control bar to take private notes during your interview.',
      icon: <MessageSquare className="h-8 w-8 text-blue-400" />,
      targetElement: 'notes-panel',
      position: 'left'
    },
    {
      title: 'Problem statement',
      description: "Click the 'Show Problem Statement' button in the control bar to view coding challenges. A dialog will appear with the complete problem description.",
      icon: <Code className="h-8 w-8 text-blue-400" />,
      targetElement: 'problem-statement',
      position: 'top'
    },
    {
      title: 'Coding interface',
      description: "When a coding challenge appears, you'll use this editor to write and test your solution. Click 'Run' to test your code and 'Submit' when finished.",
      icon: <Code className="h-8 w-8 text-blue-400" />,
      targetElement: 'coding-interface',
      position: 'center'
    },
    {
      title: 'When to speak',
      description: 'Only unmute your microphone when you need to speak. Keep it muted otherwise to prevent the AI from detecting background noise as your input. Speak clearly and at a moderate pace when responding.',
      icon: <Mic className="h-8 w-8 text-blue-400" />,
      position: 'center'
    },
    {
      title: 'Ready to begin!',
      description: `You're all set, ${userName}! The interview will begin as soon as you click "Start Interview" below. Good luck with your ${role} interview!`,
      icon: <ArrowRight className="h-8 w-8 text-blue-400" />,
      position: 'center'
    }
  ];

  const goToNextStep = () => {
    if (currentStep < tutorialSteps.length - 1) {
      setCurrentStep(prev => prev + 1);
    } else {
      onComplete();
    }
  };

  const goToPreviousStep = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const skipTutorial = () => {
    onComplete();
  };

  if (!isVisible) return null;

  const currentStepData = tutorialSteps[currentStep];
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === tutorialSteps.length - 1;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="relative w-full max-w-2xl">
        <Card className="bg-slate-800/95 border-slate-600 shadow-2xl backdrop-blur-sm">
          <CardHeader className="text-center pb-4">
            <div className="flex items-center justify-center mb-4">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl shadow-lg">
                {currentStepData.icon}
              </div>
            </div>
            <CardTitle className="text-2xl font-bold text-slate-100">
              {currentStepData.title}
            </CardTitle>
            <p className="text-slate-300 text-base mt-2">
              {currentStepData.description}
            </p>
          </CardHeader>
          
          <CardContent className="space-y-6">
            {/* Progress indicator */}
            <div className="flex items-center justify-center space-x-2">
              {tutorialSteps.map((_, index) => (
                <div
                  key={index}
                  className={`w-2 h-2 rounded-full transition-all duration-200 ${
                    index === currentStep 
                      ? 'bg-blue-400 scale-125' 
                      : index < currentStep 
                      ? 'bg-green-400' 
                      : 'bg-slate-600'
                  }`}
                />
              ))}
            </div>

            {/* Step counter */}
            <div className="text-center">
              <span className="text-sm text-slate-400">
                Step {currentStep + 1} of {tutorialSteps.length}
              </span>
            </div>

            {/* Action buttons */}
            <div className="flex items-center justify-between pt-4">
              <div className="flex items-center space-x-3">
                <Button
                  variant="outline"
                  onClick={skipTutorial}
                  className="border-slate-600 text-slate-300 hover:bg-slate-700 hover:border-slate-500 hover:text-slate-200"
                >
                  Skip Tutorial
                </Button>
              </div>
              
              <div className="flex items-center space-x-3">
                <Button
                  variant="outline"
                  onClick={goToPreviousStep}
                  disabled={isFirstStep}
                  className="border-slate-600 text-slate-300 hover:bg-slate-700 hover:border-slate-500 hover:text-slate-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="w-4 h-4 mr-2" />
                  Previous
                </Button>
                
                <Button
                  onClick={goToNextStep}
                  className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98] shadow-lg hover:shadow-xl"
                >
                  {isLastStep ? (
                    <>
                      Start Interview
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </>
                  ) : (
                    <>
                      Next
                      <ChevronRight className="w-4 h-4 ml-2" />
                    </>
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Close button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={skipTutorial}
          className="absolute -top-3 -right-3 w-8 h-8 rounded-full bg-slate-700 border-slate-600 text-slate-300 hover:bg-slate-600 hover:text-slate-200 shadow-lg"
        >
          <X className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}