import { useState, useEffect, useCallback } from 'react';
import { useConfiguration } from '../contexts/ConfigurationContext';
import { InterviewState, Message } from '../lib/types';
import { PanelData, InterviewRound } from '../lib/common';

export const useInterviewState = () => {
  const { state } = useConfiguration();
  const [interviewState, setInterviewState] = useState<InterviewState>({
    title: 'Interview',
    startTime: new Date(),
    participants: [],
    messages: [],
    currentStep: 0,
    interviewSteps: [],
    isAudioEnabled: true,
    isVideoEnabled: true,
    isScreenSharing: false,
    isProblemVisible: false,
    isTimerVisible: true,
    showLiveCodingTimer: false,
    isLiveCoding: false,
    problemStatement: '',
    elapsedTime: 0,
    liveCodingTimeRemaining: 0,
    currentTopic: '',
    currentSubTopic: '',
    currentSpeakerID: '',
    starterCode: '',
    candidateCode: ''
  });

  // Initialize participants from configuration when it changes
  useEffect(() => {
    if (state.currentConfig) {
      const loadInterviewData = async () => {
        try {
          setInterviewState(prev => ({
            ...prev,
            participants: [],
            currentStep: 0,
            interviewSteps: []
          }));
        } catch (error) {
          console.error('Failed to load interview data:', error);
          setInterviewState(prev => ({
            ...prev,
            participants: [],
            currentStep: 0,
            interviewSteps: []
          }));
        }
      };

      loadInterviewData();
    }
  }, [state.currentConfig]);

  const startInterview = useCallback(() => {
    setInterviewState((prev: InterviewState) => ({
      ...prev,
      startTime: new Date()
    }));
  }, []);

  const endInterview = useCallback(() => {
    setInterviewState((prev: InterviewState) => ({
      ...prev,
      currentStep: prev.interviewSteps.length - 1
    }));
  }, []);

  const addMessage = useCallback((message: Message) => {
    setInterviewState((prev: InterviewState) => ({
      ...prev,
      messages: [...prev.messages, message]
    }));
  }, []);

  const updatePhase = useCallback((stepIndex: number) => {
    setInterviewState((prev: InterviewState) => ({
      ...prev,
      currentStep: stepIndex,
      interviewSteps: prev.interviewSteps.map((step, index) => ({
        ...step,
        status: index === stepIndex ? 'active' : index < stepIndex ? 'completed' : 'upcoming'
      }))
    }));
  }, []);

  const switchParticipant = useCallback((participantId: string) => {
    setInterviewState((prev: InterviewState) => {
      const updatedParticipants = prev.participants.map((p: PanelData) => ({
        ...p,
        isActive: p.id === participantId
      }));

      return {
        ...prev,
        participants: updatedParticipants
      };
    });
  }, []);

  const updateScore = useCallback((newScore: number) => {
    // Score is not part of the InterviewState interface, so we'll skip this
    console.log('Score updated:', newScore);
  }, []);

  const addFeedback = useCallback((feedback: string) => {
    // Feedback is not part of the InterviewState interface, so we'll skip this
    console.log('Feedback added:', feedback);
  }, []);

  const resetInterview = useCallback(() => {
    setInterviewState({
      title: 'Interview',
      startTime: new Date(),
      participants: [],
      messages: [],
      currentStep: 0,
      interviewSteps: [],
      isAudioEnabled: true,
      isVideoEnabled: true,
      isScreenSharing: false,
      isProblemVisible: false,
      isTimerVisible: true,
      showLiveCodingTimer: false,
      isLiveCoding: false,
      problemStatement: '',
      elapsedTime: 0,
      liveCodingTimeRemaining: 0,
      currentTopic: '',
      currentSubTopic: '',
      currentSpeakerID: '',
      starterCode: '',
      candidateCode: ''
    });
  }, []);

  // Calculate elapsed time
  useEffect(() => {
    const interval = setInterval(() => {
      if (interviewState.startTime) {
        const elapsed = Math.floor((Date.now() - interviewState.startTime.getTime()) / 1000);
        setInterviewState((prev: InterviewState) => ({ ...prev, elapsedTime: elapsed }));
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [interviewState.startTime]);

  return {
    interviewState,
    startInterview,
    endInterview,
    addMessage,
    updatePhase,
    switchParticipant,
    updateScore,
    addFeedback,
    resetInterview
  };
};
