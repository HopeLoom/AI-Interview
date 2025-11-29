import React, { useState, useEffect } from 'react';
import { useLocation } from 'wouter';
import { useConfiguration } from '@/contexts/ConfigurationContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Users,
  UserPlus,
  CheckCircle,
  Clock,
  AlertCircle,
  Eye,
  Mail,
  Building,
  Target,
  ArrowRight,
  Plus,
  Search,
  Filter,
} from 'lucide-react';
import { CandidateService } from '@/services/candidateService';

interface Candidate {
  id: string;
  name: string;
  email: string;
  resume_filename: string;
  status: 'pending' | 'in_progress' | 'completed' | 'evaluated';
  progress?: number;
  score?: number;
  last_updated?: string;
  interview_duration?: number;
}

interface InterviewConfiguration {
  id: string;
  name: string;
  job_title: string;
  company_name: string;
  total_candidates: number;
  created_date: string;
  status: 'active' | 'completed' | 'draft';
}

export function CandidateListPage() {
  const { state } = useConfiguration();
  const [, setLocation] = useLocation();
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadCandidates = async () => {
      try {
        const candidatesData = await CandidateService.getCandidates();
        setCandidates(candidatesData);
      } catch (error) {
        console.error('Failed to load candidates:', error);
        // The service will return mock data as fallback
      } finally {
        setIsLoading(false);
      }
    };

    loadCandidates();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500/20 text-green-300 border-green-500/30';
      case 'in_progress':
        return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
      case 'pending':
        return 'bg-slate-500/20 text-slate-300 border-slate-500/30';
      case 'evaluated':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/30';
      default:
        return 'bg-slate-500/20 text-slate-300 border-slate-500/30';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4" />;
      case 'in_progress':
        return <Clock className="w-4 h-4" />;
      case 'pending':
        return <AlertCircle className="w-4 h-4" />;
      case 'evaluated':
        return <CheckCircle className="w-4 h-4" />;
      default:
        return <AlertCircle className="w-4 h-4" />;
    }
  };

  const filteredCandidates = candidates.filter((candidate) => {
    const matchesSearch =
      candidate.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      candidate.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || candidate.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleViewDashboard = () => {
    // Navigate to company dashboard
    setLocation('/company-dashboard');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <Card className="w-full max-w-md bg-slate-800 border-slate-700">
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-slate-300">Loading candidates...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto space-y-8">
          {/* Header */}
          <div className="text-center space-y-4">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl mb-6 shadow-2xl">
              <Users className="h-10 w-10 text-white" />
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-white to-blue-200 bg-clip-text text-transparent">
              Candidate Management
            </h1>
            <p className="text-slate-300 text-lg max-w-2xl mx-auto">
              Review your candidate list and manage the interview process. All candidates are ready
              to begin their AI-powered interviews.
            </p>
          </div>

          {/* Interview Summary Card */}
          <Card className="bg-gradient-to-br from-slate-900/90 to-slate-800/90 border-slate-700">
            <CardHeader>
              <CardTitle className="flex items-center gap-3 text-xl text-white">
                <Building className="w-6 h-6 text-blue-400" />
                Interview Configuration Summary
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-300 mb-2">{candidates.length}</div>
                  <div className="text-sm text-slate-400">Total Candidates</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-300 mb-2">
                    {candidates.filter((c) => c.status === 'pending').length}
                  </div>
                  <div className="text-sm text-slate-400">Ready to Start</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-orange-300 mb-2">
                    {candidates.filter((c) => c.status === 'completed').length}
                  </div>
                  <div className="text-sm text-slate-400">Completed</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Search and Filters */}
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
              <Input
                placeholder="Search candidates by name or email..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 bg-slate-800 border-slate-600 text-white placeholder:text-slate-400"
              />
            </div>
            <div className="flex gap-2">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white focus:border-blue-500 focus:ring-blue-500/20"
              >
                <option value="all">All Status</option>
                <option value="pending">Pending</option>
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
                <option value="evaluated">Evaluated</option>
              </select>
              <Button
                variant="outline"
                className="!border-slate-600 !text-slate-200 hover:!bg-slate-700 hover:!text-white bg-transparent"
              >
                <Filter className="w-4 h-4 mr-2" />
                Filters
              </Button>
            </div>
          </div>

          {/* Candidate List */}
          <Card className="bg-gradient-to-br from-slate-900/90 to-slate-800/90 border-slate-700">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-xl text-white">Candidate List</CardTitle>
                <Button
                  variant="outline"
                  className="!border-slate-600 !text-slate-200 hover:!bg-slate-700 hover:!text-white bg-transparent"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Add Candidate
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {filteredCandidates.map((candidate) => (
                  <div
                    key={candidate.id}
                    className="border border-slate-600 rounded-lg p-4 hover:border-slate-500 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                          <span className="text-white font-semibold text-lg">
                            {candidate.name
                              .split(' ')
                              .map((n) => n[0])
                              .join('')}
                          </span>
                        </div>

                        <div>
                          <h3 className="font-semibold text-white text-lg">{candidate.name}</h3>
                          <p className="text-slate-400 text-sm">{candidate.email}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge
                              variant="outline"
                              className="text-xs text-slate-400 border-slate-500"
                            >
                              {candidate.resume_filename}
                            </Badge>
                            <Badge className={`text-xs ${getStatusColor(candidate.status)}`}>
                              <span className="flex items-center gap-1">
                                {getStatusIcon(candidate.status)}
                                {candidate.status.replace('_', ' ').toUpperCase()}
                              </span>
                            </Badge>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-4">
                        {/* Progress/Score Display */}
                        <div className="text-right">
                          {candidate.status === 'completed' || candidate.status === 'evaluated' ? (
                            <div className="text-center">
                              <div className="text-2xl font-bold text-green-400">
                                {candidate.score?.toFixed(1) || 'N/A'}
                              </div>
                              <div className="text-xs text-slate-400">Score</div>
                            </div>
                          ) : candidate.status === 'in_progress' ? (
                            <div className="text-center">
                              <div className="text-2xl font-bold text-blue-400">
                                {candidate.progress}%
                              </div>
                              <div className="text-xs text-slate-300">Progress</div>
                            </div>
                          ) : (
                            <div className="text-center">
                              <div className="text-2xl font-bold text-slate-300">-</div>
                              <div className="text-xs text-slate-300">Not Started</div>
                            </div>
                          )}
                        </div>

                        {/* Action Buttons */}
                        <div className="flex gap-2">
                          {candidate.status === 'evaluated' && (
                            <Button
                              size="sm"
                              variant="outline"
                              className="!border-purple-500 !text-purple-400 hover:!bg-purple-500/20 hover:!text-white bg-transparent"
                              onClick={() => setLocation(`/evaluation/${candidate.id}`)}
                            >
                              <Eye className="w-4 h-4 mr-1" />
                              View Report
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Additional Info */}
                    {candidate.last_updated && (
                      <div className="mt-3 pt-3 border-t border-slate-600">
                        <div className="flex items-center justify-between text-sm text-slate-400">
                          <span>
                            Last updated: {new Date(candidate.last_updated).toLocaleString()}
                          </span>
                          {candidate.interview_duration && (
                            <span>Duration: {candidate.interview_duration} minutes</span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="flex justify-center">
            <Button
              onClick={handleViewDashboard}
              variant="outline"
              className="!border-slate-600 !text-slate-200 hover:!bg-slate-700 hover:!text-white bg-transparent px-8"
              size="lg"
            >
              <Eye className="w-5 h-5 mr-2" />
              View Dashboard
            </Button>
          </div>

          {/* Info Box */}
          <Card className="bg-gradient-to-br from-slate-800/90 to-slate-700/90 border-slate-600">
            <CardContent className="pt-6">
              <div className="text-center space-y-3">
                <div className="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center mx-auto">
                  <Target className="w-6 h-6 text-blue-400" />
                </div>
                <h3 className="text-lg font-semibold text-white">Next Steps</h3>
                <p className="text-slate-300 text-sm max-w-2xl mx-auto">
                  Once interviews begin, you'll be able to monitor real-time progress, view
                  candidate performance, and access detailed evaluation reports. The dashboard will
                  show rankings, analytics, and insights to help you make informed hiring decisions.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
