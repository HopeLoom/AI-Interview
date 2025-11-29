import React, { useState, useEffect } from 'react';
import { useLocation, useParams } from 'wouter';
import { useUser, useCompanyId } from '@/contexts/UserContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import {
  ArrowLeft,
  User,
  Target,
  BarChart3,
  Code,
  MessageSquare,
  FileText,
  ChevronDown,
  ChevronUp,
  Star,
  Clock,
  Award,
  TrendingUp,
  CheckCircle,
  AlertCircle,
  Eye,
  Download,
  Home,
} from 'lucide-react';

import { CompanyEvaluationService, EvaluationReport } from '@/services/companyEvaluationService';

interface SectionCardProps {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  collapsible?: boolean;
  defaultOpen?: boolean;
}

const SectionCard: React.FC<SectionCardProps> = ({
  title,
  icon,
  children,
  collapsible = false,
  defaultOpen = true,
}) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  if (!collapsible) {
    return (
      <Card className="bg-gradient-to-br from-slate-800/90 to-slate-700/90 border-slate-600">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center text-lg text-white">
            <span className="mr-2">{icon}</span>
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0">{children}</CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-gradient-to-br from-slate-800/90 to-slate-700/90 border-slate-600">
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger asChild>
          <CardHeader className="pb-3 cursor-pointer hover:bg-slate-700/50 transition-colors">
            <CardTitle className="flex items-center justify-between text-lg text-white">
              <span className="flex items-center">
                <span className="mr-2">{icon}</span>
                {title}
              </span>
              {isOpen ? (
                <ChevronUp className="w-5 h-5 text-slate-400" />
              ) : (
                <ChevronDown className="w-5 h-5 text-slate-400" />
              )}
            </CardTitle>
          </CardHeader>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <CardContent className="pt-0">{children}</CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
};

const CandidateEvaluationReport: React.FC = () => {
  const [, setLocation] = useLocation();
  const { user } = useUser();
  const companyId = useCompanyId();
  const [showFullCode, setShowFullCode] = useState(false);
  const [data, setData] = useState<EvaluationReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadEvaluationData = async () => {
      const id = user?.email || '';
      setLoading(true);
      console.log('Loading evaluation for candidate ID:', id);

      try {
        // Try to get evaluation data from the company service
        // This will use the updated /evaluation/{company_id}/{user_id} endpoint
        // Get company ID from user context
        if (!companyId) {
          throw new Error('Company ID not found in user context');
        }

        const evaluationData = await CompanyEvaluationService.getCandidateEvaluation(
          companyId,
          user?.email || ''
        );

        // Data is now already in the correct format
        setData(evaluationData);

        // Show success message if using real API
        // Always show the API availability message for now
        console.log('✅ Loaded evaluation data from backend API');
      } catch (error) {
        console.error('Failed to load evaluation data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadEvaluationData();
  }, [user]);

  const handleGoBack = () => {
    setLocation('/company-dashboard');
  };

  const handleGoHome = () => {
    setLocation('/company-dashboard');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-700 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-slate-300 text-lg">Loading evaluation report...</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-700 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">Report Not Found</h2>
          <p className="text-slate-300 mb-4">Unable to load the evaluation report.</p>
          <Button
            onClick={handleGoBack}
            variant="outline"
            className="!border-slate-600 !text-slate-200 hover:!bg-slate-700 hover:!text-white bg-transparent"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Go Back
          </Button>
        </div>
      </div>
    );
  }

  const getScoreColor = (score: number) => {
    if (score >= 4.5) return 'text-green-400';
    if (score >= 4.0) return 'text-blue-400';
    if (score >= 3.5) return 'text-yellow-400';
    if (score >= 3.0) return 'text-orange-400';
    return 'text-red-400';
  };

  const getScoreBadge = (score: number) => {
    if (score >= 4.5) return { text: 'Outstanding', color: 'bg-green-600' };
    if (score >= 4.0) return { text: 'Excellent', color: 'bg-blue-600' };
    if (score >= 3.5) return { text: 'Good', color: 'bg-yellow-600' };
    if (score >= 3.0) return { text: 'Satisfactory', color: 'bg-orange-600' };
    return { text: 'Needs Improvement', color: 'bg-red-600' };
  };

  const scoreBadge = getScoreBadge(data.overall_score);
  const initials = data.candidate_name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .toUpperCase();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-700">
      <div className="container mx-auto px-4 py-6">
        {/* Navigation Header */}
        <div className="flex items-center justify-between mb-8">
          <Button
            onClick={handleGoBack}
            variant="outline"
            className="!border-slate-600 !text-slate-200 hover:!bg-slate-700 hover:!text-white bg-transparent"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>

          <Button
            onClick={handleGoHome}
            variant="outline"
            className="!border-slate-600 !text-slate-200 hover:!bg-slate-700 hover:!text-white bg-transparent"
          >
            <Home className="w-4 h-4 mr-2" />
            Home
          </Button>
        </div>

        {/* Candidate Overview */}
        <SectionCard title="Candidate Overview" icon={<User className="w-5 h-5" />}>
          <div className="flex items-center space-x-6">
            {data.candidate_profile_image ? (
              <img
                src={data.candidate_profile_image}
                alt={`${data.candidate_name}'s profile`}
                className="w-20 h-20 rounded-full object-cover border-2 border-slate-500"
              />
            ) : (
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-2xl font-bold border-2 border-slate-500">
                {initials}
              </div>
            )}

            <div className="flex-1">
              <h1 className="text-3xl font-bold text-white mb-2">{data.candidate_name}</h1>
              <div className="flex items-center space-x-4 mb-3">
                <Badge className={`${scoreBadge.color} text-white px-3 py-1`}>
                  {scoreBadge.text}
                </Badge>
                <div className="flex items-center space-x-1">
                  <Star className="w-5 h-5 text-yellow-400 fill-current" />
                  <span className="text-white font-semibold">
                    {data.overall_score.toFixed(1)}/5.0
                  </span>
                </div>
              </div>
              <p className="text-slate-300 text-lg">
                {data.overall_visual_summary.key_insights.join('. ')}
              </p>
            </div>
          </div>
        </SectionCard>

        {/* Key Insights */}
        <SectionCard title="Key Insights" icon={<Target className="w-5 h-5" />}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
              <h4 className="text-white font-semibold mb-2 flex items-center">
                <TrendingUp className="w-4 h-4 mr-2 text-green-400" />
                Strengths
              </h4>
              <ul className="space-y-1">
                {data.code_analysis.code_overall_summary.map((achievement, idx) => (
                  <li key={idx} className="text-slate-300 text-sm flex items-start">
                    <CheckCircle className="w-3 h-3 mr-2 mt-0.5 text-green-400 flex-shrink-0" />
                    {achievement}
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
              <h4 className="text-white font-semibold mb-2 flex items-center">
                <AlertCircle className="w-4 h-4 mr-2 text-yellow-400" />
                Areas for Improvement
              </h4>
              <ul className="space-y-1">
                {data.code_analysis.code_dimension_summary
                  .filter(
                    (dim) =>
                      dim.rating.toLowerCase().includes('need') ||
                      dim.rating.toLowerCase().includes('poor')
                  )
                  .map((area, idx) => (
                    <li key={idx} className="text-slate-300 text-sm flex items-start">
                      <AlertCircle className="w-3 h-3 mr-2 mt-0.5 text-yellow-400 flex-shrink-0" />
                      {area.name}: {area.comment}
                    </li>
                  ))}
                {data.code_analysis.code_dimension_summary.filter(
                  (dim) =>
                    dim.rating.toLowerCase().includes('need') ||
                    dim.rating.toLowerCase().includes('poor')
                ).length === 0 && (
                  <li className="text-slate-300 text-sm flex items-start">
                    <CheckCircle className="w-3 h-3 mr-2 mt-0.5 text-green-400 flex-shrink-0" />
                    No significant areas for improvement identified
                  </li>
                )}
              </ul>
            </div>
          </div>
        </SectionCard>

        {/* Evaluation Metrics */}
        <SectionCard title="Evaluation Metrics" icon={<BarChart3 className="w-5 h-5" />}>
          <div className="space-y-6">
            {data.criteria_scores.map((metric, index) => (
              <div key={index} className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-white font-semibold">{metric.criteria}</h3>
                  <div className="flex items-center space-x-2">
                    <span className={`text-lg font-bold ${getScoreColor(metric.score)}`}>
                      {metric.score.toFixed(1)}
                    </span>
                    <span className="text-slate-400">/ 5.0</span>
                  </div>
                </div>

                <p className="text-slate-300 mb-3">{metric.reason_bullets.join('. ')}</p>

                <div className="space-y-2">
                  <h4 className="text-slate-300 font-medium text-sm">Topics Covered:</h4>
                  <div className="flex flex-wrap gap-2">
                    {metric.topics_covered.map((topic, i) => (
                      <Badge key={i} variant="secondary" className="bg-slate-600 text-slate-200">
                        {topic}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </SectionCard>

        {/* Code Submission */}
        <SectionCard title="Code Submission" icon={<Code className="w-5 h-5" />}>
          <div className="space-y-4">
            <Button
              onClick={() => setShowFullCode(!showFullCode)}
              variant="outline"
              className="!border-slate-600 !text-slate-200 hover:!bg-slate-700 hover:!text-white bg-transparent"
            >
              {showFullCode ? 'Hide Code' : 'Show Full Code'}
            </Button>

            {showFullCode && (
              <div className="bg-slate-900 rounded-lg p-4 border border-slate-600">
                <div className="mb-2">
                  <Badge className="bg-blue-600 text-white">
                    {data.code_submission.language || 'Code'}
                  </Badge>
                </div>
                <pre className="text-slate-200 text-sm overflow-x-auto">
                  <code>{data.code_submission.content}</code>
                </pre>
              </div>
            )}
          </div>
        </SectionCard>

        {/* Activity Analysis */}
        <SectionCard title="Activity Analysis" icon={<TrendingUp className="w-5 h-5" />}>
          <div className="space-y-6">
            {/* Overall Progress */}
            <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
              <h4 className="text-white font-semibold mb-3">Overall Progress</h4>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-slate-300">Completion</span>
                  <span className="text-white font-semibold">
                    {data.code_analysis.completion_percentage}%
                  </span>
                </div>
                <Progress value={data.code_analysis.completion_percentage} className="h-2" />
              </div>
            </div>

            {/* Code Dimension Analysis */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.code_analysis.code_dimension_summary.map((dimension, index) => (
                <div
                  key={index}
                  className="bg-slate-700/50 rounded-lg p-4 border border-slate-600 text-center"
                >
                  <h5 className="text-slate-300 text-sm mb-2">{dimension.name}</h5>
                  <div className="text-lg font-bold text-blue-400 mb-1">{dimension.rating}</div>
                  <div className="text-xs text-slate-400">{dimension.comment}</div>
                </div>
              ))}
            </div>
          </div>
        </SectionCard>

        {/* Panelist Feedback */}
        <SectionCard title="Panelist Feedback" icon={<MessageSquare className="w-5 h-5" />}>
          <div className="space-y-4">
            {data.panelist_feedback.map((panelist, i) => (
              <div key={i} className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
                <div className="flex items-start space-x-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-semibold flex-shrink-0">
                    {panelist.name?.charAt(0) || 'P'}
                  </div>
                  <div className="flex-1">
                    <h4 className="text-white font-semibold">
                      {panelist.name || `Panelist ${i + 1}`}
                    </h4>
                    <p className="text-slate-400 text-sm mb-2">{panelist.role || 'Interviewer'}</p>
                    <ul className="space-y-1">
                      {panelist.summary_bullets.map((bullet, idx) => (
                        <li key={idx} className="text-slate-300 text-sm flex items-start">
                          <span className="w-1 h-1 bg-blue-400 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                          {bullet}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </SectionCard>

        {/* Interview Transcript */}
        <SectionCard
          title="Interview Transcript"
          icon={<FileText className="w-5 h-5" />}
          collapsible
          defaultOpen={false}
        >
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {data.transcript.map((msg, index) => (
              <div
                key={index}
                className={`flex ${msg.speaker === data.candidate_name ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    msg.speaker === data.candidate_name
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-600 text-slate-200'
                  }`}
                >
                  <div className="text-xs opacity-75 mb-1">
                    {msg.speaker} {msg.timestamp && `• ${msg.timestamp}`}
                  </div>
                  <p>{msg.content}</p>
                </div>
              </div>
            ))}
          </div>
        </SectionCard>
      </div>
    </div>
  );
};

export default CandidateEvaluationReport;
