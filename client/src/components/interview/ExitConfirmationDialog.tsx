import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

interface ExitConfirmationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

export function ExitConfirmationDialog({
  isOpen,
  onClose,
  onConfirm,
}: ExitConfirmationDialogProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md bg-slate-800 border-slate-600 text-slate-100">
        <DialogHeader>
          <DialogTitle className="text-slate-100">End Interview?</DialogTitle>
          <DialogDescription className="text-slate-300">
            Are you sure you want to leave this interview? Your progress will be saved.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="flex flex-row justify-end gap-2 sm:gap-0">
          <Button
            variant="outline"
            onClick={onClose}
            className="border-slate-600 text-slate-300 hover:bg-slate-700 hover:border-slate-500 hover:text-slate-200"
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={onConfirm}
            className="bg-red-500 hover:bg-red-600 text-white"
          >
            End Interview
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
