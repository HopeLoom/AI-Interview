import React, { useState, useEffect, useMemo } from 'react';
import { useLocation } from 'wouter';
import { useCompanyData } from '@/contexts/UserContext';
import {
  CompanyDashboardService,
  Interview,
  SessionSummary,
  SessionEvaluationSummary
} from '@/services/companyDashboardService';
import { SessionEvaluationPanel } from '@/components/company/SessionEvaluationPanel';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { ErrorDisplay } from '@/components/ui/error-display';
import { useErrorHandler } from '@/hooks/useErrorHandler';
import { 
  Building, 
  Users, 
  CheckCircle, 
  Award, 
  Home, 
  Search, 
  Plus,
  TrendingUp,
  Clock,
  Eye,
  Loader2
} from 'lucide-react';

interface Company {
  id: string;
  name: string;
  industry: string;
  size: string;
  location: string;
  founded_year?: number;
  description: string;
  logo_url?: string;
}

type SessionEvaluationDetail = SessionEvaluationSummary & {
  session?: SessionSummary;
};

export function CompanyDashboard() {
  const [currentView, setCurrentView] = useState<'interview-list' | 'interview-detail'>('interview-list');
  const [location, setLocation] = useLocation();
  const companyData = useCompanyData();                                   // this is the company data from the user context that is saved during login.
  const [company, setCompany] = useState<Company | null>(null);           
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [selectedInterview, setSelectedInterview] = useState<Interview | null>(null);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [evaluations, setEvaluations] = useState<SessionEvaluationSummary[]>([]);
  const [selectedEvaluation, setSelectedEvaluation] = useState<SessionEvaluationDetail | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState<'candidates' | 'analytics'>('candidates');
  const [isSessionsLoading, setIsSessionsLoading] = useState(false);
  const [isEvaluationLoading, setIsEvaluationLoading] = useState(false);
  const [isEvaluationPanelOpen, setIsEvaluationPanelOpen] = useState(false);
  const [evaluationError, setEvaluationError] = useState<string | null>(null);
  const { error, isLoading, executeAsync, clearError } = useErrorHandler();

  const handleViewCandidates = () => {
    setCurrentView('interview-detail');
  };

  const handleBackToDashboard = () => {
    setCurrentView('interview-list');
    setSelectedInterview(null);
  };

  const handleGoHome = () => {
    setCurrentView('interview-list');
    setSelectedInterview(null);
    setLocation('/company-dashboard');
  };

  // Load company data and interviews
  useEffect(() => {
    const loadDashboardData = async () => {
      if (!companyData) {
        return;
      }

      try {
        if (!company) {
          setCompany({
            id: companyData.companyId,
            name: companyData.companyName,
            industry: companyData.industry || 'Industry',
            size: companyData.size || 'Company Size',
            location: companyData.location || 'Location',
            description: 'Manage your interview processes and track candidate performance with HopeLoom.'
          });
        }

        const interviewsData = await CompanyDashboardService.getCompanyInterviews(companyData.companyId);

        setInterviews(interviewsData);
        console.log('✅ Loaded company interviews:', interviewsData);
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
        setInterviews([]);
      }
    };

    loadDashboardData();
  }, [companyData]);

  useEffect(() => {
    const loadInterviewDetails = async () => {
      if (!companyData || !selectedInterview) {
        setSessions([]);
        setEvaluations([]);
        return;
      }

      setIsSessionsLoading(true);
      setEvaluationError(null);

      try {
        const [sessionData, evaluationData] = await Promise.all([
          CompanyDashboardService.getInterviewSessions(companyData.companyId, selectedInterview.id),
          CompanyDashboardService.getInterviewEvaluations(companyData.companyId, selectedInterview.id)
        ]);

        setSessions(sessionData);
        setEvaluations(evaluationData);
      } catch (error) {
        console.error('Failed to load interview sessions/evaluations:', error);
        setSessions([]);
        setEvaluations([]);
        setEvaluationError('Unable to load interview sessions. Please try again.');
      } finally {
        setIsSessionsLoading(false);
      }
    };

    loadInterviewDetails();
  }, [companyData, selectedInterview]);

  // Check URL to set initial view
  useEffect(() => {
    if (location === '/company-dashboard/candidates') {
      setCurrentView('interview-detail');
      setActiveTab('candidates');
      // In a real app, this would load the actual interview data from the service
      // For now, we'll use the first available interview or create a placeholder
      if (interviews.length > 0) {
        setSelectedInterview(interviews[0]);
      }
    } else if (location === '/company-dashboard/analytics') {
      setCurrentView('interview-detail');
      setActiveTab('analytics');
      // In a real app, this would load the actual interview data from the service
      // For now, we'll use the first available interview or create a placeholder
      if (interviews.length > 0) {
        setSelectedInterview(interviews[0]);
      }
    } else if (location === '/company-dashboard') {
      // Reset to interview list view when going to dashboard home
      setCurrentView('interview-list');
      setSelectedInterview(null);
    }
  }, [location]);

  const totalInterviews = interviews.length;
  const totalCandidates = interviews.reduce((sum, interview) => sum + (interview.total_candidates || 0), 0);
  const completedCandidates = interviews.reduce((sum, interview) => sum + (interview.completed_candidates || 0), 0);
  const overallAverageScore = interviews.length > 0
    ? interviews.reduce((sum, interview) => sum + (interview.average_score || 0), 0) / interviews.length
    : 0;

  const filteredInterviews = interviews.filter(interview =>
    interview.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    interview.job_title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    interview.department.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const sortedEvaluations = useMemo(() => {
    return [...evaluations].sort((a, b) => (b.overall_score || 0) - (a.overall_score || 0));
  }, [evaluations]);

  const evaluationMap = useMemo(() => {
    const map = new Map<string, SessionEvaluationSummary>();
    evaluations.forEach((evaluation) => {
      if (evaluation.session_id) {
        map.set(evaluation.session_id, evaluation);
      }
    });
    return map;
  }, [evaluations]);

  const handleViewEvaluation = async (session: SessionSummary) => {
    if (!session.session_id) {
      return;
    }

    setEvaluationError(null);

    const existingEvaluation = evaluationMap.get(session.session_id);
    if (existingEvaluation && existingEvaluation.evaluation) {
      setSelectedEvaluation({ ...existingEvaluation, session });
      setIsEvaluationPanelOpen(true);
      return;
    }

    setIsEvaluationLoading(true);

    try {
      const response = await CompanyDashboardService.getSessionEvaluation(session.session_id);
      const evaluationDetail = response.evaluation || existingEvaluation?.evaluation || null;
      const sessionInfo = response.session || {};

      const mergedEvaluation: SessionEvaluationDetail = {
        session_id: session.session_id,
        candidate_id: session.candidate_id,
        candidate_name: session.candidate_name,
        candidate_email: session.candidate_email,
        status: existingEvaluation?.status || session.status,
        overall_score: evaluationDetail?.overall_score ?? existingEvaluation?.overall_score ?? session.overall_score,
        evaluation: evaluationDetail,
        completed_at: sessionInfo.completed_at || session.completed_at,
        session: {
          ...session,
          completed_at: sessionInfo.completed_at || session.completed_at,
          started_at: sessionInfo.started_at || session.started_at,
          status: sessionInfo.status || session.status,
        }
      };

      setSelectedEvaluation(mergedEvaluation);
      setIsEvaluationPanelOpen(true);

      setEvaluations((prev) => {
        const clone = [...prev];
        const idx = clone.findIndex((item) => item.session_id === session.session_id);
        if (idx >= 0) {
          clone[idx] = { ...clone[idx], ...mergedEvaluation };
        } else {
          clone.push(mergedEvaluation);
        }
        return clone;
      });
    } catch (error) {
      console.error('Failed to load session evaluation:', error);
      setEvaluationError('Unable to load evaluation for this session. Please try again.');
    } finally {
      setIsEvaluationLoading(false);
    }
  };

  const handleCloseEvaluation = () => {
    setIsEvaluationPanelOpen(false);
    setSelectedEvaluation(null);
  };

  if (currentView === 'interview-detail' && selectedInterview) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-700">
        <div className="container mx-auto px-4 py-6">
          {/* Navigation Header */}
          <div className="flex justify-center mb-8">
            <Button
              onClick={handleGoHome}
              variant="outline"
              className="!border-slate-600 !text-slate-200 hover:!bg-slate-700 hover:!text-white bg-transparent"
            >
              <Home className="w-4 h-4 mr-2" />
              Home
            </Button>
          </div>

          {/* Interview Header */}
          <div className="text-center space-y-4 mb-8">
            <h1 className="text-3xl font-bold text-white">{selectedInterview.name}</h1>
            <p className="text-slate-300">{selectedInterview.job_title} • {selectedInterview.department}</p>
            <div className="flex items-center justify-center gap-6 text-sm text-slate-400">
              <span>{selectedInterview.total_candidates} Total Candidates</span>
              <span>{selectedInterview.completed_candidates} Completed</span>
              <span>Avg Score: {selectedInterview.average_score.toFixed(1)}</span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex space-x-1 bg-slate-800 p-1 rounded-lg mb-8">
            {[
              { id: 'candidates', label: 'Candidates', icon: Users },
              { id: 'analytics', label: 'Analytics', icon: TrendingUp }
            ].map((tab) => {
              const IconComponent = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => {
                    setActiveTab(tab.id as any);
                    setLocation(`/company-dashboard/${tab.id}`);
                  }}
                  className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-md transition-all ${
                    activeTab === tab.id
                      ? 'bg-blue-600 text-white shadow-lg'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700'
                  }`}
                >
                  <IconComponent className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Tab Content */}
          {activeTab === 'candidates' && (
            <div className="space-y-6">
              {isSessionsLoading ? (
                <div className="flex items-center justify-center py-12 text-slate-300">
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Loading interview sessions...
                </div>
              ) : (
                <>
                  {evaluationError && (
                    <Card className="bg-red-500/10 border-red-500/30">
                      <CardContent className="py-4 text-sm text-red-200">
                        {evaluationError}
                      </CardContent>
                    </Card>
                  )}

                  <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                    {sessions.map((session) => {
                      const evaluation = session.session_id ? evaluationMap.get(session.session_id) : undefined;
                      const statusLabel = (session.status || 'unknown').replace(/_/g, ' ');
                      const normalizedScore = evaluation?.overall_score ?? session.overall_score;

                      return (
                        <Card
                          key={session.session_id || `${session.candidate_id}-${session.started_at}`}
                          className="bg-gradient-to-br from-slate-900/90 to-slate-800/90 border-slate-700"
                        >
                          <CardHeader>
                            <div className="flex items-start justify-between">
                              <div>
                                <CardTitle className="text-lg text-white flex items-center gap-3">
                                  <span>{session.candidate_name || 'Candidate'}</span>
                                  <Badge className="bg-slate-600/40 border-slate-500/60 text-xs capitalize">
                                    {statusLabel}
                                  </Badge>
                                </CardTitle>
                                <p className="text-slate-400 text-sm">{session.candidate_email || 'No email on file'}</p>
                              </div>
                              <div className="text-right">
                                <div className="text-xs text-slate-400">Score</div>
                                <div className="text-2xl font-semibold text-blue-400">
                                  {normalizedScore !== undefined && normalizedScore !== null ? normalizedScore.toFixed(1) : '—'}
                                </div>
                              </div>
                            </div>
                          </CardHeader>
                          <CardContent>
                            <div className="flex flex-wrap items-center justify-between gap-4 text-sm text-slate-300">
                              <div>
                                <span className="text-slate-400">Session ID:</span>{' '}
                                <span className="font-mono text-slate-200">{session.session_id || 'N/A'}</span>
                              </div>
                              <div>
                                <span className="text-slate-400">Completed:</span>{' '}
                                <span>{session.completed_at ? new Date(session.completed_at).toLocaleString() : 'Pending'}</span>
                              </div>
                              <div>
                                <span className="text-slate-400">Status:</span>{' '}
                                <span className="capitalize">{statusLabel}</span>
                              </div>
                            </div>
                            <div className="mt-4 flex items-center justify-between">
                              <div className="flex items-center gap-2 text-xs text-slate-400">
                                <Users className="w-4 h-4" />
                                Session overview
                              </div>
                              <div className="flex gap-2">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="!border-slate-600 !text-slate-200 hover:!bg-slate-700 hover:!text-white bg-transparent"
                                  onClick={() => handleViewEvaluation(session)}
                                >
                                  <Eye className="w-4 h-4 mr-2" />
                                  {evaluation && evaluation.evaluation ? 'View Evaluation' : 'Preview Session'}
                                </Button>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      );
                    })}
                  </div>

                  {sessions.length === 0 && (
                    <Card className="bg-gradient-to-br from-slate-900/90 to-slate-800/90 border-slate-700">
                      <CardContent className="py-10 text-center text-slate-300">
                        No interview sessions have been scheduled for this configuration yet.
                      </CardContent>
                    </Card>
                  )}
                </>
              )}

              <SessionEvaluationPanel
                isOpen={isEvaluationPanelOpen}
                isLoading={isEvaluationLoading}
                evaluation={selectedEvaluation}
                onClose={handleCloseEvaluation}
              />
            </div>
          )}

          {activeTab === 'analytics' && (
            <div className="space-y-8">
              {/* Key Performance Metrics */}
              <Card className="bg-gradient-to-br from-slate-800/90 to-slate-700/90 border-slate-600">
                <CardHeader>
                  <CardTitle className="text-xl text-white text-center">Performance Overview</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    <div className="text-center">
                      <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                        <CheckCircle className="w-8 h-8 text-green-400" />
                      </div>
                      <div className="text-3xl font-bold text-white mb-1">
                        {selectedInterview.total_candidates > 0
                          ? ((selectedInterview.completed_candidates / selectedInterview.total_candidates) * 100).toFixed(0)
                          : '0'
                        }%
                      </div>
                      <div className="text-sm text-slate-300">Completion Rate</div>
                    </div>
                    
                    <div className="text-center">
                      <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                        <Award className="w-8 h-8 text-blue-400" />
                      </div>
                      <div className="text-3xl font-bold text-white mb-1">
                        {selectedInterview.average_score.toFixed(1)}
                      </div>
                      <div className="text-sm text-slate-300">Average Score</div>
                    </div>
                    
                    <div className="text-center">
                      <div className="w-16 h-16 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                        <Clock className="w-8 h-8 text-purple-400" />
                      </div>
                      <div className="text-3xl font-bold text-white mb-1">
                        {(() => {
                          const durations = sessions
                            .map((session) => session.interview_duration || session.duration_minutes)
                            .filter((duration): duration is number => typeof duration === 'number' && duration > 0);
                          if (!durations.length) {
                            return '0';
                          }
                          const avgDuration = durations.reduce((sum, value) => sum + value, 0) / durations.length;
                          return avgDuration.toFixed(0);
                        })()}m
                      </div>
                      <div className="text-sm text-slate-300">Avg Duration</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Score Distribution */}
              <Card className="bg-gradient-to-br from-slate-800/90 to-slate-700/90 border-slate-600">
                <CardHeader>
                  <CardTitle className="text-xl text-white text-center">Score Distribution</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex justify-center">
                    <div className="grid grid-cols-5 gap-6">
                      {[1, 2, 3, 4, 5].map((score) => {
                        const count = evaluations.filter(e => Math.round(e.overall_score || 0) === score).length;
                        const percentage = evaluations.length > 0 ? (count / evaluations.length) * 100 : 0;
                        return (
                          <div key={score} className="text-center">
                            <div className="w-12 h-12 bg-slate-700 rounded-full flex items-center justify-center mx-auto mb-2">
                              <span className="text-xl font-bold text-white">{score}</span>
                            </div>
                            <div className="text-lg font-bold text-blue-400 mb-1">{count}</div>
                            <div className="text-xs text-slate-300">{percentage.toFixed(0)}%</div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto px-4 py-6">
        {/* No navigation header needed on homepage */}
        
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-slate-300">Loading dashboard...</p>
            </div>
          </div>
        ) : error ? (
          <ErrorDisplay error={error} onDismiss={clearError} />
        ) : (
          <div className="space-y-8">
            {/* Company Header */}
            <div className="text-center space-y-4">
              <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl mb-6 shadow-2xl">
                <Building className="h-10 w-10 text-white" />
              </div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-white to-blue-200 bg-clip-text text-transparent">
                {company?.name || 'Your Company'}
              </h1>
              <div className="flex items-center justify-center gap-4 text-slate-300 text-sm">
                <span>{company?.industry}</span>
                <span>•</span>
                <span>{company?.size}</span>
                <span>•</span>
                <span>{company?.location}</span>
              </div>
              <p className="text-slate-300 text-lg max-w-2xl mx-auto">
                Manage your interview processes and track candidate performance across all positions.
              </p>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <Card className="bg-gradient-to-br from-slate-800/90 to-slate-700/90 border-slate-600 hover:border-blue-500 transition-colors">
                <CardContent className="pt-6 text-center">
                  <div className="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center mx-auto mb-3">
                    <Building className="w-6 h-6 text-blue-400" />
                  </div>
                  <div className="text-3xl font-bold text-white mb-1">{totalInterviews}</div>
                  <div className="text-sm text-slate-300">Active Interviews</div>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-br from-slate-800/90 to-slate-700/90 border-slate-600 hover:border-green-500 transition-colors">
                <CardContent className="pt-6 text-center">
                  <div className="w-12 h-12 bg-green-500/20 rounded-lg flex items-center justify-center mx-auto mb-3">
                    <Users className="w-6 h-6 text-green-400" />
                  </div>
                  <div className="text-3xl font-bold text-white mb-1">{totalCandidates}</div>
                  <div className="text-sm text-slate-300">Total Candidates</div>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-br from-slate-800/90 to-slate-700/90 border-slate-600 hover:border-orange-500 transition-colors">
                <CardContent className="pt-6 text-center">
                  <div className="w-12 h-12 bg-orange-500/20 rounded-lg flex items-center justify-center mx-auto mb-3">
                    <CheckCircle className="w-6 h-6 text-orange-400" />
                  </div>
                  <div className="text-3xl font-bold text-white mb-1">{completedCandidates}</div>
                  <div className="text-sm text-slate-300">Completed</div>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-br from-slate-800/90 to-slate-700/90 border-slate-600 hover:border-purple-500 transition-colors">
                <CardContent className="pt-6 text-center">
                  <div className="w-12 h-12 bg-purple-500/20 rounded-lg flex items-center justify-center mx-auto mb-3">
                    <Award className="w-6 h-6 text-purple-400" />
                  </div>
                  <div className="text-3xl font-bold text-white mb-1">{overallAverageScore.toFixed(1)}</div>
                  <div className="text-sm text-slate-300">Avg Score</div>
                </CardContent>
              </Card>
            </div>

            {/* Interview List */}
            <div className="space-y-6">
              {/* Search and Actions */}
              <div className="flex gap-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                  <Input
                    placeholder="Search interviews..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 bg-slate-800 border-slate-600 text-white placeholder:text-slate-400"
                  />
                </div>
                <Button 
                  onClick={() => setLocation('/configure')}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Create New Interview
                </Button>
              </div>

              {/* Interview Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredInterviews.map((interview) => (
                  <Card 
                    key={interview.id} 
                    className="bg-gradient-to-br from-slate-800/90 to-slate-700/90 border-slate-600 hover:border-blue-500 transition-colors cursor-pointer group"
                    onClick={() => {
                      setSelectedInterview(interview);
                      setCurrentView('interview-detail');
                    }}
                  >
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div>
                          <CardTitle className="text-lg text-white mb-2 group-hover:text-blue-300 transition-colors">
                            {interview.name}
                          </CardTitle>
                          <p className="text-slate-300 text-sm">{interview.job_title}</p>
                        </div>
                        <Badge className={`${
                          interview.status === 'active' ? 'bg-green-500/20 text-green-300 border-green-500/30' :
                          interview.status === 'completed' ? 'bg-blue-500/20 text-blue-300 border-blue-500/30' :
                          'bg-slate-500/20 text-slate-300 border-slate-500/30'
                        }`}>
                          {interview.status.toUpperCase()}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-300">Candidates:</span>
                          <span className="text-white">
                            {interview.completed_candidates || 0}/{interview.total_candidates || 0}
                          </span>
                        </div>
                        <Progress 
                          value={
                            interview.total_candidates
                              ? (interview.completed_candidates / interview.total_candidates) * 100
                              : 0
                          } 
                          className="w-full"
                        />
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-300">Avg Score:</span>
                          <span className="text-white">
                            {(interview.average_score ?? 0).toFixed(1)}
                          </span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-300">Created:</span>
                          <span className="text-white">{new Date(interview.created_date).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Empty State */}
              {filteredInterviews.length === 0 && (
                <Card className="bg-gradient-to-br from-slate-800/90 to-slate-700/90 border-slate-600">
                  <CardContent className="pt-12 pb-12 text-center">
                    <div className="w-16 h-16 bg-slate-700 rounded-full flex items-center justify-center mx-auto mb-4">
                      <Building className="w-8 h-8 text-slate-400" />
                    </div>
                    <h3 className="text-xl font-semibold text-white mb-2">No interviews found</h3>
                    <p className="text-slate-300 mb-4">
                      {searchTerm ? `No interviews match "${searchTerm}"` : "You haven't created any interviews yet."}
                    </p>
                    <Button 
                      onClick={() => setLocation('/configure')}
                      className="bg-blue-600 hover:bg-blue-700 text-white"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Create Your First Interview
                    </Button>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
