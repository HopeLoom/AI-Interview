import { Button } from "@/components/ui/button";
import { Code, Clock, Mic, MicOff } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useCamera } from "@/contexts/CameraContext";

interface MediaControlsProps {
  onToggleLiveCoding: () => void;
  onToggleTimerVisibility: () => void;
  isUserTurn?: boolean;
  onStartRecording?: () => void;
  onStopRecording?: () => void;
  isRecording?: boolean;
}

export function MediaControls({
  onToggleLiveCoding,
  onToggleTimerVisibility,
  isUserTurn = false,
  onStartRecording,
  onStopRecording,
  isRecording = false
}: MediaControlsProps) {
  const { isMicrophoneMuted, toggleMicrophone, muteMicrophone, unmuteMicrophone } = useCamera();

  const handleMicrophoneClick = () => {
    if (!isUserTurn) {
      // Don't allow toggling if it's not the user's turn
      return;
    }

    if (isMicrophoneMuted) {
      // Unmuting - start recording
      unmuteMicrophone();
      onStartRecording?.();
    } else {
      // Muting - stop recording
      muteMicrophone();
      onStopRecording?.();
    }
  };

  return (
    <div id="media-controls" className="mt-4 bg-white border border-neutral-200 rounded-lg p-3 flex items-center justify-between">
      <div className="flex items-center space-x-2">
        <Button
          variant="outline"
          className={`px-4 py-2 rounded-md font-medium flex items-center ${
            !isUserTurn 
              ? 'bg-gray-400 border-gray-400 text-white cursor-not-allowed' 
              : isMicrophoneMuted 
                ? 'bg-red-600 border-red-600 text-white hover:bg-red-700' 
                : 'bg-green-600 border-green-600 text-white hover:bg-green-700'
          }`}
          onClick={handleMicrophoneClick}
          disabled={!isUserTurn}
        >
          {isMicrophoneMuted ? <MicOff className="w-4 h-4 mr-2" /> : <Mic className="w-4 h-4 mr-2" />}
          {!isUserTurn ? 'Microphone Disabled' : isMicrophoneMuted ? 'Unmute' : 'Mute'}
        </Button>
        
        {isRecording && (
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
            <span className="text-sm text-red-600 font-medium">Recording...</span>
          </div>
        )}
      </div>
      
      {/* <Button
        variant="ghost"
        className="bg-primary-100 hover:bg-primary-200 text-primary-700 px-4 py-2 rounded-md font-medium flex items-center"
        onClick={onToggleLiveCoding}
      >
        <Code className="w-5 h-5 mr-2" />
        Live Coding
      </Button> */}
      
      <div className="flex items-center space-x-2">
        {onToggleTimerVisibility && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="bg-neutral-100 hover:bg-neutral-200 text-neutral-700 p-2.5 rounded-full"
                  onClick={onToggleTimerVisibility}
                >
                  <Clock className="w-5 h-5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                Toggle Timer Display
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>
    </div>
  );
}
