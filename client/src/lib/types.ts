import { PanelData } from "./common";
export enum InterviewRound { 
  ROUND_ONE = "HR_ROUND",
  ROUND_TWO = "TECHNICAL_ROUND",
  ROUND_THREE = "BEHAVIORAL_ROUND"
}

export interface Participant {
  id: string;
  name: string;
  avatar?: string;
  isAI: boolean;
  isActive: boolean;
  intro:string;
  interview_round_part_of: InterviewRound;
  connectionStatus: 'connected' | 'connecting' | 'disconnected';
}

export interface Message {
  id: string;
  senderId: string;
  senderName: string;
  content: string;
  timestamp: Date;
  isTyping?: boolean;
}

export interface InterviewStep {
  id: number;
  name: string;
  status: 'completed' | 'active' | 'upcoming';
}

export type ConnectionStatus = 'connected' | 'muted' | 'disabled' | 'connecting';

export interface InterviewState {
  title: string;
  startTime: Date;
  participants: PanelData[];
  messages: Message[];
  currentStep: number;
  interviewSteps: InterviewStep[];
  isAudioEnabled: boolean;
  isVideoEnabled: boolean;
  isScreenSharing: boolean;
  isProblemVisible: boolean;
  isTimerVisible: boolean;
  showLiveCodingTimer: boolean;
  isLiveCoding: boolean;
  problemStatement: string;
  elapsedTime: number;
  liveCodingTimeRemaining: number;
  currentTopic: string;
  currentSubTopic: string;
  currentSpeakerID: string;
  starterCode: string;
  candidateCode: string;
}


export interface Candidate {
  id: string;
  name: string;
  email: string;
  position: string;
  status: string;
  interview_date: string;
  overall_score: number;
}