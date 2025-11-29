import { Button } from '@/components/ui/button';
import { Dialog, DialogContent } from '@/components/ui/dialog';
import { PanelData } from '@/lib/common';

interface InterviewIntroScreenProps {
  isOpen: boolean;
  onClose: () => void;
  role: string;
  company?: string;
  interviewType: string;
  panelists: PanelData[];
  introduction: string;
}

export function InterviewIntroScreen({
  isOpen,
  onClose,
  role,
  company,
  interviewType,
  panelists,
  introduction
}: InterviewIntroScreenProps) {
  return (
    <Dialog open={isOpen} onOpenChange={() => {}}>
      <DialogContent className="max-w-3xl p-0 overflow-hidden bg-white" onPointerDownOutside={(e) => e.preventDefault()} onEscapeKeyDown={(e) => e.preventDefault()}>
        <div className="p-6">
          {/* Header with logo */}
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 text-blue-500">
              {/* HopeLoom logo - simplified representation */}
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L8 6L4 2L2 4L6 8L2 12L4 14L8 10L12 14L16 10L20 14L22 12L18 8L22 4L20 2L16 6L12 2Z" fill="currentColor" />
                <circle cx="12" cy="8" r="2" fill="currentColor" />
                <circle cx="8" cy="12" r="2" fill="currentColor" />
                <circle cx="16" cy="12" r="2" fill="currentColor" />
                <circle cx="12" cy="16" r="2" fill="currentColor" />
              </svg>
            </div>
          </div>
          
          {/* Title */}
          <h1 className="text-2xl font-bold text-center mb-4">
            Prescreening Interview Powered by HopeLoom
          </h1>
          
          {/* Description */}
          <p className="text-center mb-8 text-neutral-700">
            {introduction}
          </p>
          
          {/* Panelists */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            {panelists.map((panelist, index) => (
              <div key={index} className="border border-neutral-200 rounded-lg p-4 bg-neutral-50">
                <h3 className="font-bold text-lg mb-2">{panelist.name}</h3>
                <p className="text-neutral-600 text-sm italic mb-2">{panelist.interview_round_part_of}</p>
                <p className="text-neutral-700 text-sm">{panelist.intro}</p>
              </div>
            ))}
          </div>
          
          {/* Call to action button */}
          <div className="flex justify-center">
            <Button 
              onClick={onClose}
              className="bg-blue-600 hover:bg-blue-700 py-2 px-6 text-base"
            >
              OK
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}