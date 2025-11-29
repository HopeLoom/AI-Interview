import { useState, useEffect, useRef } from 'react';
import { Header } from './Header';
import { VideoParticipant } from './VideoParticipant';
import { ChatPanel } from './ChatPanel';
import { MediaControls } from './MediaControls';
import { TutorialOverlay } from './TutorialOverlay';
import { LiveCodingLayout } from './LiveCodingLayout';
import { ProblemStatement } from './ProblemStatement';
import { ProgressTracker } from './ProgressTracker';
import { useInterviewState } from '@/hooks/useInterviewState';
import { Dialog, DialogContent } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';
import { formatDistanceToNowStrict } from 'date-fns';
import { useLocation } from 'wouter';
import { useUser } from '@/contexts/UserContext';
import webSocketService from '@/lib/websocketService';
import { useInterview } from '@/contexts/InterviewContext';
import { useAudioStreaming } from '@/hooks/useAudioStreaming';
import { useCamera } from '@/contexts/CameraContext';
import { ExitConfirmationDialog } from './ExitConfirmationDialog';
import { ThankYouScreen } from './ThankYouScreen';

import {
  WebSocketMessageTypeToServer,
  WebSocketMessageTypeFromServer,
  EvaluationDataToServer,
  InterviewEndDataFromServer,
  InterviewMessageFromServer,
  TOPICS,
  SUBTOPICS,
  ActivityInfoFromServer,
  NextSpeakerInfoFromServer,
  InterviewStartDataToServer,
  InterviewStartDataFromServer,
  InterviewMessageToServer,
} from '@/lib/common';

import { toast } from '@/hooks/use-toast';

// When we reach here, interview has already started.
export function InterviewLayout() {
  const { state, actions, interviewDetails } = useInterview(); // Use shared context
  const [isNoteDialogOpen, setIsNoteDialogOpen] = useState(false);
  const { user } = useUser();
  const userIdentifier = user?.id || (user as any)?.email || '';
  const [, setLocation] = useLocation();
  const [showExitDialog, setShowExitDialog] = useState(false);
  const [showThankYouScreen, setShowThankYouScreen] = useState(false);
  const {
    startStream,
    stopStream,
    isReady,
    isStreamActive,
    toggleMicrophone,
    muteMicrophone,
    unmuteMicrophone,
    isMicrophoneMuted,
  } = useCamera();

  // Use refs to maintain stable references to the latest actions and audioStreaming
  const actionsRef = useRef(actions);
  const audioStreamingRef = useRef<any>(null);

  // Add a ref to track participants
  const participantsRef = useRef(state.participants);

  // Add state for user's turn and audio recording
  const [isUserTurn, setIsUserTurn] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioStreamRef = useRef<MediaStream | null>(null);

  // Add a ref to track live coding state to avoid toggle loops
  const isLiveCodingRef = useRef(false);

  // Update the ref when state changes
  useEffect(() => {
    participantsRef.current = state.participants;
    isLiveCodingRef.current = state.isLiveCoding;
  }, [state.participants, state.isLiveCoding]);

  // Update refs when dependencies change
  useEffect(() => {
    actionsRef.current = actions;
  }, [actions]);

  // Load configuration from URL if config_id is present
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const urlParams = new URLSearchParams(window.location.search);
      const configId = urlParams.get('config_id');

      if (configId && userIdentifier) {
        console.log(`Loading configuration: ${configId} for user: ${userIdentifier}`);

        // Send LOAD_CONFIGURATION message via WebSocket
        webSocketService.sendMessage(
          userIdentifier,
          WebSocketMessageTypeToServer.LOAD_CONFIGURATION,
          {
            configuration_id: configId,
          }
        );
      }
    }
  }, [userIdentifier]);

  // Add debugging
  console.log('InterviewLayout - state.messages:', state.messages);
  console.log('InterviewLayout - state.participants:', state.participants);
  console.log('InterviewLayout - isUserTurn:', isUserTurn);

  // when there is an error we should show a toast message
  const handleError = (data: any, id: string) => {
    console.error('WebSocket error:', data);
    toast({
      title: 'Connection Error',
      description: 'Unable to connect to server. Please try again.',
      variant: 'destructive',
    });
  };

  // Use the audio streaming hook
  const audioStreaming = useAudioStreaming({
    onAddMessage: actions.addMessage,
    onError: handleError,
  });

  // Update audioStreaming ref when it changes
  useEffect(() => {
    audioStreamingRef.current = audioStreaming;
  }, [audioStreaming]);

  // Ensure camera is started when interview begins
  useEffect(() => {
    if (user && !isStreamActive()) {
      console.log('Starting camera stream for interview...');
      startStream();
    } else if (user && isStreamActive()) {
      console.log('Camera stream already active, using existing stream');
    }
  }, [user, startStream, isStreamActive]);

  // Function to start audio recording
  const startAudioRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioStreamRef.current = stream;
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
          console.log('Audio chunk received:', event.data.size, 'bytes');
        }
      };

      mediaRecorder.onstop = async () => {
        console.log('Recording stopped, processing audio chunks...');
        console.log('Total audio chunks:', audioChunksRef.current.length);

        if (audioChunksRef.current.length > 0) {
          try {
            // Create a blob from all audio chunks
            const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
            console.log('Audio blob created:', audioBlob.size, 'bytes');

            // Convert blob to base64
            const base64Audio = await blobToBase64(audioBlob);
            console.log('Audio converted to base64, length:', base64Audio.length);

            // Send the audio data to the server
            if (userIdentifier) {
              console.log('Sending AUDIO_RAW_DATA to server...');
              const speechData = { raw_audio_data: base64Audio };
              webSocketService.sendMessage(
                userIdentifier,
                WebSocketMessageTypeToServer.AUDIO_RAW_DATA,
                speechData
              );
            }
          } catch (error) {
            console.error('Error processing recorded audio:', error);
            handleError('Failed to process recorded audio', 'audio_processing_error');
          }
        } else {
          console.warn('No audio chunks recorded');
        }

        // Clean up
        if (audioStreamRef.current) {
          audioStreamRef.current.getTracks().forEach((track) => track.stop());
          audioStreamRef.current = null;
        }
        audioChunksRef.current = [];
        setIsRecording(false);
        console.log('Audio recording cleanup completed');
      };

      mediaRecorder.start();
      setIsRecording(true);
      console.log('Started audio recording');
    } catch (error) {
      console.error('Failed to start audio recording:', error);
      handleError('Failed to start audio recording', 'recording_error');
    }
  };

  // Function to stop audio recording
  const stopAudioRecording = async () => {
    if (mediaRecorderRef.current && isRecording) {
      console.log('Stopping audio recording...');
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      // we are sending audio data in the stop event of the media recorder
    }
  };

  // Helper function to convert blob to base64
  const blobToBase64 = (blob: Blob): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result as string;
        // Remove the data URL prefix to get just the base64 string
        const base64 = result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  };

  // Function to set participant as thinking
  const setParticipantThinking = (speakerId: string) => {
    console.log('Setting participant as thinking:', speakerId);
    actionsRef.current.updateParticipants(
      participantsRef.current.map((p) => ({
        ...p,
        isActive: p.id === speakerId,
        status: p.id === speakerId ? 'THINKING' : 'LISTENING',
      }))
    );
  };

  // Function to set participant as speaking
  const setParticipantSpeaking = (speakerId: string) => {
    console.log('Setting participant as speaking:', speakerId);
    actionsRef.current.updateParticipants(
      participantsRef.current.map((p) => ({
        ...p,
        isActive: p.id === speakerId,
        status: p.id === speakerId ? 'SPEAKING' : 'LISTENING',
      }))
    );
  };

  // Function to set participant as inactive
  const setParticipantInactive = (speakerId: string) => {
    console.log('Setting participant as inactive:', speakerId);
    actionsRef.current.updateParticipants(
      participantsRef.current.map((p) => ({
        ...p,
        isActive: false,
        status: 'LISTENING',
      }))
    );
  };

  // this function will handle the messages received from the server
  const handleMessages = async (data: string, id: string) => {
    console.log('InterviewLayout - handleMessages called with:', data);

    // convert interview message to json
    console.log('Interview message received:', data);
    const interviewMessage: InterviewMessageFromServer = JSON.parse(data);
    console.log('InterviewLayout - parsed interviewMessage:', interviewMessage);

    let is_user_input_required = interviewMessage.is_user_input_required;
    let speaker = interviewMessage.speaker;
    console.log('InterviewLayout - speaker:', speaker);
    // from the participant list, get the current speaker id
    const currentSpeaker = participantsRef.current.find(
      (participant) => participant.name === speaker
    );

    console.log('InterviewLayout - currentSpeaker found:', currentSpeaker);

    if (is_user_input_required === true) {
      if (currentSpeaker) {
        // Set the speaker as speaking (not thinking anymore)
        setParticipantSpeaking(currentSpeaker.id);
        actionsRef.current.setCurrentSpeakerIDData(currentSpeaker.id);
        actionsRef.current.addTypingIndicator(currentSpeaker.id, currentSpeaker.name);

        // If it's the user's turn, enable microphone
        if (currentSpeaker.id === 'Candidate') {
          setIsUserTurn(true);
        }
      } else {
        console.log('Speaker not found in the participant list');
      }
    }

    let current_topic = interviewMessage.current_topic;
    let current_subtopic = interviewMessage.current_subtopic;

    actionsRef.current.setCurrentTopicName(current_topic);
    actionsRef.current.setCurrentSubTopicName(current_subtopic);

    if (current_topic === TOPICS.PROBLEM_INTRODUCTION_AND_CLARIFICATION_SOLVING) {
      // Use ref to check current state immediately
      if (isLiveCodingRef.current === false) {
        console.log('Toggling live coding to true');
        actionsRef.current.toggleLiveCoding();
        actionsRef.current.toggleProblemVisibility();
        actionsRef.current.toggleTimerVisibility();
      } else {
        console.log('Live coding already enabled, skipping toggle');
      }
      console.log('Problem Introduction and Clarification Solving');
    } else if (
      current_topic === TOPICS.DEEP_DIVE_AND_QA &&
      current_subtopic === SUBTOPICS.TASK_SPECIFIC_DISCUSSION
    ) {
      console.log('Task specific discussion');
      if (isLiveCodingRef.current === true) {
        console.log('Toggling live coding to false');
        actionsRef.current.toggleLiveCoding();
        actionsRef.current.toggleProblemVisibility();
        actionsRef.current.toggleTimerVisibility();
      } else {
        console.log('Live coding already disabled, skipping toggle');
      }
    } else {
      console.log('Not in problem solving topic');
    }

    if (is_user_input_required === false && currentSpeaker) {
      console.log('InterviewLayout - calling actions.addMessage with:', {
        text: interviewMessage.text_message,
        senderId: currentSpeaker.id,
        senderName: currentSpeaker.name,
      });

      actionsRef.current.addMessage(
        interviewMessage.text_message,
        currentSpeaker.id,
        currentSpeaker.name
      );
      await audioStreamingRef.current.runTextToSpeech(
        interviewMessage.voice_name,
        interviewMessage.text_message
      );
    }

    if (!currentSpeaker) {
      // display error message
      handleError('Speaker not found in the participant list', id);
    } else {
      actionsRef.current.setCurrentSpeakerIDData(currentSpeaker.id);
    }
  };

  // const handleActivityInfoData = (raw_message: string, id:string) => {
  //   console.log("Activity Info Data Received:", raw_message);
  //   // convert string to json
  //   const message:ActivityInfoFromServer = JSON.parse(raw_message);
  //   const starter_code = message.starter_code || "// Start coding..."; // Use provided code or default
  //   actions.setCode(starter_code);
  // };

  const handleNextSpeakerInfo = (data: string, id: string) => {
    console.log('Next speaker info received:', data);
    const nextSpeakerInfo: NextSpeakerInfoFromServer = JSON.parse(data);
    let speaker = nextSpeakerInfo.speaker;
    console.log('Next speaker info received:', speaker);
    console.log('InterviewLayout - state.participants:', participantsRef.current);
    // from the participant list, get the current speaker id
    const currentSpeaker = participantsRef.current.find(
      (participant) => participant.name === speaker
    );
    console.log('Current speaker id:', currentSpeaker?.id);

    if (!currentSpeaker) {
      handleError('Speaker not found in the participant list', id);
      console.error('Speaker not found in the participant list');
      return;
    }

    // Set the speaker as thinking (not speaking yet)
    setParticipantThinking(currentSpeaker.id);
    actionsRef.current.setCurrentSpeakerIDData(currentSpeaker.id);
    actionsRef.current.addTypingIndicator(currentSpeaker.id, currentSpeaker.name);
  };

  const handleInterviewStart = (data: string, id: string) => {
    console.log('Interview started');
    const interviewStartData: InterviewStartDataFromServer = JSON.parse(data);
    console.log('Interview start data:', interviewStartData);

    // Update participants in state
    actionsRef.current.updateParticipants(interviewStartData.participants);

    // Also update the ref immediately for immediate access
    participantsRef.current = interviewStartData.participants;

    // say the message being received from the server.
    audioStreamingRef.current.runTextToSpeech(
      interviewStartData.voice_name,
      interviewStartData.message
    );
  };

  // Check if user has seen the tutorial before
  useEffect(() => {
    if (!user) {
      console.log('No user logged in');
      setLocation('/login');
    }
    webSocketService.on(WebSocketMessageTypeFromServer.INTERVIEW_START, handleInterviewStart);
    webSocketService.on(WebSocketMessageTypeFromServer.ERROR, handleError);
    webSocketService.on(WebSocketMessageTypeFromServer.INTERVIEW_DATA, handleMessages);
    webSocketService.on(WebSocketMessageTypeFromServer.NEXT_SPEAKER_INFO, handleNextSpeakerInfo);
    webSocketService.on(WebSocketMessageTypeFromServer.INTERVIEW_END, handleInterviewEnd);
    webSocketService.on(WebSocketMessageTypeFromServer.AUDIO_SPEECH_TO_TEXT, handleSpeechToText); // Use custom handler
    webSocketService.on(
      WebSocketMessageTypeFromServer.AUDIO_STREAMING_COMPLETED,
      handleAudioStreamingCompleted
    );
    webSocketService.on(
      WebSocketMessageTypeFromServer.AUDIO_CHUNKS,
      audioStreaming.handleAudioChunks
    );

    // send the interview start data to the server after 500ms delay
    setTimeout(() => {
      if (user) {
        const interviewStartData: InterviewStartDataToServer = { message: 'interview_started' };
        if (userIdentifier) {
          webSocketService.sendMessage(
            userIdentifier,
            WebSocketMessageTypeToServer.INTERVIEW_START,
            interviewStartData
          );
        }
      }
    }, 500);

    return () => {
      webSocketService.off(WebSocketMessageTypeFromServer.INTERVIEW_START, handleInterviewStart);
      webSocketService.off(WebSocketMessageTypeFromServer.ERROR, handleError);
      webSocketService.off(WebSocketMessageTypeFromServer.INTERVIEW_DATA, handleMessages);
      webSocketService.off(WebSocketMessageTypeFromServer.NEXT_SPEAKER_INFO, handleNextSpeakerInfo);
      webSocketService.off(WebSocketMessageTypeFromServer.INTERVIEW_END, handleInterviewEnd);
      webSocketService.off(WebSocketMessageTypeFromServer.AUDIO_SPEECH_TO_TEXT, handleSpeechToText); // Use custom handler
      webSocketService.off(
        WebSocketMessageTypeFromServer.AUDIO_STREAMING_COMPLETED,
        handleAudioStreamingCompleted
      );
      webSocketService.off(
        WebSocketMessageTypeFromServer.AUDIO_CHUNKS,
        audioStreaming.handleAudioChunks
      );
    };
  }, []);

  const handleTakeNotes = () => {
    setIsNoteDialogOpen(true);
  };

  const handleInterviewEnd = async (end_data: string, id: string) => {
    console.log('Interview ended');
    // Stop the timer first
    // Close the video and audio streams
    actionsRef.current.endInterview();
    stopStream();
    const end_message: InterviewEndDataFromServer = JSON.parse(end_data);
    await audioStreamingRef.current.runTextToSpeech(end_message.voice_name, end_message.message);
    setShowThankYouScreen(true);
  };

  // Handle audio streaming completed - set speaker as inactive
  const handleAudioStreamingCompleted = (data: string, id: string) => {
    console.log('Audio streaming completed:', data);

    // Set current speaker as inactive
    const currentSpeakerId = state.currentSpeakerID;
    if (currentSpeakerId) {
      setParticipantInactive(currentSpeakerId);
    }

    // Call the original handler
    audioStreamingRef.current.handleAudioStreamingCompleted(data, id);
  };

  // Add a specific handler for speech-to-text results to ensure typing indicators are removed
  const handleSpeechToText = (data: string, id: string) => {
    console.log('Speech-to-text result received:', data);

    // Call the original handler first
    audioStreamingRef.current.handleTextFromSpeech(data, id);

    // Ensure typing indicator is removed for the current user
    if (user) {
      // Force remove typing indicator for the user
      actionsRef.current.addMessage('', user.id, user.name);
    }
  };

  const formatTimeFromSeconds = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleBackToInterview = () => {
    // This will be called when the user clicks the done button in the live coding layout.
    //actionsRef.current.toggleLiveCoding();
    // send the done problem solving message to the server with the code written by the user
    if (user) {
      if (userIdentifier) {
        webSocketService.sendMessage(
          userIdentifier,
          WebSocketMessageTypeToServer.DONE_PROBLEM_SOLVING,
          { message: 'done_problem_solving', activity_data: state.candidateCode }
        );
      }
    }
  };

  const handleSendMessage = (message: string, senderId: string, senderName: string) => {
    actionsRef.current.addMessage(message, senderId, senderName);
  };

  const handleEndInterviewButtonClick = () => {
    // show exit confirmation dialog
    setShowExitDialog(true);
  };

  if (state.isLiveCoding) {
    return (
      <LiveCodingLayout
        participants={state.participants}
        messages={state.messages}
        onSendMessage={handleSendMessage}
        onBackToInterview={handleBackToInterview}
        OnEndInterview={handleEndInterviewButtonClick}
        elapsedTime={formatTimeFromSeconds(state.elapsedTime)}
        timeRemaining={formatTimeFromSeconds(state.liveCodingTimeRemaining)}
        starterCode={state.starterCode}
      />
    );
  }

  const handleCancelExit = () => {
    setShowExitDialog(false);
  };

  const handleConfirmExit = () => {
    setShowExitDialog(false);
    actionsRef.current.endInterview(); // This will stop the timer
    if (user) {
      if (userIdentifier) {
        webSocketService.sendMessage(userIdentifier, WebSocketMessageTypeToServer.INTERVIEW_END, {
          message: 'interview_ended',
        });
      }
    }
  };

  if (showThankYouScreen) {
    return (
      <ThankYouScreen
        isVisible={showThankYouScreen}
        interviewDuration={formatTimeFromSeconds(state.elapsedTime)}
        role={interviewDetails?.role}
        company={interviewDetails?.company}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 relative overflow-hidden dark-theme">
      {/* Background decorative elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-tr from-indigo-500/10 to-pink-500/10 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-gradient-to-r from-cyan-500/5 to-blue-500/5 rounded-full blur-3xl"></div>
      </div>

      <div className="relative z-10 min-h-screen flex flex-col interview-interface">
        {/* Header */}
        <Header
          title={interviewDetails?.company || 'HopeLoom'}
          interviewType={interviewDetails?.role || 'ML Engineer'}
          elapsedTime="00:00"
          onEndInterview={() => setShowExitDialog(true)}
          isTimerVisible={true}
        />

        {/* Main Content */}
        <div className="flex-1 flex flex-col lg:flex-row gap-6 p-6">
          {/* Left Panel - Video Participants */}
          <div className="lg:w-2/3 space-y-6">
            {/* Video Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {state.participants.map((participant) => (
                <VideoParticipant
                  key={participant.id}
                  participant={participant}
                  isVideoEnabled={true}
                />
              ))}
            </div>

            {/* Live Coding Interface */}
            {state.isLiveCoding && (
              <LiveCodingLayout
                participants={state.participants}
                messages={state.messages}
                onSendMessage={actions.addMessage}
                OnEndInterview={() => setShowExitDialog(true)}
                onBackToInterview={() => actions.toggleLiveCoding()}
                elapsedTime="00:00"
                timeRemaining="15:00"
                starterCode="// Your code here"
              />
            )}

            {/* Problem Statement */}
            {state.problemStatement && (
              <ProblemStatement
                title="Problem Statement"
                content={state.problemStatement}
                isVisible={true}
              />
            )}
          </div>

          {/* Right Panel - Chat and Controls */}
          <div className="lg:w-1/3 space-y-6">
            {/* Chat Panel */}
            <ChatPanel
              messages={state.messages}
              participants={state.participants}
              onSendMessage={actions.addMessage}
            />

            {/* Media Controls */}
            <MediaControls
              onToggleLiveCoding={actions.toggleLiveCoding}
              onToggleTimerVisibility={() => {}}
              isUserTurn={isUserTurn}
              onStartRecording={() => {}}
              onStopRecording={() => {}}
              isRecording={isRecording}
            />

            {/* Progress Tracker */}
            <ProgressTracker
              steps={[
                { id: 1, name: 'Introduction', status: 'completed' },
                { id: 2, name: 'Technical', status: 'active' },
                { id: 3, name: 'Behavioral', status: 'upcoming' },
                { id: 4, name: 'Coding', status: 'upcoming' },
                { id: 5, name: 'Conclusion', status: 'upcoming' },
              ]}
              currentStep={state.currentStep || 1}
            />
          </div>
        </div>

        {/* Tutorial Overlay */}
        {/* Tutorial overlay removed - property doesn't exist in InterviewState */}

        {/* Notes Dialog */}
        <Dialog open={isNoteDialogOpen} onOpenChange={setIsNoteDialogOpen}>
          <DialogContent className="bg-slate-800 border-slate-600 text-slate-100 max-w-2xl max-h-[80vh]">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-slate-100">Interview Notes</h2>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsNoteDialogOpen(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
            <ScrollArea className="h-[60vh]">
              <div className="space-y-4">
                <div className="p-4 bg-slate-700 rounded-lg border border-slate-600">
                  <h3 className="font-medium text-slate-200 mb-2">Key Points</h3>
                  <textarea
                    className="w-full h-32 bg-slate-600 border border-slate-500 rounded-md p-3 text-slate-100 placeholder:text-slate-400 focus:border-blue-400 focus:ring-blue-400/20 focus:bg-slate-500 transition-all duration-200"
                    placeholder="Write your key points here..."
                  />
                </div>
                <div className="p-4 bg-slate-700 rounded-lg border border-slate-600">
                  <h3 className="font-medium text-slate-200 mb-2">Questions to Ask</h3>
                  <textarea
                    className="w-full h-32 bg-slate-600 border border-slate-500 rounded-md p-3 text-slate-100 placeholder:text-slate-400 focus:border-blue-400 focus:ring-blue-400/20 focus:bg-slate-500 transition-all duration-200"
                    placeholder="Write your questions here..."
                  />
                </div>
              </div>
            </ScrollArea>
          </DialogContent>
        </Dialog>

        {/* Exit Confirmation Dialog */}
        <ExitConfirmationDialog
          isOpen={showExitDialog}
          onClose={() => setShowExitDialog(false)}
          onConfirm={() => {
            setShowExitDialog(false);
            setShowThankYouScreen(true);
          }}
        />

        {/* Thank You Screen */}
        {showThankYouScreen && (
          <ThankYouScreen
            isVisible={showThankYouScreen}
            onClose={() => {
              setShowThankYouScreen(false);
              setLocation('/');
            }}
            interviewDuration="00:00"
            role={interviewDetails?.role}
            company={interviewDetails?.company}
          />
        )}
      </div>
    </div>
  );
}
