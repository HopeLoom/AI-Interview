import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Check, Lock, Video, Camera } from 'lucide-react';
import { useUser } from '@/contexts/UserContext';
import { useCamera } from '@/contexts/CameraContext';

interface ReadyToJoinScreenProps {
  isOpen: boolean;
  onJoin: () => void;
  onCancel?: () => void;
}

export function ReadyToJoinScreen({
  isOpen,
  onJoin,
  onCancel
}: ReadyToJoinScreenProps) {
  const { user } = useUser();
  const { 
    stream, 
    isReady, 
    isStarting, 
    error, 
    startStream, 
    stopStream
  } = useCamera();
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const imageTimerRef = useRef<NodeJS.Timeout | null>(null);
  const [hasCapturedImage, setHasCapturedImage] = useState(false);
  const [isCapturing, setIsCapturing] = useState(false);
  const [videoReady, setVideoReady] = useState(false);

  // Start camera when dialog opens
  useEffect(() => {
    if (isOpen && !isReady && !isStarting) {
      startStream();
    }
    
    return () => {
      stopCaptureLoop();
    };
  }, [isOpen, isReady, isStarting, startStream]);

  // Set video element when stream is ready
  useEffect(() => {
    if (stream && videoRef.current) {
      videoRef.current.srcObject = stream;
      
      // Add event listeners for video readiness
      const video = videoRef.current;
      
      const handleLoadedMetadata = () => {
        console.log("Video metadata loaded");
        setVideoReady(true);
        // Don't start capture loop here, wait for playing event
      };
      
      const handleCanPlay = () => {
        console.log("Video can play");
        setVideoReady(true);
        // Don't start capture loop here, wait for playing event
      };
      
      const handlePlaying = () => {
        console.log("Video is playing");
        setVideoReady(true);
        // Start capture loop when video is actually playing
        startCaptureLoop();
      };
      
      video.addEventListener('loadedmetadata', handleLoadedMetadata);
      video.addEventListener('canplay', handleCanPlay);
      video.addEventListener('playing', handlePlaying);
      
      return () => {
        video.removeEventListener('loadedmetadata', handleLoadedMetadata);
        video.removeEventListener('canplay', handleCanPlay);
        video.removeEventListener('playing', handlePlaying);
      };
    }
  }, [stream]);

  const captureFrame = async () => {
    const video = videoRef.current;
    
    if (!video) {
      console.warn("Video element not found");
      return;
    }
    
    // Check if video is actually ready with content
    if (video.videoWidth === 0 || video.videoHeight === 0) {
      console.warn("Video dimensions not ready yet, retrying...");
      setTimeout(() => captureFrame(), 100);
      return;
    }
    
    // Additional check to ensure video is actually playing
    if (video.paused || video.ended) {
      console.warn("Video is not playing, retrying...");
      setTimeout(() => captureFrame(), 100);
      return;
    }

    console.log(`Capturing frame with dimensions: ${video.videoWidth}x${video.videoHeight}`);

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");
    if (!ctx) {
      console.error("Canvas context not available");
      return;
    }

    try {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      canvas.toBlob(async (blob) => {
        if (!blob) {
          console.error("Failed to create blob from canvas");
          return;
        }

        const formData = new FormData();
        const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
        formData.append("user_id", user?.email || "unknown");
        formData.append("image", blob, `frame_${timestamp}.jpg`);
        
        const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;
        
        try {
          setIsCapturing(true);
          const response = await fetch(`https://${apiBaseUrl}/upload_image`, {
            method: "POST",
            body: formData,
          });
          
          if (response.ok) {
            console.log("Image sent successfully");
            setHasCapturedImage(true);
            stopCaptureLoop();
          } else {
            console.error("Failed to upload image:", response.statusText);
          }
        } catch (error) {
          console.error("Failed to send image", error);
        } finally {
          setIsCapturing(false);
        }
      }, "image/jpeg", 0.95);
    } catch (error) {
      console.error("Error drawing video to canvas:", error);
    }
  };

  const startCaptureLoop = () => {
    console.log("Starting capture loop...");
    // Remove the videoReady check since we're calling this from the playing event
    if (!imageTimerRef.current) {
      // Wait a bit more to ensure video is fully ready
      setTimeout(() => {
        console.log("Executing capture frame...");
        if ("requestVideoFrameCallback" in HTMLVideoElement.prototype) {
          videoRef.current?.requestVideoFrameCallback(() => {
            captureFrame();
          });
        } else {
          captureFrame();
        }
  
        imageTimerRef.current = setInterval(() => {
          console.log("Interval capture frame...");
          captureFrame();
        }, 5000);
      }, 1000); // Reduced delay since video is already playing
    }
  };

  const stopCaptureLoop = () => {
    console.log("Stopping capture loop...");
    if (imageTimerRef.current) {
      clearInterval(imageTimerRef.current);
      imageTimerRef.current = null;
    }
  };

  const handleJoin = () => {
    stopCaptureLoop();
    onJoin();
  };

  const handleCancel = () => {
    stopCaptureLoop();
    onCancel?.();
  };

  return (
    <Dialog open={isOpen} onOpenChange={() => {}}>
      <DialogContent 
        className="max-w-2xl p-0 overflow-hidden bg-white" 
        onPointerDownOutside={(e) => e.preventDefault()} 
        onEscapeKeyDown={(e) => e.preventDefault()}
      >
        <DialogTitle className="sr-only">Ready to Join?</DialogTitle>
        <DialogDescription className="sr-only">Camera and microphone check before joining interview</DialogDescription>
        
        <div className="p-6">
          <h2 className="text-2xl font-bold text-center mb-5">Ready to Join?</h2>
          
          <div className="bg-blue-50 rounded-lg p-4 mb-6 text-blue-800">
            <p className="font-medium mb-3">This is a video interview.</p>
            <ul className="space-y-2">
              <li className="flex items-center">
                <Check className="h-5 w-5 text-green-600 mr-2 flex-shrink-0" />
                <span>Keep your camera on during the interview. <span className="font-semibold">Only unmute your microphone when speaking</span>, and mute it when listening to prevent AI from detecting background noise.</span>
              </li>
              <li className="flex items-center">
                <Video className="h-5 w-5 text-blue-600 mr-2 flex-shrink-0" />
                <span>Your interview will be <span className="font-semibold">recorded</span> for evaluation purposes.</span>
              </li>
              <li className="flex items-center">
                <Lock className="h-5 w-5 text-blue-600 mr-2 flex-shrink-0" />
                <span>Recordings are securely stored and used strictly for interview review.</span>
              </li>
            </ul>
          </div>
          
          <div className="rounded-lg overflow-hidden border border-neutral-200 mb-6 relative aspect-video">
            {isReady ? (
              <div className="relative">
                <video 
                  ref={videoRef}
                  autoPlay 
                  muted 
                  playsInline
                  className="w-full h-full object-cover"
                />
                {isCapturing && (
                  <div className="absolute top-2 right-2 bg-blue-600 text-white px-2 py-1 rounded-full text-xs flex items-center">
                    <Camera className="w-3 h-3 mr-1" />
                    Capturing...
                  </div>
                )}
                {hasCapturedImage && (
                  <div className="absolute top-2 right-2 bg-green-600 text-white px-2 py-1 rounded-full text-xs flex items-center">
                    <Check className="w-3 h-3 mr-1" />
                    Image Captured
                  </div>
                )}
              </div>
            ) : (
              <div className="w-full h-full bg-neutral-100 flex items-center justify-center">
                <div className="text-center text-neutral-500">
                  <Video className="h-10 w-10 mx-auto mb-2 opacity-50" />
                  <p>{isStarting ? "Starting camera..." : error || "Camera unavailable"}</p>
                  {!isStarting && (
                    <button 
                      onClick={startStream}
                      className="mt-2 text-sm text-blue-600 hover:underline"
                    >
                      Enable camera
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
          
          <div className="flex justify-center gap-4 p-6">
            <Button 
              onClick={handleJoin}
              disabled={!hasCapturedImage || isCapturing}
              className="bg-blue-600 hover:bg-blue-700 py-2 px-6 text-base"
            >
              <Video className="w-4 h-4 mr-2" />
              Join Interview
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}