import { useState } from "react";
import { useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { useToast } from "@/hooks/use-toast";
import { apiClient } from "@/services/apiClient";
import { Loader2, KeyRound } from "lucide-react";
import { useUser } from "@/contexts/UserContext";

interface JoinByCodeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function JoinByCodeDialog({ open, onOpenChange }: JoinByCodeDialogProps) {
  const [invitationCode, setInvitationCode] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [, setLocation] = useLocation();
  const { toast } = useToast();
  const { user } = useUser();

  const handleJoinInterview = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!invitationCode.trim()) {
      toast({
        title: "Code Required",
        description: "Please enter an invitation code",
        variant: "destructive"
      });
      return;
    }

    if (!user?.id) {
      toast({
        title: "Not Logged In",
        description: "Please log in first",
        variant: "destructive"
      });
      return;
    }

    setIsLoading(true);

    try {
      const response = await apiClient.post("/api/configurations/join-by-code", {
        invitation_code: invitationCode.trim().toUpperCase(),
        candidate_id: user.id,
        candidate_email: user.email || user.id  // Pass email for auto-registration
      });

      if (response.data.success) {
        const { configuration, company, session_id } = response.data;
        const companyName = company?.name || 'the company';

        toast({
          title: "Success!",
          description: `Successfully joined ${companyName}'s interview. Redirecting...`,
        });

        // Navigate to interview page with configuration ID
        const configId = response.data.configuration_id;
        setTimeout(() => {
          setLocation(`/interview?config_id=${configId}&session_id=${session_id}`);
          onOpenChange(false);
        }, 500);
      } else {
        throw new Error(response.data.message || "Failed to join interview");
      }
    } catch (error: any) {
      console.error("Error joining interview:", error);
      toast({
        title: "Failed to Join",
        description: error.response?.data?.detail || error.message || "Invalid invitation code. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md bg-slate-800 border-slate-700">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center gap-2">
            <KeyRound className="w-5 h-5 text-blue-400" />
            Join Interview
          </DialogTitle>
          <DialogDescription className="text-slate-300">
            Enter the invitation code shared by the company to join the interview
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleJoinInterview} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="invitation-code" className="text-slate-200">
              Invitation Code
            </Label>
            <Input
              id="invitation-code"
              placeholder="ABC123"
              value={invitationCode}
              onChange={(e) => setInvitationCode(e.target.value.toUpperCase())}
              className="bg-slate-700 border-slate-600 text-white font-mono text-2xl text-center tracking-widest"
              maxLength={6}
              disabled={isLoading}
            />
            <p className="text-xs text-slate-400">
              Enter the 6-character code (e.g., ABC123)
            </p>
          </div>

          <div className="flex gap-2 justify-end">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              className="border-slate-600 text-slate-200 hover:bg-slate-700"
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isLoading || !invitationCode.trim()}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Joining...
                </>
              ) : (
                "Join Interview"
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
