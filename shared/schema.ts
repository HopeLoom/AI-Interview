// Simple TypeScript interfaces for frontend use
// These replace the drizzle schema that was causing import issues

export interface User {
  id: number;
  username: string;
  name: string;
  email: string;
  avatarUrl?: string;
  createdAt: Date;
}

export interface InterviewSession {
  id: number;
  title: string;
  description?: string;
  startedAt: Date;
  endedAt?: Date;
  status: string;
  candidateId: number;
  problemStatement?: string;
  interviewType: string;
  currentStep: number;
}

export interface Participant {
  id: number;
  sessionId: number;
  userId?: number;
  name: string;
  avatarUrl?: string;
  isAI: boolean;
  role: string;
  connectionStatus: string;
}

export interface Message {
  id: number;
  sessionId: number;
  participantId: number;
  content: string;
  timestamp: Date;
  metadata?: any;
}

// Insert types (for creating new records)
export type InsertUser = Omit<User, 'id' | 'createdAt'>;
export type InsertInterviewSession = Omit<InterviewSession, 'id' | 'startedAt' | 'endedAt' | 'status' | 'currentStep'>;
export type InsertParticipant = Omit<Participant, 'id'>;
export type InsertMessage = Omit<Message, 'id' | 'timestamp'>;
