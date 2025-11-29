import { useState, useRef, useCallback, useEffect } from 'react';

interface CameraStreamState {
  stream: MediaStream | null;
  isReady: boolean;
  isStarting: boolean;
  error: string | null;
  isMicrophoneMuted: boolean;
}

interface UseCameraStreamReturn {
  // State
  stream: MediaStream | null;
  isReady: boolean;
  isStarting: boolean;
  error: string | null;
  isMicrophoneMuted: boolean;
  
  // Actions
  startStream: () => Promise<void>;
  stopStream: () => void;
  restartStream: () => Promise<void>;
  toggleMicrophone: () => void;
  muteMicrophone: () => void;
  unmuteMicrophone: () => void;
  
  // Utilities
  getVideoElement: () => HTMLVideoElement | null;
  getAudioTrack: () => MediaStreamTrack | null;
  isStreamActive: () => boolean;
}

export function useCameraStream(): UseCameraStreamReturn {
  const [state, setState] = useState<CameraStreamState>({
    stream: null,
    isReady: false,
    isStarting: false,
    error: null,
    isMicrophoneMuted: false
  });

  const streamRef = useRef<MediaStream | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const updateState = useCallback((updates: Partial<CameraStreamState>) => {
    setState(prev => ({ ...prev, ...updates }));
  }, []);

  const startStream = useCallback(async () => {
    if (state.isStarting || state.isReady) {
      console.log("Camera stream already starting or ready");
      return;
    }

    try {
      updateState({ isStarting: true, error: null });
      
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'user'
        },
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      streamRef.current = mediaStream;
      
      // Mute microphone by default
      const audioTrack = mediaStream.getAudioTracks()[0];
      if (audioTrack) {
        audioTrack.enabled = false;
      }
      
      updateState({
        stream: mediaStream,
        isReady: true,
        isStarting: false,
        error: null,
        isMicrophoneMuted: true // Set to true by default
      });

      console.log("Camera stream started successfully with microphone muted by default");
    } catch (error) {
      console.error("Failed to start camera stream:", error);
      updateState({
        isStarting: false,
        error: error instanceof Error ? error.message : "Failed to access camera"
      });
    }
  }, [state.isStarting, state.isReady, updateState]);

  const toggleMicrophone = useCallback(() => {
    if (!streamRef.current) return;

    const audioTrack = streamRef.current.getAudioTracks()[0];
    if (audioTrack) {
      const newMutedState = !audioTrack.enabled;
      audioTrack.enabled = newMutedState;
      updateState({ isMicrophoneMuted: !newMutedState });
      console.log(`Microphone ${newMutedState ? 'unmuted' : 'muted'}`);
    }
  }, [updateState]);

  const muteMicrophone = useCallback(() => {
    if (!streamRef.current) return;

    const audioTrack = streamRef.current.getAudioTracks()[0];
    if (audioTrack) {
      audioTrack.enabled = false;
      updateState({ isMicrophoneMuted: true });
      console.log("Microphone muted");
    }
  }, [updateState]);

  const unmuteMicrophone = useCallback(() => {
    if (!streamRef.current) return;

    const audioTrack = streamRef.current.getAudioTracks()[0];
    if (audioTrack) {
      audioTrack.enabled = true;
      updateState({ isMicrophoneMuted: false });
      console.log("Microphone unmuted");
    }
  }, [updateState]);

  const stopStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => {
        track.stop();
      });
      streamRef.current = null;
    }

    updateState({
      stream: null,
      isReady: false,
      isStarting: false,
      error: null,
      isMicrophoneMuted: false
    });

    console.log("Camera stream stopped");
  }, [updateState]);

  const restartStream = useCallback(async () => {
    stopStream();
    await new Promise(resolve => setTimeout(resolve, 100));
    await startStream();
  }, [stopStream, startStream]);

  const getVideoElement = useCallback(() => {
    return videoRef.current;
  }, []);

  const getAudioTrack = useCallback(() => {
    if (!streamRef.current) return null;
    return streamRef.current.getAudioTracks()[0] || null;
  }, []);

  const isStreamActive = useCallback(() => {
    return streamRef.current !== null && state.isReady;
  }, [state.isReady]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopStream();
    };
  }, [stopStream]);

  return {
    // State
    stream: state.stream,
    isReady: state.isReady,
    isStarting: state.isStarting,
    error: state.error,
    isMicrophoneMuted: state.isMicrophoneMuted,
    
    // Actions
    startStream,
    stopStream,
    restartStream,
    toggleMicrophone,
    muteMicrophone,
    unmuteMicrophone,
    
    // Utilities
    getVideoElement,
    getAudioTrack,
    isStreamActive
  };
} 