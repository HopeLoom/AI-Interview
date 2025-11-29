import { useEffect, useState } from 'react';
import { TutorialOverlay } from '@/components/interview/TutorialOverlay';
import { InterviewIntroScreen } from '@/components/interview/InterviewIntroScreen';
import { ReadyToJoinScreen } from '@/components/interview/ReadyToJoinScreen';
import { LoadingDialog } from '@/components/interview/LoadingDialog';
import { Button } from '@/components/ui/button';
import { VideoParticipant } from '@/components/interview/VideoParticipant';
import { ChatPanel } from '@/components/interview/ChatPanel';
import { MediaControls } from '@/components/interview/MediaControls';
import { Header } from '@/components/interview/Header';
import { LiveCodingLayout } from '@/components/interview/LiveCodingLayout';
import { InterviewRound, PanelData, ActivityInfoFromServer, ActivityInfoDataToServer } from '@/lib/common';
import { useLocation } from 'wouter';
import { useUser } from '@/contexts/UserContext';
import webSocketService from '@/lib/websocketService';
import { WebSocketMessageTypeToServer, WebSocketMessageTypeFromServer, InstructionDataToServer, InstructionDataFromServer } from '@/lib/common';
import { useInterview } from '@/contexts/InterviewContext';

// Mock data for the demo - this will be replaced by service calls
const mockParticipants:PanelData[] = [
  {
    id: 'ai1',
    name: 'Alice Thompson',
    avatar: undefined,
    isAI: true,
    isActive: true,
    intro: "Alice Thompson is a Lead Machine Learning Engineer with over 8 years of experience, skilled in building and deploying ML models. She has a strong analytical mindset and stays updated with the latest ML technologies.",
    interview_round_part_of: InterviewRound.ROUND_TWO,
    connectionStatus: 'connected' as const
  },
  {
    id: 'ai2',
    name: 'Ben Martinez',
    avatar: undefined,
    isAI: true,
    isActive: false,
    intro: "Ben Martinez is a Product Manager with a knack for aligning technical teams with business goals. He's experienced in developing ML solutions and ensures cohesive product execution.",
    interview_round_part_of: InterviewRound.ROUND_TWO,
    connectionStatus: 'connected' as const
  },
  {
    id: 'user',
    name: 'Demo User',
    avatar: undefined,
    isAI: false,
    isActive: false,
    intro: "Demo User is a user who is participating in the interview.",
    interview_round_part_of: InterviewRound.ROUND_TWO,
    connectionStatus: 'connected' as const
  }
];

const mockMessages = [
  {
    id: '1',
    senderId: 'ai1',
    senderName: 'Alice Thompson',
    content: 'Welcome to your ML Engineer interview! Let\'s start by discussing your experience with recommendation systems.',
    timestamp: new Date(Date.now() - 300000)
  },
  {
    id: '2',
    senderId: 'user',
    senderName: 'Demo User',
    content: 'Thank you! I\'ve worked on collaborative filtering and content-based recommendation models in my previous role.',
    timestamp: new Date(Date.now() - 270000)
  },
  {
    id: '3',
    senderId: 'ai2',
    senderName: 'Ben Martinez',
    content: 'Great! Could you explain the difference between these approaches and when you might choose one over the other?',
    timestamp: new Date(Date.now() - 240000)
  },
  {
    id: '4',
    senderId: 'user',
    senderName: 'Demo User',
    content: 'Collaborative filtering relies on user interaction data and finds similar users to make recommendations. Content-based filtering uses item features instead. I typically use collaborative filtering when we have rich user interaction data, and content-based when we have good item metadata or for cold-start problems.',
    timestamp: new Date(Date.now() - 210000)
  },
  {
    id: '5',
    senderId: 'ai1',
    senderName: 'Alice Thompson',
    content: 'Excellent explanation. What evaluation metrics do you typically use for recommendation systems?',
    timestamp: new Date(Date.now() - 180000)
  },
  {
    id: '6',
    senderId: 'user',
    senderName: 'Demo User',
    content: 'For offline evaluation, I use metrics like precision, recall, NDCG, and MAP. In production, I focus on A/B testing with business metrics like CTR, conversion rate, and session duration to measure real-world impact.',
    timestamp: new Date(Date.now() - 150000)
  },
  {
    id: '7',
    senderId: 'ai2',
    senderName: 'Ben Martinez',
    content: 'Now let\'s move on to a practical problem. Can you describe how you would build a recommendation system for a streaming service with millions of users?',
    timestamp: new Date(Date.now() - 120000)
  }
];

// Panelist data
const panelistData:PanelData[] = [
  {
    name: "Alice Thompson",
    id: "ai1",
    avatar: "https://via.placeholder.com/150",
    interview_round_part_of: InterviewRound.ROUND_TWO,
    intro: "Alice Thompson is a Lead Machine Learning Engineer with over 8 years of experience, skilled in building and deploying ML models. She has a strong analytical mindset and stays updated with the latest ML technologies.",
    isAI: false,
    isActive: false,
    connectionStatus: 'connected'
  },
  {
    name: "Ben Martinez",
    id: "ai2",
    avatar: "https://via.placeholder.com/150",
    interview_round_part_of: InterviewRound.ROUND_TWO,
    intro: "Ben Martinez is a Product Manager with a knack for aligning technical teams with business goals. He's experienced in developing ML solutions and ensures cohesive product execution.",
    isAI: false,
    isActive: false,
    connectionStatus: 'connected'
  }
];
// This will show tutorial followed by intro screen followed by ready to join screen.
export default function TutorialDemo() {
  const [showTutorial, setShowTutorial] = useState(true);
  const [showIntroScreen, setShowIntroScreen] = useState(false);
  const [showReadyToJoin, setShowReadyToJoin] = useState(false);
  const [showLoadingDialog, setShowLoadingDialog] = useState(false);
  const [isInterviewStarted, setIsInterviewStarted] = useState(false);
  const [instructionData, setInstructionData] = useState<InstructionDataFromServer | null>(null);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const { state, actions, interviewData } = useInterview(); // Use shared context instead of useInterviewState
  // Camera is always enabled - isVideoEnabled state removed
  // Screen sharing removed
  const [isLiveCodingActive, setIsLiveCodingActive] = useState(false);
  const [isTimerVisible, setIsTimerVisible] = useState(true);
  const [, setLocation] = useLocation();
  const { user } = useUser(); // this is companycandidateProfile or companyProfile
  const userIdentifier = user?.id || (user as any)?.email || '';


  useEffect(() => {
    const hasSeenTutorial = localStorage.getItem('hasSeenTutorial');
    if (hasSeenTutorial === 'true') {
      setShowTutorial(false);
      handleTutorialComplete();
    }
  }, []);

  const handleTutorialComplete = () => {
    const instructionData: InstructionDataToServer = { message: "Start the interview" };
    if (userIdentifier) {
      webSocketService.sendMessage(userIdentifier, WebSocketMessageTypeToServer.INSTRUCTION, instructionData);
      // Show loading dialog immediately after sending the message
      setShowLoadingDialog(true);
      startLoadingProgress();
    } else {
      console.error("User data not found");
    }
    setShowTutorial(false);
    localStorage.setItem('hasSeenTutorial', 'true');
    // send the interview start data to the server
  };

  const startLoadingProgress = () => {
    setLoadingProgress(0);
    const interval = setInterval(() => {
      setLoadingProgress(prev => {
        if (prev >= 90) {
          clearInterval(interval);
          return 90; // Stop at 90% until we get the response
        }
        return prev + 10;
      });
    }, 250);
  };

  const handleInstructionData = async (start_data: string, id: string) => { 
    console.log("Interview Started");
    const start_message: InstructionDataFromServer = JSON.parse(start_data);
    setInstructionData(start_message);
    
    // Complete the loading progress
    setLoadingProgress(100);
    
    // Wait a moment to show 100% completion, then hide loading dialog
    setTimeout(() => {
      setShowLoadingDialog(false);
      setShowIntroScreen(true);
    }, 500);
    
    actions.updateInterviewData(start_message);
    actions.setInterviewStarted(true);
    if (userIdentifier) {
      const activityInfoData: ActivityInfoDataToServer = { message: "activity_info" };
      webSocketService.sendMessage(userIdentifier, WebSocketMessageTypeToServer.ACTIVITY_INFO, activityInfoData);
    }
  };

  const handleActivityInfoData = (raw_message: string, id: string) => { 
    console.log("Activity Info Data Received:", raw_message);
    const message: ActivityInfoFromServer = JSON.parse(raw_message);
    const starter_code = message.starter_code;
    actions.setStarterCode(starter_code);
  };
  
  const handleShowTutorial = () => {
    setShowTutorial(true);
    setShowIntroScreen(false);
    setShowReadyToJoin(false);
    setIsInterviewStarted(false);
    setShowLoadingDialog(false);
    setLoadingProgress(0);
  };
  
  const handleIntroScreenClose = () => {
    setShowIntroScreen(false);
    setShowReadyToJoin(true);
  };
  
  const handleJoinInterview = () => {
    setShowReadyToJoin(false);
    setIsInterviewStarted(true);
    setLocation("/interview");
  };

  useEffect(() => {
    webSocketService.on(WebSocketMessageTypeFromServer.INSTRUCTION, handleInstructionData);
    webSocketService.on(WebSocketMessageTypeFromServer.ACTIVITY_INFO, handleActivityInfoData);
    return () => {
      webSocketService.off(WebSocketMessageTypeFromServer.INSTRUCTION, handleInstructionData);
      webSocketService.off(WebSocketMessageTypeFromServer.ACTIVITY_INFO, handleActivityInfoData);
    };
  }, []);

  // Show live coding layout when active
  if (isLiveCodingActive) {
    return (
      <LiveCodingLayout
        participants={mockParticipants}
        starterCode={""}
        messages={mockMessages}
        onSendMessage={(message) => console.log('Send message:', message)}
        onBackToInterview={() => setIsLiveCodingActive(false)}
        OnEndInterview={() => console.log('End interview')}
        elapsedTime="05:23"
        timeRemaining="13:23"
      />
    );
  }

  return (
    <div className="flex flex-col h-screen bg-white">
      {/* Mock Interview Interface */}
      <Header 
        title="HopeLoom" 
        interviewType="ML Engineer Interview"
        elapsedTime="05:23"
        onEndInterview={() => console.log('End interview')}
        isTimerVisible={isTimerVisible}
        showLiveCodingTimer={false}
        liveCodingTimeRemaining="30:00"
      />

      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 flex flex-col p-4 overflow-hidden">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 flex-1 overflow-y-auto pb-2">
            {/* Camera always enabled for user */}
            {mockParticipants.map((participant) => (
              <VideoParticipant
                key={participant.id}
                participant={participant}
                isVideoEnabled={participant.id === 'user'}
              />
            ))}
          </div>

          <MediaControls

            onToggleLiveCoding={() => setIsLiveCodingActive(true)}
            onToggleTimerVisibility={() => setIsTimerVisible(!isTimerVisible)}
          />
        </div>

        <ChatPanel 
          messages={mockMessages} 
          participants={mockParticipants}
          onSendMessage={(message) => console.log('Send message:', message)}
        />
      </div>
      
      {/* Tutorial Overlay */}
      {showTutorial && (
        <TutorialOverlay 
          onComplete={handleTutorialComplete}
          userName="Demo User"
          role="ML Engineer"
        />
      )}
      
      {/* Loading Dialog */}
      <LoadingDialog 
        isOpen={showLoadingDialog}
        title="Getting Interview Information"
        description="Please wait while we prepare your interview..."
        progress={loadingProgress}
      />
      
      {/* Button to show tutorial again when it's closed */}
      {!showTutorial && !showIntroScreen && !showLoadingDialog && (
        <div className="fixed bottom-5 right-5 z-50">
          <Button 
            onClick={handleShowTutorial}
            className="bg-blue-600 hover:bg-blue-700 shadow-lg"
          >
            Show Tutorial Again
          </Button>
        </div>
      )}
      
      {/* Interview Introduction Screen */}
      {instructionData && (
        <InterviewIntroScreen
          isOpen={showIntroScreen}
          onClose={handleIntroScreenClose}
          role={instructionData.role} 
          company={instructionData.company}
          interviewType={instructionData.interview_type}
          panelists={instructionData.panelists}
          introduction={instructionData.introduction}

        />
      )}
      
      {/* Ready to Join Screen */}
      <ReadyToJoinScreen
        isOpen={showReadyToJoin}
        onJoin={handleJoinInterview}
        onCancel={() => setShowReadyToJoin(false)}
      />
    </div>
  );
}