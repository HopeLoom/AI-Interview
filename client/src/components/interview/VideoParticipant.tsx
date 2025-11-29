import { cn } from "@/lib/utils";
import { Participant } from "@/lib/types";
import { PanelData } from "@/lib/common";
import { useCamera } from "@/contexts/CameraContext";
import { useRef, useEffect } from "react";
import { Mic, MicOff } from "lucide-react";
import { ActiveSpeakerIndicator } from "./ActiveSpeakerIndicator";

interface VideoParticipantProps {
  participant: PanelData;
  isVideoEnabled: boolean;
  className?: string;
}

export function VideoParticipant({ participant, isVideoEnabled, className }: VideoParticipantProps) {
  const { id, name, avatar, isAI, isActive, connectionStatus } = participant;
  const { stream, isReady, isStreamActive, isMicrophoneMuted } = useCamera();
  const videoRef = useRef<HTMLVideoElement>(null);
  
  const isSelf = id === 'Candidate';
  const colSpan = isSelf ? "col-span-1 sm:col-span-2 md:col-span-1" : "";
  
  // Set up video stream for candidate
  useEffect(() => {
    if (isSelf && isVideoEnabled && stream && videoRef.current && isStreamActive()) {
      console.log("Setting up video stream for candidate");
      videoRef.current.srcObject = stream;
    }
  }, [isSelf, isVideoEnabled, stream, isStreamActive]);
  
  return (
    <div 
      className={cn(
        "video-container rounded-xl overflow-hidden border-2 border-slate-600 bg-slate-800 aspect-video relative transition-all duration-300",
        isActive && "active-speaker border-blue-400 shadow-lg",
        colSpan,
        className
      )}
    >
      {isSelf && isVideoEnabled && isReady && isStreamActive() ? (
        // Show live video stream for candidate
        <video 
          ref={videoRef}
          autoPlay 
          muted 
          playsInline
          className="w-full h-full object-cover" 
        />
      ) : isAI && avatar ? (
        // Show avatar image for AI participants
        <img 
          src={avatar} 
          alt={name} 
          className="w-full h-full object-cover" 
        />
      ) : (
        // Show placeholder for other participants or when video is disabled
        <div className="w-full h-full flex items-center justify-center">
          <div className="h-24 w-24 rounded-full bg-slate-700 flex items-center justify-center text-4xl font-medium text-slate-200">
            {name.charAt(0)}
          </div>
        </div>
      )}
      
      {/* Active Speaker Indicator */}
      <ActiveSpeakerIndicator isActive={isActive} />
      
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-slate-900/90 to-transparent p-3 flex items-center justify-between">
        <div className="flex items-center">
          <div className={cn(
            "text-xs font-medium px-2 py-1 rounded-md mr-2",
            isAI ? "ai-badge" : "human-badge"
          )}>
            {isAI ? "AI" : "You"}
          </div>
          <span className={cn(
            "font-medium",
            isActive ? "text-white" : "text-slate-300"
          )}>
            {name}
          </span>
        </div>
        <div className="flex items-center space-x-2">
          {/* Audio mute indicator for self */}
          {isSelf && (
            <div className={cn(
              "p-1 rounded-full",
              isMicrophoneMuted ? "bg-red-500" : "bg-green-500"
            )}>
              {isMicrophoneMuted ? (
                <MicOff className="w-3 h-3 text-white" />
              ) : (
                <Mic className="w-3 h-3 text-white" />
              )}
            </div>
          )}
          <div className={cn(
            "w-2 h-2 rounded-full",
            connectionStatus === 'connected' ? "bg-green-400" : 
            connectionStatus === 'connecting' ? "bg-yellow-400" : "bg-red-400"
          )}></div>
        </div>
      </div>
      
      {/* Additional active speaker overlay for better visibility */}
      {isActive && (
        <div className="absolute inset-0 border-2 border-blue-400/50 rounded-xl pointer-events-none">
          <div className="absolute top-2 left-2 bg-blue-500 text-white text-xs font-medium px-2 py-1 rounded-md">
            Speaking
          </div>
        </div>
      )}
    </div>
  );
}
