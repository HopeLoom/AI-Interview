import { useState, useRef, useEffect } from 'react';
import { Message, Participant } from '@/lib/types';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Paperclip, Image, SmilePlus, Send, Save } from 'lucide-react';
import { format } from 'date-fns';
import { useUser } from '@/contexts/UserContext';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { cn } from '@/lib/utils';

interface ChatPanelProps {
  messages: Message[];
  participants: Participant[];
  onSendMessage: (message: string, senderId: string, senderName: string) => void;
  isNoteDialogOpenExternal?: boolean;
  onNoteDialogOpenChange?: (open: boolean) => void;
}

export function ChatPanel({
  messages,
  participants,
  onSendMessage,
  isNoteDialogOpenExternal,
  onNoteDialogOpenChange,
}: ChatPanelProps) {
  const [input, setInput] = useState('');
  const [noteInput, setNoteInput] = useState('');
  const [isNoteDialogOpen, setIsNoteDialogOpen] = useState(false);
  const [notes, setNotes] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState('chat'); // Add missing state
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { user } = useUser();

  // Add debugging for messages
  console.log('ChatPanel - messages received:', messages);
  console.log('ChatPanel - participants received:', participants);

  const handleSendMessage = () => {
    if (input.trim()) {
      onSendMessage(input, user?.id || '', user?.name || '');
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Auto-scroll to bottom when new messages are added
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Remove or comment out the auto-scroll effect for now
  useEffect(() => {
    console.log('ChatPanel - messages changed, scrolling to bottom');
    scrollToBottom();
  }, [messages]);

  // Sync internal and external note dialog state
  useEffect(() => {
    if (isNoteDialogOpenExternal !== undefined) {
      setIsNoteDialogOpen(isNoteDialogOpenExternal);
    }
  }, [isNoteDialogOpenExternal]);

  // Notify parent component when internal note dialog state changes
  useEffect(() => {
    if (onNoteDialogOpenChange) {
      onNoteDialogOpenChange(isNoteDialogOpen);
    }
  }, [isNoteDialogOpen, onNoteDialogOpenChange]);

  const getParticipantById = (id: string) => {
    return participants.find((p) => p.id === id);
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('');
  };

  const handleCreateNote = () => {
    setIsNoteDialogOpen(true);
  };

  const handleSaveNote = () => {
    if (noteInput.trim()) {
      setNotes([...notes, noteInput]);
      setNoteInput('');
      setIsNoteDialogOpen(false);
    }
  };

  return (
    <div className="bg-slate-800 border border-slate-600 rounded-xl overflow-hidden h-full flex flex-col">
      {/* Header */}
      <div className="bg-slate-700 border-b border-slate-600 px-4 py-3">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3 bg-slate-600">
            <TabsTrigger
              value="chat"
              className="data-[state=active]:bg-slate-500 data-[state=active]:text-slate-100 text-slate-300"
            >
              Chat
            </TabsTrigger>
            <TabsTrigger
              value="transcript"
              className="data-[state=active]:bg-slate-500 data-[state=active]:text-slate-100 text-slate-300"
            >
              Transcript
            </TabsTrigger>
            <TabsTrigger
              value="notes"
              className="data-[state=active]:bg-slate-500 data-[state=active]:text-slate-100 text-slate-300"
            >
              Notes
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {/* Chat Tab */}
        <TabsContent value="chat" className="h-full flex flex-col m-0">
          <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
            <div className="space-y-4">
              {messages.map((message, index) => {
                const participant = getParticipantById(message.senderId);
                const isOwnMessage = message.senderId === user?.id;

                return (
                  <div
                    key={index}
                    className={cn(
                      'flex items-start space-x-3',
                      isOwnMessage ? 'flex-row-reverse space-x-reverse' : ''
                    )}
                  >
                    {/* Avatar */}
                    <div
                      className={cn(
                        'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium text-white flex-shrink-0',
                        isOwnMessage ? 'bg-blue-500' : 'bg-slate-600'
                      )}
                    >
                      {participant?.avatar ? (
                        <img
                          src={participant.avatar}
                          alt={participant.name}
                          className="w-full h-full rounded-full object-cover"
                        />
                      ) : (
                        getInitials(participant?.name || 'Unknown')
                      )}
                    </div>

                    {/* Message */}
                    <div className={cn('flex-1 max-w-[80%]', isOwnMessage ? 'text-right' : '')}>
                      <div
                        className={cn(
                          'rounded-lg px-3 py-2',
                          isOwnMessage
                            ? 'bg-blue-500 text-white ml-auto'
                            : 'bg-slate-700 text-slate-100'
                        )}
                      >
                        <p className="text-sm">{message.content}</p>
                      </div>
                      <div
                        className={cn(
                          'text-xs text-slate-400 mt-1',
                          isOwnMessage ? 'text-right' : ''
                        )}
                      >
                        {format(new Date(message.timestamp), 'HH:mm')}
                      </div>
                    </div>
                  </div>
                );
              })}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          {/* Input */}
          <div className="p-4 border-t border-slate-600">
            <div className="flex space-x-2">
              <Textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your message..."
                className="flex-1 bg-slate-700 border-slate-600 text-slate-100 placeholder:text-slate-400 focus:border-blue-400 focus:ring-blue-400/20 focus:bg-slate-600 resize-none"
                rows={2}
              />
              <Button
                onClick={handleSendMessage}
                disabled={!input.trim()}
                className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </TabsContent>

        {/* Transcript Tab */}
        <TabsContent value="transcript" className="h-full m-0">
          <ScrollArea className="h-full p-4">
            <div className="space-y-4">
              {messages.map((message, index) => {
                const participant = getParticipantById(message.senderId);
                return (
                  <div key={index} className="p-3 bg-slate-700 rounded-lg border border-slate-600">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-slate-200">
                        {participant?.name || 'Unknown'}
                      </span>
                      <span className="text-xs text-slate-400">
                        {format(new Date(message.timestamp), 'HH:mm:ss')}
                      </span>
                    </div>
                    <p className="text-slate-300 text-sm">{message.content}</p>
                  </div>
                );
              })}
            </div>
          </ScrollArea>
        </TabsContent>

        {/* Notes Tab */}
        <TabsContent value="notes" className="h-full m-0">
          <div className="p-4 h-full flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-slate-100">Interview Notes</h3>
              <Button
                onClick={handleCreateNote}
                className="bg-blue-500 hover:bg-blue-600 text-white"
              >
                <Save className="w-4 h-4 mr-2" />
                New Note
              </Button>
            </div>

            <ScrollArea className="flex-1">
              <div className="space-y-3">
                {notes.map((note, index) => (
                  <div key={index} className="p-3 bg-slate-700 rounded-lg border border-slate-600">
                    <p className="text-slate-300 text-sm">{note}</p>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>
        </TabsContent>
      </div>

      {/* Note Creation Dialog */}
      <Dialog open={isNoteDialogOpen} onOpenChange={setIsNoteDialogOpen}>
        <DialogContent className="bg-slate-800 border-slate-600 text-slate-100">
          <DialogHeader>
            <DialogTitle className="text-slate-100">Create Note</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <Textarea
              value={noteInput}
              onChange={(e) => setNoteInput(e.target.value)}
              placeholder="Write your note here..."
              className="bg-slate-700 border-slate-600 text-slate-100 placeholder:text-slate-400 focus:border-blue-400 focus:ring-blue-400/20 focus:bg-slate-600"
              rows={4}
            />
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsNoteDialogOpen(false)}
              className="border-slate-600 text-slate-300 hover:bg-slate-700"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSaveNote}
              disabled={!noteInput.trim()}
              className="bg-blue-500 hover:bg-blue-600 text-white"
            >
              Save Note
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
