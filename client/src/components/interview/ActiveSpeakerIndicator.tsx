import { Mic } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ActiveSpeakerIndicatorProps {
  isActive: boolean;
  className?: string;
}

export function ActiveSpeakerIndicator({ isActive, className }: ActiveSpeakerIndicatorProps) {
  if (!isActive) return null;

  return (
    <div className={cn('absolute top-2 right-2 flex items-center space-x-1', className)}>
      <div className="bg-primary text-white text-xs font-medium px-2 py-1 rounded-full flex items-center shadow-lg">
        <Mic className="w-3 h-3 mr-1 animate-pulse" />
        <span>LIVE</span>
      </div>
    </div>
  );
}
