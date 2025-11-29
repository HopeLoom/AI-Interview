import React from 'react';
import { SessionEvaluationSummary, SessionSummary } from '@/services/companyDashboardService';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Loader2, Award, CheckCircle, ListChecks, AlertCircle } from 'lucide-react';

export type SessionEvaluationPanelData = SessionEvaluationSummary & {
  session?: SessionSummary;
};

interface SessionEvaluationPanelProps {
  isOpen: boolean;
  isLoading?: boolean;
  evaluation: SessionEvaluationPanelData | null;
  onClose: () => void;
}

const getArray = (value: any): string[] => {
  if (!value) return [];
  if (Array.isArray(value)) {
    return value.map((item) => (typeof item === 'string' ? item : JSON.stringify(item)));
  }
  if (typeof value === 'string') {
    return [value];
  }
  return [];
};

export const SessionEvaluationPanel: React.FC<SessionEvaluationPanelProps> = ({
  isOpen,
  isLoading = false,
  evaluation,
  onClose,
}) => {
  const handleOpenChange = (open: boolean) => {
    if (!open) {
      onClose();
    }
  };

  const evaluationPayload = evaluation?.evaluation || {};
  const strengths = getArray(evaluationPayload.strengths || evaluationPayload.key_strengths);
  const improvements = getArray(
    evaluationPayload.areas_for_improvement || evaluationPayload.areas_for_development
  );
  const feedback = evaluationPayload.feedback || evaluationPayload.overall_feedback;
  const criteriaScores = Array.isArray(evaluationPayload.criteria_specific_scoring)
    ? evaluationPayload.criteria_specific_scoring
    : Array.isArray(evaluationPayload.criteria_scores)
      ? evaluationPayload.criteria_scores
      : [];

  return (
    <Sheet open={isOpen} onOpenChange={handleOpenChange}>
      <SheetContent className="w-full sm:max-w-3xl bg-slate-950 text-white border-slate-800">
        <SheetHeader className="space-y-2">
          <SheetTitle className="text-2xl font-semibold text-white">
            Candidate Evaluation
          </SheetTitle>
          <SheetDescription className="text-slate-300">
            {evaluation?.candidate_name
              ? `Detailed evaluation for ${evaluation.candidate_name}`
              : 'Detailed session evaluation'}
          </SheetDescription>
        </SheetHeader>

        <div className="mt-4 flex flex-col gap-4">
          {evaluation && (
            <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-slate-800 bg-slate-900/60 p-4">
              <div>
                <div className="text-sm text-slate-400">Candidate</div>
                <div className="text-lg font-semibold text-white">
                  {evaluation.candidate_name || 'Unknown Candidate'}
                </div>
                <div className="text-sm text-slate-400">
                  {evaluation.candidate_email || 'No email provided'}
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-slate-400">Overall Score</div>
                <div className="text-3xl font-bold text-blue-400">
                  {evaluation.overall_score !== undefined && evaluation.overall_score !== null
                    ? evaluation.overall_score.toFixed(1)
                    : '—'}
                </div>
                {evaluation.status && (
                  <Badge className="mt-2 bg-slate-700/60 border-slate-500/60 capitalize">
                    {evaluation.status.replace(/_/g, ' ')}
                  </Badge>
                )}
              </div>
            </div>
          )}

          {evaluation?.session && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-300">
              <div>
                <div className="text-slate-400">Session ID</div>
                <div className="font-mono text-white text-sm">
                  {evaluation.session.session_id || 'N/A'}
                </div>
              </div>
              <div>
                <div className="text-slate-400">Completed At</div>
                <div>
                  {evaluation.session.completed_at
                    ? new Date(evaluation.session.completed_at).toLocaleString()
                    : 'Pending'}
                </div>
              </div>
              <div>
                <div className="text-slate-400">Status</div>
                <div className="capitalize">{evaluation.session.status || 'Unknown'}</div>
              </div>
              <div>
                <div className="text-slate-400">Started At</div>
                <div>
                  {evaluation.session.started_at
                    ? new Date(evaluation.session.started_at).toLocaleString()
                    : 'Unknown'}
                </div>
              </div>
            </div>
          )}

          <Separator className="bg-slate-800" />

          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-12 text-slate-300">
              <Loader2 className="w-6 h-6 animate-spin mb-2" />
              Loading evaluation details...
            </div>
          ) : evaluation ? (
            <ScrollArea className="h-[calc(100vh-280px)] pr-4">
              <div className="space-y-6">
                <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                  <div className="flex items-center gap-3 mb-3 text-lg font-semibold text-white">
                    <Award className="w-5 h-5 text-blue-300" />
                    Overall Feedback
                  </div>
                  <div className="text-sm leading-relaxed text-slate-300 whitespace-pre-line">
                    {feedback || 'No qualitative feedback has been recorded for this session yet.'}
                  </div>
                </section>

                {strengths.length > 0 && (
                  <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                    <div className="flex items-center gap-3 mb-3 text-lg font-semibold text-white">
                      <CheckCircle className="w-5 h-5 text-green-300" />
                      Key Strengths
                    </div>
                    <ul className="list-disc pl-6 space-y-2 text-sm text-slate-300">
                      {strengths.map((item, index) => (
                        <li key={`strength-${index}`}>{item}</li>
                      ))}
                    </ul>
                  </section>
                )}

                {improvements.length > 0 && (
                  <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                    <div className="flex items-center gap-3 mb-3 text-lg font-semibold text-white">
                      <AlertCircle className="w-5 h-5 text-orange-300" />
                      Areas for Improvement
                    </div>
                    <ul className="list-disc pl-6 space-y-2 text-sm text-slate-300">
                      {improvements.map((item, index) => (
                        <li key={`improvement-${index}`}>{item}</li>
                      ))}
                    </ul>
                  </section>
                )}

                {criteriaScores.length > 0 && (
                  <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                    <div className="flex items-center gap-3 mb-3 text-lg font-semibold text-white">
                      <ListChecks className="w-5 h-5 text-purple-300" />
                      Criteria Breakdown
                    </div>
                    <div className="space-y-4">
                      {criteriaScores.map((criterion: any, index: number) => (
                        <div
                          key={`criterion-${index}`}
                          className="rounded-lg border border-slate-800 bg-slate-950/60 p-3"
                        >
                          <div className="flex items-center justify-between text-sm">
                            <div className="text-white font-medium">
                              {criterion.criteria || criterion.name || `Criterion ${index + 1}`}
                            </div>
                            {criterion.score !== undefined && (
                              <Badge className="bg-blue-600/30 border-blue-500/50">
                                Score: {criterion.score}
                              </Badge>
                            )}
                          </div>
                          {criterion.reason && (
                            <p className="mt-2 text-sm text-slate-300">{criterion.reason}</p>
                          )}
                          {criterion.reason_bullets && Array.isArray(criterion.reason_bullets) && (
                            <ul className="mt-2 list-disc pl-6 text-sm text-slate-300 space-y-1">
                              {criterion.reason_bullets.map((item: string, bulletIdx: number) => (
                                <li key={`criterion-${index}-bullet-${bulletIdx}`}>{item}</li>
                              ))}
                            </ul>
                          )}
                          {criterion.key_phrases_from_conversation &&
                            Array.isArray(criterion.key_phrases_from_conversation) && (
                              <div className="mt-2 text-xs text-slate-400">
                                Key phrases: {criterion.key_phrases_from_conversation.join(', ')}
                              </div>
                            )}
                        </div>
                      ))}
                    </div>
                  </section>
                )}
              </div>
            </ScrollArea>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-slate-400">
              <AlertCircle className="w-8 h-8 mb-3 text-slate-500" />
              <p>No evaluation data available for this session yet.</p>
            </div>
          )}

          <Button onClick={onClose} className="mt-auto bg-blue-600 hover:bg-blue-700 text-white">
            Close
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
};

SessionEvaluationPanel.displayName = 'SessionEvaluationPanel';
