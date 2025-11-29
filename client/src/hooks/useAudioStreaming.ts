import { useRef, useCallback } from 'react';
import { useUser } from '@/contexts/UserContext';
import webSocketService from '@/lib/websocketService';
import { ttStreamingService } from '@/lib/audioStreamingService';
import { 
  WebSocketMessageTypeToServer, 
  TextToSpeechDataMessageToServer,
  AudioPlaybackCompletedDataToServer,
  TextToSpeechDataMessageFromServer,
  ConvertedSpeechFromServer,
  InterviewMessageToServer
} from '@/lib/common';

interface UseAudioStreamingProps {
  onAddMessage: (text: string, speakerId: string, speakerName: string) => void;
  onError: (message: string, id: string) => void;
}

export function useAudioStreaming({ onAddMessage, onError }: UseAudioStreamingProps) {
  const { user } = useUser();
  const audioQueueRef = useRef<Uint8Array[]>([]);
  const minBufferedChunks = 16;
  const streamingCompletedRef = useRef(false);

  const runTextToSpeech = useCallback(async (voice_name: string, text: string) => {
    console.log("Running text to speech:", voice_name, text);
    const textToSpeechData: TextToSpeechDataMessageToServer = { 
      voice_name: voice_name, 
      text: text 
    };
    if (user) {
      webSocketService.sendMessage(
        user.email, 
        WebSocketMessageTypeToServer.START_AUDIO_STREAMING, 
        textToSpeechData
      );
    }
  }, []);

  const processTextFromSpeech = useCallback((text: string, speaker_name: string) => {
    console.log("Transcript from speech:", text);
    if (user) {
      const interviewMessage: InterviewMessageToServer = { 
        speaker: speaker_name, 
        message: text, 
        activity_data: "" 
      };
      webSocketService.sendMessage(
        user.email, 
        WebSocketMessageTypeToServer.INTERVIEW_DATA, 
        interviewMessage
      );

      // Add message to chat panel - use user.id instead of user.name for speakerId
      onAddMessage(text, user.id, speaker_name);
    } else {
      console.error("User data not found");
    }
  }, []);

  const sendPlaybackCompletedMessage = useCallback(() => {
    const audioPlaybackCompletedData: AudioPlaybackCompletedDataToServer = { 
      isAudioPlaybackCompleted: true 
    };
    if (user) {
      webSocketService.sendMessage(
        user.email,
        WebSocketMessageTypeToServer.AUDIO_PLAYBACK_COMPLETED,
        audioPlaybackCompletedData
      );
      console.log("Sent AUDIO_PLAYBACK_COMPLETED message to backend.");
    } else {
      console.error("User data not found, could not send completion message.");
    }
  }, []);

  const createAudioStream = useCallback(() => {
    return {
      async *[Symbol.asyncIterator]() {
        while (true) {
          while (audioQueueRef.current.length > 0) {
            yield audioQueueRef.current.shift()!;
          }
          console.warn("No new audio data, waiting...");
          
          await new Promise<void>(resolve => {
            const checkQueue = setInterval(() => {
              if (audioQueueRef.current.length > 0) {
                clearInterval(checkQueue);
                resolve();
              } else if (streamingCompletedRef.current) {
                console.log("Streaming is complete, exiting stream.");
                clearInterval(checkQueue);
                resolve();
                return;
              }
            }, 100);
          });
          
          if (streamingCompletedRef.current && audioQueueRef.current.length === 0) {
            console.log("No more audio data, stopping stream.");
            break;
          }
        }
      }
    };
  }, []);

  const handleAudioChunks = useCallback(async (data: string, id: string) => {
    console.log("Audio chunks received:", data);
    const audioData: TextToSpeechDataMessageFromServer = JSON.parse(data);
    let audio_data = audioData.audio_data;

    // Convert Base64 to Uint8Array
    const binaryData = Uint8Array.from(atob(audio_data), c => c.charCodeAt(0));
    
    // If streaming has completed, clear old data and start fresh
    if (streamingCompletedRef.current) {
      console.warn("Streaming was completed previously. Resetting queue for new audio.");
      audioQueueRef.current = [];
      streamingCompletedRef.current = false;
    }

    audioQueueRef.current.push(binaryData);
    console.log(`Buffer size: ${audioQueueRef.current.length} chunks`);

    // If already playing, just keep appending new data
    if (ttStreamingService.isPlaying) {
      console.log("Already playing, appending new data...");
      return;
    }

    // Only start playback when enough chunks are buffered
    if (audioQueueRef.current.length >= minBufferedChunks) {
      console.log("Enough audio buffered, starting playback...");
      const audioStream = createAudioStream();

      await ttStreamingService.playStreamedAudio(audioStream, () => {
        console.log("Playback complete.");
        
        if (audioQueueRef.current.length === 0) {
          console.log("Clearing queue after playback.");
          audioQueueRef.current = [];
          sendPlaybackCompletedMessage();
        } else {
          console.log("New data arrived, keeping queue.");
        }
      }, () => {
        console.error("Error during playback.");
        audioQueueRef.current = [];
        onError("Error during playback", id);
      });
    }
  }, []);

  const handleAudioStreamingCompleted = useCallback(async (data: string, id: string) => {
    console.log("Audio streaming completed:", data);
    streamingCompletedRef.current = true;

    if (audioQueueRef.current.length > 0) {
      console.log("Finalizing playback with remaining queued audio...");
      const audioStream = createAudioStream();

      await ttStreamingService.playStreamedAudio(audioStream, () => {
        console.log("All remaining audio played, queue cleared.");
        audioQueueRef.current = [];
        sendPlaybackCompletedMessage();
      }, () => {
        console.error("Error during final playback.");
        audioQueueRef.current = [];
        onError("Error during final playback", id);
      });
    } else {
      console.log("No remaining audio, clearing queue.");
      audioQueueRef.current = [];
      sendPlaybackCompletedMessage();
    }
  }, []);

  const handleTextFromSpeech = useCallback((data: string, id: string) => {
    console.log("Text from speech received:", data);
    const speechData: ConvertedSpeechFromServer = JSON.parse(data);
    console.log("Converted speech:", speechData.text);
    processTextFromSpeech(speechData.text, speechData.speaker_name);
  }, []);

  return {
    runTextToSpeech,
    handleAudioChunks,
    handleAudioStreamingCompleted,
    handleTextFromSpeech,
    processTextFromSpeech
  };
} 