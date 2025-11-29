import React, { createContext, useContext, ReactNode } from 'react';
import { useCameraStream } from '@/hooks/useCameraStream';

interface CameraContextType {
  // State
  stream: MediaStream | null;
  isReady: boolean;
  isStarting: boolean;
  error: string | null;
  isMicrophoneMuted: boolean; // Add this
  
  // Actions
  startStream: () => Promise<void>;
  stopStream: () => void;
  restartStream: () => Promise<void>;
  toggleMicrophone: () => void; // Add this
  muteMicrophone: () => void; // Add this
  unmuteMicrophone: () => void; // Add this
  
  // Utilities
  getVideoElement: () => HTMLVideoElement | null;
  isStreamActive: () => boolean;
}

const CameraContext = createContext<CameraContextType | undefined>(undefined);

export const useCamera = () => {
  const context = useContext(CameraContext);
  if (!context) {
    throw new Error('useCamera must be used within a CameraProvider');
  }
  return context;
};

interface CameraProviderProps {
  children: ReactNode;
}

export const CameraProvider: React.FC<CameraProviderProps> = ({ children }) => {
  const cameraStream = useCameraStream();

  return (
    <CameraContext.Provider value={cameraStream}>
      {children}
    </CameraContext.Provider>
  );
}; 