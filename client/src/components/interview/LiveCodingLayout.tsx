import { useEffect, useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { VideoParticipant } from './VideoParticipant';
import { ChatPanel } from './ChatPanel';
import { Header } from './Header';
import { Mic, MicOff } from 'lucide-react';
import { Message } from '@/lib/types';
import { PanelData } from '@/lib/common';
import { useInterview } from '@/contexts/InterviewContext';
import webSocketService from '@/lib/websocketService';
import { WebSocketMessageTypeToServer } from '@/lib/common';
import { useUser } from '@/contexts/UserContext';
import { useCamera } from '@/contexts/CameraContext';

interface LiveCodingLayoutProps {
  participants: PanelData[];
  messages: Message[];
  onSendMessage: (message: string, senderId: string, senderName: string) => void;
  OnEndInterview: () => void;
  onBackToInterview: () => void;
  elapsedTime: string;
  timeRemaining: string;
  starterCode: string;
}

export function LiveCodingLayout({
  participants,
  messages,
  onSendMessage,
  OnEndInterview,
  onBackToInterview,
  elapsedTime,
  timeRemaining,
  starterCode,
}: LiveCodingLayoutProps) {
  const [code, setCode] = useState('');
  const [output, setOutput] = useState('');
  const [isCodeEditorFrozen, setIsCodeEditorFrozen] = useState(false);
  const { state, actions, interviewData } = useInterview();
  const { user } = useUser();
  const userIdentifier = user?.id || (user as any)?.email || '';
  const { startStream, isStreamActive, isMicrophoneMuted, toggleMicrophone } = useCamera();

  // Add ref to track if timer has been started
  const timerStartedRef = useRef(false);

  useEffect(() => {
    setCode(starterCode);
  }, [starterCode]);

  useEffect(() => {
    actions.setCandidateCode(code);
  }, [code, actions]);

  // Start live coding timer when component mounts
  useEffect(() => {
    if (!timerStartedRef.current) {
      console.log('Starting live coding timer');
      timerStartedRef.current = true;
      // The timer is already running in the context, we just need to ensure it's visible
      actions.toggleLiveCodingTimer();
    }
  }, [actions]);

  // Ensure camera is active for live coding
  useEffect(() => {
    if (user && !isStreamActive()) {
      console.log('Starting camera stream for live coding...');
      startStream();
    } else if (user && isStreamActive()) {
      console.log('Camera stream already active for live coding');
    }
  }, [user, startStream, isStreamActive]);

  // Freeze code editor when time runs out
  useEffect(() => {
    if (state.liveCodingTimeRemaining <= 0) {
      console.log('Time ran out - freezing code editor');
      setIsCodeEditorFrozen(true);
      // Stop the timer by ending the interview
      //actions.endInterview();
      actions.stopTimer();
      onBackToInterview();
    }
  }, [state.liveCodingTimeRemaining, onBackToInterview, actions]);

  // We need to send candidate code to the server every 1 minute in the background while time is running or user has not clicked done
  useEffect(() => {
    const interval = setInterval(() => {
      if (state.isLiveCoding && userIdentifier && !isCodeEditorFrozen) {
        webSocketService.sendMessage(
          userIdentifier,
          WebSocketMessageTypeToServer.DONE_PROBLEM_SOLVING,
          { message: '', activity_data: state.candidateCode }
        );
      }
    }, 60000);

    return () => clearInterval(interval);
  }, [state.isLiveCoding, state.candidateCode, user, isCodeEditorFrozen]);

  // Handle Done button click
  const handleDoneClick = () => {
    console.log('User clicked Done - freezing code editor');
    setIsCodeEditorFrozen(true);
    // Stop the timer
    actions.stopTimer();
    onBackToInterview();
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800">
      {/* Header */}
      <Header
        title={interviewData?.company || 'HopeLoom'}
        interviewType={interviewData?.role || 'ML Engineer'}
        elapsedTime={elapsedTime}
        onEndInterview={OnEndInterview}
        isTimerVisible={true}
        showLiveCodingTimer={true}
        liveCodingTimeRemaining={timeRemaining}
      />

      {/* Video Participants Row */}
      <div className="bg-slate-800/50 backdrop-blur-sm border-b border-slate-700/50 p-4">
        <div className="grid grid-cols-3 gap-4 max-w-4xl mx-auto">
          {participants.map((participant) => (
            <div key={participant.id} className="h-24">
              <VideoParticipant
                participant={participant}
                isVideoEnabled={participant.id === 'Candidate'}
                className="h-full shadow-lg"
              />
            </div>
          ))}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Coding Area */}
        <div className="flex-1 p-6 flex flex-col min-h-0">
          {/* Coding Header */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
              <div className="h-6 w-px bg-slate-600"></div>
              <h2 className="text-xl font-semibold text-white">Coding Challenge</h2>
              {isCodeEditorFrozen && (
                <div className="bg-yellow-600/20 border border-yellow-500/30 px-3 py-1 rounded-md">
                  <span className="text-yellow-400 text-sm font-medium">Code Editor Frozen</span>
                </div>
              )}
            </div>
            <div
              className={`px-4 py-2 rounded-lg font-medium text-sm text-white shadow-lg ${
                isCodeEditorFrozen ? 'bg-gray-600' : 'bg-gradient-to-r from-red-600 to-red-500'
              }`}
            >
              {isCodeEditorFrozen ? 'Time Up' : `Time Remaining: ${timeRemaining}`}
            </div>
          </div>

          {/* Code Editor - Increased height */}
          <div className="flex-1 flex flex-col min-h-0 mb-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-slate-300">Code Editor</span>
              <div className="flex items-center space-x-2 text-xs text-slate-400">
                <div
                  className={`w-2 h-2 rounded-full ${isCodeEditorFrozen ? 'bg-gray-400' : 'bg-green-400'}`}
                ></div>
                <span>Python</span>
                {isCodeEditorFrozen && <span className="text-yellow-400">• Frozen</span>}
              </div>
            </div>

            <div
              className={`flex-1 rounded-xl border overflow-hidden shadow-2xl bg-slate-800/50 backdrop-blur-sm min-h-0 ${
                isCodeEditorFrozen ? 'border-yellow-500/30 bg-slate-800/70' : 'border-slate-600/50'
              }`}
            >
              <textarea
                value={code}
                onChange={(e) => {
                  if (!isCodeEditorFrozen) {
                    setCode(e.target.value);
                  }
                }}
                className={`w-full h-full bg-transparent p-6 font-mono text-sm focus:outline-none resize-none border-0 leading-relaxed ${
                  isCodeEditorFrozen ? 'text-slate-400 cursor-not-allowed' : 'text-slate-100'
                }`}
                spellCheck="false"
                disabled={isCodeEditorFrozen}
                style={{
                  fontFamily:
                    '"JetBrains Mono", "Fira Code", Monaco, Menlo, "Ubuntu Mono", monospace',
                  lineHeight: '1.6',
                }}
                placeholder={isCodeEditorFrozen ? 'Code editor is frozen' : 'Start coding here...'}
              />
            </div>
          </div>

          {/* Bottom Controls - Moved lower with more spacing */}
          <div className="flex justify-center space-x-4 pb-4">
            <Button
              variant="outline"
              className={`px-6 py-3 rounded-lg font-medium transition-all duration-200 ${
                isMicrophoneMuted
                  ? 'bg-red-600 border-red-500 text-white hover:bg-red-700 shadow-lg shadow-red-600/25'
                  : 'bg-green-600 border-green-500 text-white hover:bg-green-700 shadow-lg shadow-green-600/25'
              }`}
              onClick={toggleMicrophone}
            >
              {isMicrophoneMuted ? (
                <MicOff className="w-4 h-4 mr-2" />
              ) : (
                <Mic className="w-4 h-4 mr-2" />
              )}
              {isMicrophoneMuted ? 'Unmute' : 'Mute'}
            </Button>
            <Button
              className={`px-6 py-3 rounded-lg font-medium transition-all duration-200 shadow-lg ${
                isCodeEditorFrozen
                  ? 'bg-gray-600 text-gray-300 cursor-not-allowed'
                  : 'bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 shadow-blue-600/25'
              }`}
              onClick={handleDoneClick}
              disabled={isCodeEditorFrozen}
            >
              {isCodeEditorFrozen ? 'Done' : 'Done'}
            </Button>
          </div>
        </div>

        {/* Chat Panel - Fixed to match InterviewLayout structure */}
        <ChatPanel messages={messages} participants={participants} onSendMessage={onSendMessage} />
      </div>
    </div>
  );
}
