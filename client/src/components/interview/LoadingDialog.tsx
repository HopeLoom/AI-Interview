import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import { Loader2 } from 'lucide-react';

interface LoadingDialogProps {
  isOpen: boolean;
  title?: string;
  description?: string;
  progress?: number;
}

export function LoadingDialog({
  isOpen,
  title = 'Getting Interview Information',
  description = 'Please wait while we prepare your interview...',
  progress,
}: LoadingDialogProps) {
  return (
    <Dialog open={isOpen} onOpenChange={() => {}}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-center space-x-2">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span>{title}</span>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <p className="text-center text-sm text-muted-foreground">{description}</p>

          {progress !== undefined && (
            <div className="space-y-2">
              <Progress value={progress} className="w-full" />
              <p className="text-center text-xs text-muted-foreground">{progress}% complete</p>
            </div>
          )}

          {progress === undefined && (
            <div className="flex justify-center">
              <div className="animate-pulse">
                <div className="h-2 bg-muted rounded w-32"></div>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
