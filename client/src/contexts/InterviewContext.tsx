import React, { createContext, useContext, useState, ReactNode, useMemo, useRef } from 'react';
import { InterviewDetails, getInterviewDetails } from '@/lib/interviewDetails';
import { InterviewState, Participant, Message, InterviewStep } from '@/lib/types';
import { InstructionDataFromServer, PanelData } from '@/lib/common';

interface InterviewContextType {
  // Interview details (existing)
  interviewDetails: InterviewDetails;
  setInterviewDetails: (details: InterviewDetails) => void;
  updateInterviewDetails: (updates: Partial<InterviewDetails>) => void;
  resetInterviewDetails: () => void;
  
  // Interview state (new)
  state: InterviewState;
  actions: {
    updateInterviewData: (data: InstructionDataFromServer) => void;
    updateParticipants: (participants: PanelData[]) => void;
    setInterviewStarted: (started: boolean) => void;
    setCurrentTopicName: (topic: string) => void;
    setStarterCode: (code: string) => void;
    setCurrentSubTopicName: (subtopic: string) => void;
    setCurrentSpeakerIDData: (speakerID: string) => void;
    addTypingIndicator: (senderID: string, senderName: string) => void;
    toggleAudio: () => void;
    toggleVideo: () => void;
    toggleScreenSharing: () => void;
    toggleProblemVisibility: () => void;
    addMessage: (content: string, senderId?: string, senderName?: string) => void;
    toggleLiveCodingTimer: () => void;
    toggleTimerVisibility: () => void;
    toggleLiveCoding: () => void;
    endInterview: () => void;
    setCandidateCode: (code: string) => void;
    stopTimer: () => void;
    startTimer: () => void;
  };
  interviewData: InstructionDataFromServer | null;
  isInterviewStarted: boolean;
  isUserInputRequired: boolean;
  currentTopic: string;
  currentSubTopic: string;
  currentSpeakerID: string;
}

const InterviewContext = createContext<InterviewContextType | undefined>(undefined);

export const useInterview = () => {
  const context = useContext(InterviewContext);
  if (!context) {
    throw new Error('useInterview must be used within an InterviewProvider');
  }
  return context;
};

interface InterviewProviderProps {
  children: ReactNode;
}

export const InterviewProvider: React.FC<InterviewProviderProps> = ({ children }) => {
  // Interview details state (existing)
  const [interviewDetails, setInterviewDetailsState] = useState<InterviewDetails>(() => {
    return getInterviewDetails();
  });

  // Interview state (new)
  const [interviewState, setState] = useState<InterviewState>({
    title: '',
    currentTopic: '',
    currentSubTopic: '',
    currentSpeakerID: '',
    startTime: new Date(Date.now()), 
    participants: [],
    messages: [],
    currentStep: 1,
    interviewSteps: [],
    isAudioEnabled: true,
    isVideoEnabled: true,
    isScreenSharing: false,
    isProblemVisible: false,
    isLiveCoding: false,
    isTimerVisible: false,
    showLiveCodingTimer: false,
    problemStatement: "",
    starterCode: "",
    candidateCode: "",
    elapsedTime: 0,
    liveCodingTimeRemaining: 15 * 60,
  });

  // WebSocket data state
  const [interviewData, setInterviewData] = useState<InstructionDataFromServer | null>(null);
  const [isInterviewStarted, setIsInterviewStarted] = useState(false);
  const [isUserInputRequired, setIsUserInputRequired] = useState(false);
  const [currentTopic, setCurrentTopic] = useState('');
  const [currentSubTopic, setCurrentSubTopic] = useState('');
  const [currentSpeakerID, setCurrentSpeakerID] = useState('');

  // Add ref to control timer
  const timerIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const liveCodingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const isInterviewEndedRef = useRef(false);

  // Update timer every second - but only if interview hasn't ended
  React.useEffect(() => {
    timerIntervalRef.current = setInterval(() => {
      if (!isInterviewEndedRef.current) {
        setState((prev) => ({
          ...prev,
          elapsedTime: prev.elapsedTime + 1,
        }));
      }
    }, 1000);

    return () => {
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
      }
    };
  }, []);

  // Interview details functions (existing)
  const setInterviewDetails = (details: InterviewDetails) => {
    setInterviewDetailsState(details);
  };

  const updateInterviewDetails = (updates: Partial<InterviewDetails>) => {
    setInterviewDetailsState(prev => ({
      ...prev,
      ...updates
    }));
  };

  const resetInterviewDetails = () => {
    setInterviewDetailsState(getInterviewDetails());
  };

  // Interview state functions (new)
  const updateInterviewData = (data: InstructionDataFromServer) => {
    setInterviewData(data);
    setState(prev => ({
      ...prev,
      title: `${data.role} Interview`,
      participants: data.panelists,
      startTime: new Date(),
      elapsedTime: 0,
    }));
  };

  const updateParticipants = (participants: PanelData[]) => {
    setState(prev => ({
      ...prev,
      participants,
    }));
  };

  const setInterviewStarted = (started: boolean) => {
    setIsInterviewStarted(started);
  };

  const setCurrentTopicName = (topic: string) => {
    setCurrentTopic(topic);
  };

  const setStarterCode = (code: string) => {
    setState((prev) => ({
      ...prev,
      starterCode: code,
    }));
  };

  const setCurrentSubTopicName = (subtopic: string) => {
    setCurrentSubTopic(subtopic);
  };

  const setCurrentSpeakerIDData = (speakerID: string) => {
    setCurrentSpeakerID(speakerID);
  };

  const addTypingIndicator = (senderID: string, senderName: string) => {
    const typingMessage: Message = {
      id: `typing-${Date.now()}`,
      senderId: senderID,
      senderName: senderName,
      content: '',
      timestamp: new Date(),
      isTyping: true
    };
    
    setState((prev) => ({
      ...prev,
      messages: [...prev.messages, typingMessage],
      participants: prev.participants.map(p => 
        p.id === senderID ? { ...p, isActive: true } : p
      ),
    }));
  };

  const toggleAudio = () => {
    setState((prev) => ({
      ...prev,
      isAudioEnabled: !prev.isAudioEnabled,
    }));
  };

  const toggleVideo = () => {
    setState((prev) => ({
      ...prev,
      isVideoEnabled: !prev.isVideoEnabled,
    }));
  };

  const toggleScreenSharing = () => {
    setState((prev) => ({
      ...prev,
      isScreenSharing: !prev.isScreenSharing,
    }));
  };

  const toggleProblemVisibility = () => {
    setState((prev) => ({
      ...prev,
      isProblemVisible: !prev.isProblemVisible,
    }));
  };

  const addMessage = (content: string, senderId: string = 'user', senderName: string = 'You') => {
    console.log("InterviewContext - addMessage called with:", { content, senderId, senderName });
    
    if (content.trim() === '') return;
    
    const newMessage: Message = {
      id: Date.now().toString(),
      senderId: senderId,
      senderName: senderName,
      content,
      timestamp: new Date(),
    };
    
    console.log("InterviewContext - newMessage created:", newMessage);
    
    setState((prev) => {
      console.log("InterviewContext - prev.messages:", prev.messages);
      
      // Remove typing indicator for this sender before adding the new message
      const messagesWithoutTyping = prev.messages.filter(m => !(m.senderId === senderId && m.isTyping));
      
      console.log("InterviewContext - messagesWithoutTyping:", messagesWithoutTyping);
      
      const updatedState = {
        ...prev,
        messages: [...messagesWithoutTyping, newMessage],
        participants: prev.participants.map(p => 
          p.id === senderId ? { ...p, isActive: false } : p
        ),
      };
      
      console.log("InterviewContext - updatedState.messages:", updatedState.messages);
      return updatedState;
    });
  };

  const toggleLiveCodingTimer = () => {
    setState((prev) => ({
      ...prev,
      showLiveCodingTimer: !prev.showLiveCodingTimer,
    }));
  };

  const toggleTimerVisibility = () => {
    setState((prev) => ({
      ...prev,
      isTimerVisible: !prev.isTimerVisible,
    }));
  };

  const toggleLiveCoding = () => {
    setState((prev) => {
      const newIsLiveCoding = !prev.isLiveCoding;
      
      if (newIsLiveCoding) {
        // Starting live coding - start the countdown timer
        console.log("Starting live coding countdown timer");
        liveCodingTimerRef.current = setInterval(() => {
          setState((currentState) => {
            if (currentState.liveCodingTimeRemaining > 0) {
              return {
                ...currentState,
                liveCodingTimeRemaining: currentState.liveCodingTimeRemaining - 1,
              };
            } else {
              // Time's up - clear the timer
              if (liveCodingTimerRef.current) {
                clearInterval(liveCodingTimerRef.current);
                liveCodingTimerRef.current = null;
              }
              return currentState;
            }
          });
        }, 1000);
      } else {
        // Stopping live coding - clear the countdown timer
        console.log("Stopping live coding countdown timer");
        if (liveCodingTimerRef.current) {
          clearInterval(liveCodingTimerRef.current);
          liveCodingTimerRef.current = null;
        }
      }
      
      return {
        ...prev,
        isLiveCoding: newIsLiveCoding,
        // Reset live coding timer when toggling
        liveCodingTimeRemaining: newIsLiveCoding ? 15 * 60 : 0, // 15 minutes when starting
      };
    });
  };

  const endInterview = () => {
    console.log("Ending interview - stopping timer");
    isInterviewEndedRef.current = true;
    
    // Clear the timer
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }
    
    setState((prev) => ({
      ...prev,
      isLiveCoding: false,
      isProblemVisible: false,
      isTimerVisible: false,
      showLiveCodingTimer: false,
    }));
  };

  // Add function to stop timer without ending interview
  const stopTimer = () => {
    console.log("Stopping interview timer");
    isInterviewEndedRef.current = true;
    
    // Clear the main timer
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }
    
    // Clear the live coding timer
    if (liveCodingTimerRef.current) {
      clearInterval(liveCodingTimerRef.current);
      liveCodingTimerRef.current = null;
    }
  };

  // Add function to start timer
  const startTimer = () => {
    console.log("Starting interview timer");
    isInterviewEndedRef.current = false;
    
    // Clear any existing timer
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
    }
    
    // Start the timer
    timerIntervalRef.current = setInterval(() => {
      if (!isInterviewEndedRef.current) {
        setState((prev) => ({
          ...prev,
          elapsedTime: prev.elapsedTime + 1,
        }));
      }
    }, 1000);
  };

  const setCandidateCode = (code: string) => {
    setState((prev) => ({
      ...prev,
      candidateCode: code,
    }));
  };

  const actions = useMemo(() => ({
    updateInterviewData,
    updateParticipants,
    setInterviewStarted,
    setCurrentTopicName,
    setStarterCode,
    setCurrentSubTopicName,
    setCurrentSpeakerIDData,
    addTypingIndicator,
    toggleAudio,
    toggleVideo,
    toggleScreenSharing,
    toggleProblemVisibility,
    addMessage,
    toggleLiveCodingTimer,
    toggleTimerVisibility,
    toggleLiveCoding,
    endInterview,
    setCandidateCode,
    stopTimer,
    startTimer,
  }), []);

  return (
    <InterviewContext.Provider value={{ 
      // Interview details (existing)
      interviewDetails, 
      setInterviewDetails, 
      updateInterviewDetails, 
      resetInterviewDetails,
      
      // Interview state (new)
      state: interviewState,
      actions,
      interviewData,
      isInterviewStarted,
      isUserInputRequired,
      currentTopic,
      currentSubTopic,
      currentSpeakerID,
    }}>
      {children}
    </InterviewContext.Provider>
  );
}; 