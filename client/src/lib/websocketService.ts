class EventEmitter {
  private events: { [key: string]: Function[] } = {};

  on(event: string, listener: Function) {
    if (!this.events[event]) {
      this.events[event] = [];
    }
    this.events[event].push(listener);
  }

  off(event: string, listener: Function) {
    if (!this.events[event]) return;
    this.events[event] = this.events[event].filter(l => l !== listener);
  }

  emit(event: string, ...args: any[]) {
    if (!this.events[event]) return;
    this.events[event].forEach(listener => listener(...args));
  }

  listenerCount(event: string): number {
    return this.events[event] ? this.events[event].length : 0;
  }
}

import {
  WebSocketMessageTypeToServer,
  WebSocketMessageTypeFromServer,
  InstructionDataToServer,
  UserLoginDataToServer,
  UserLogoutDataToServer,
  InterviewEndDataToServer,
  InterviewMessageToServer,
  InterviewStartDataToServer,
  AudioPlaybackCompletedDataToServer,
  ActivityInfoDataToServer,
  SpeechDataToServer,
  TextToSpeechDataMessageToServer
} from "./common";

class WebSocketService {
  private static instance: WebSocketService;
  private socket: WebSocket | null = null;
  private eventEmitter = new EventEmitter();
  private reconnectInterval = 5000;
  private maxRetries = 5;
  private retryCount = 0;
  private isManuallyClosed = false;
  private url: string = "";
  private isConnected = false;
  private reconnecting = false;

  private constructor() {}

  static getInstance() {
    if (!WebSocketService.instance) {
      WebSocketService.instance = new WebSocketService();
    }
    return WebSocketService.instance;
  }

  connect(url: string) {
    console.log("Connecting to WebSocket...");
    if (this.isConnected) return;
    this.url = url;
    this.isManuallyClosed = false;
    this.retryCount = 0;
    this.initializeWebSocket();
  }

  private initializeWebSocket() {
    this.socket = new WebSocket(this.url);

    this.socket.onopen = () => {
      console.log("WebSocket connected.");
      this.eventEmitter.emit(WebSocketMessageTypeFromServer.CONNECTION, "WebSocket connected successfully.");
      this.isConnected = true;
      this.reconnecting = false;
      this.retryCount = 0;
    };

    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.eventEmitter.emit(data.message_type, data.message, data.id);
    };

    this.socket.onclose = () => {
      console.log("WebSocket disconnected.");
      this.isConnected = false;
      this.socket = null;

      if (!this.isManuallyClosed && this.retryCount < this.maxRetries) {
        if (!this.reconnecting) {
          this.reconnecting = true;
          this.retryCount++;
          console.log(`Reconnecting in ${this.reconnectInterval / 1000} seconds... (Attempt ${this.retryCount})`);
          setTimeout(() => {
            this.initializeWebSocket();
            this.reconnecting = false;
          }, this.reconnectInterval);
        }
      } else if (this.retryCount >= this.maxRetries) {
        this.eventEmitter.emit(WebSocketMessageTypeFromServer.ERROR, "WebSocket encountered an error or cannot connect.");
        console.error("Maximum retry attempts reached. Unable to reconnect.");
      }
    };

    this.socket.onerror = (error) => {
      console.error("WebSocket error:", error);
      this.socket?.close();
    };
  }

  disconnect() {
    this.isManuallyClosed = true;
    this.socket?.close();
    this.socket = null;
    this.isConnected = false;
    this.reconnecting = false;
    this.retryCount = 0;
  }

  sendMessage(
    id: string,
    message_type: WebSocketMessageTypeToServer,
    message:
      | InstructionDataToServer
      | UserLoginDataToServer
      | UserLogoutDataToServer
      | InterviewEndDataToServer
      | InterviewMessageToServer
      | InterviewStartDataToServer
      | AudioPlaybackCompletedDataToServer
      | ActivityInfoDataToServer
      | SpeechDataToServer
      | TextToSpeechDataMessageToServer
  ) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ message_type, message, id }));
    } else {
      console.error("WebSocket is not open. Message not sent:", { message_type, message, id });
      this.eventEmitter.emit(WebSocketMessageTypeFromServer.ERROR, "Unable to connect to WebSocket after multiple attempts.");
    }
  }

  on(eventType: WebSocketMessageTypeFromServer, listener: (data: any, id: string) => void) {
    this.eventEmitter.on(eventType as unknown as string, listener);
  }

  off(eventType: WebSocketMessageTypeFromServer, listener: (data: any, id: string) => void) {
    this.eventEmitter.off(eventType as unknown as string, listener);
  }
}

const webSocketService = WebSocketService.getInstance();
export default webSocketService;
