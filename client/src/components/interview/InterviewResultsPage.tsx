import React, { useState, useEffect } from 'react';
import { useLocation, useRoute } from 'wouter';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { apiClient } from '@/services/apiClient';
import { useToast } from '@/hooks/use-toast';
import {
  CheckCircle,
  AlertCircle,
  Award,
  Star,
  TrendingUp,
  Target,
  MessageSquare,
  ArrowLeft,
  Sparkles
} from 'lucide-react';

export default function InterviewResultsPage() {
  const [, setLocation] = useLocation();
  const [match, params] = useRoute('/results/:sessionId');
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(true);
  const [evaluationData, setEvaluationData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (match && params?.sessionId) {
      const fetchEvaluation = async () => {
        try {
          setIsLoading(true);
          setError(null);
          const response = await apiClient.get(`/api/configurations/sessions/${params.sessionId}/evaluation`);

          if (response.data.success) {
            setEvaluationData(response.data);
          } else {
            throw new Error('Failed to fetch evaluation');
          }
        } catch (error: any) {
          console.error('Error fetching evaluation:', error);
          const errorMsg = error.response?.data?.detail || 'Failed to load interview results';
          setError(errorMsg);
          toast({
            title: 'Error',
            description: errorMsg,
            variant: 'destructive'
          });
        } finally {
          setIsLoading(false);
        }
      };

      fetchEvaluation();
    }
  }, [match, params, toast]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-6">
        <Card className="w-full max-w-2xl bg-slate-800 border-slate-700">
          <CardContent className="pt-8 pb-8">
            <div className="text-center space-y-6">
              <div className="relative">
                <div className="w-24 h-24 mx-auto bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center animate-pulse">
                  <Sparkles className="w-12 h-12 text-white animate-bounce" />
                </div>
                <div className="absolute inset-0 w-24 h-24 mx-auto border-4 border-blue-500/30 rounded-full animate-ping"></div>
              </div>
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">Loading Interview Results</h2>
                <p className="text-slate-300">Please wait while we retrieve your evaluation...</p>
              </div>
              <Progress value={75} className="w-full" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !evaluationData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-6">
        <Card className="w-full max-w-md bg-slate-800 border-slate-700">
          <CardContent className="pt-6">
            <div className="text-center">
              <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">Results Not Available</h3>
              <p className="text-slate-300 mb-4">{error || 'Unable to load interview results.'}</p>
              <Button
                onClick={() => setLocation('/candidate-dashboard')}
                className="bg-blue-600 hover:bg-blue-700"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Dashboard
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { session, evaluation } = evaluationData;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Header */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <div className="flex items-center justify-between">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setLocation('/candidate-dashboard')}
                className="text-slate-300 hover:text-white"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Dashboard
              </Button>
              <Badge variant={session?.status === 'completed' ? 'default' : 'secondary'}>
                {session?.status || 'Unknown'}
              </Badge>
            </div>
            <CardTitle className="text-3xl text-white mt-4">Interview Results</CardTitle>
            {session?.candidate_name && (
              <p className="text-slate-300">
                Candidate: {session.candidate_name} ({session.candidate_email})
              </p>
            )}
          </CardHeader>
        </Card>

        {/* Overall Score */}
        {evaluation && evaluation.overall_score != null && (
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Award className="w-6 h-6 text-yellow-500" />
                Overall Score
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center">
                <div className="text-6xl font-bold text-white mb-2">
                  {evaluation.overall_score}
                  <span className="text-3xl text-slate-400">/100</span>
                </div>
                <Progress value={evaluation.overall_score} className="w-full mt-4" />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Strengths */}
        {evaluation?.strengths && evaluation.strengths.length > 0 && (
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Star className="w-6 h-6 text-green-500" />
                Strengths
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {evaluation.strengths.map((strength: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-2 text-slate-300">
                    <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>{strength}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {/* Areas for Improvement */}
        {evaluation?.areas_for_improvement && evaluation.areas_for_improvement.length > 0 && (
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <TrendingUp className="w-6 h-6 text-blue-500" />
                Areas for Improvement
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {evaluation.areas_for_improvement.map((area: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-2 text-slate-300">
                    <Target className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" />
                    <span>{area}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {/* Feedback */}
        {evaluation?.feedback && (
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <MessageSquare className="w-6 h-6 text-purple-500" />
                Detailed Feedback
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-300 whitespace-pre-wrap">{evaluation.feedback}</p>
            </CardContent>
          </Card>
        )}

        {/* Session Info */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">Session Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-slate-300">
            <div className="flex justify-between">
              <span>Session ID:</span>
              <span className="font-mono text-sm">{session?.session_id}</span>
            </div>
            {session?.started_at && (
              <div className="flex justify-between">
                <span>Started:</span>
                <span>{new Date(session.started_at).toLocaleString()}</span>
              </div>
            )}
            {session?.completed_at && (
              <div className="flex justify-between">
                <span>Completed:</span>
                <span>{new Date(session.completed_at).toLocaleString()}</span>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
