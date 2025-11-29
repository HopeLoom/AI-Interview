import React, { useState, useEffect } from 'react';
import { useConfiguration } from '@/contexts/ConfigurationContext';
import { useLocation, useRoute } from 'wouter';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { apiClient } from '@/services/apiClient';
import { useToast } from '@/hooks/use-toast';
import {
  CheckCircle,
  Clock,
  Users,
  Code,
  Building,
  Briefcase,
  MessageSquare,
  AlertCircle,
  Download,
  FileText,
  Target,
  Edit3,
  Save,
  X,
  Sparkles,
  User,
  Calendar,
  Zap,
  Award,
  Star,
  TrendingUp,
  ArrowLeft,
} from 'lucide-react';

interface InterviewRound {
  description: string;
  objective: string;
  metrics_covered: string[];
  topic_info: Array<{
    name: string;
    description: string;
    time_limit: number;
    subtopics?: Array<{
      name: string;
      description: string;
      time_limit?: number;
      sections?: string[];
    }>;
  }>;
}

interface Character {
  character_id: string;
  character_name: string;
  role: string;
  objective: string;
  job_description: string;
  interview_round_part_of: string;
}

// Import the GeneratedConfiguration interface from the context
import { GeneratedConfiguration } from '@/contexts/ConfigurationContext';

export default function InterviewConfigurationResults() {
  const { state, actions } = useConfiguration();
  const [, setLocation] = useLocation();
  const [match, params] = useRoute('/results/:sessionId');
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(true);
  const [generatedConfig, setGeneratedConfig] = useState<GeneratedConfiguration | null>(null);
  const [evaluationData, setEvaluationData] = useState<any>(null);
  const [editingMode, setEditingMode] = useState(false);
  const [editedConfig, setEditedConfig] = useState<GeneratedConfiguration | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  // Fetch evaluation data if sessionId is provided in URL
  useEffect(() => {
    if (match && params?.sessionId) {
      const fetchEvaluation = async () => {
        try {
          setIsLoading(true);
          const response = await apiClient.get(
            `/api/configurations/sessions/${params.sessionId}/evaluation`
          );

          if (response.data.success) {
            setEvaluationData(response.data);
            setIsLoading(false);
          } else {
            throw new Error('Failed to fetch evaluation');
          }
        } catch (error: any) {
          console.error('Error fetching evaluation:', error);
          toast({
            title: 'Error',
            description: error.response?.data?.detail || 'Failed to load interview results',
            variant: 'destructive',
          });
          setIsLoading(false);
        }
      };

      fetchEvaluation();
    } else if (state.generatedConfig) {
      // Fallback to configuration context for configuration results
      setGeneratedConfig(state.generatedConfig);
      setEditedConfig(state.generatedConfig);
      setIsLoading(false);
    } else {
      setIsLoading(true);
    }
  }, [match, params, state.generatedConfig, toast]);

  const handleEdit = () => {
    setEditingMode(true);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // Here you would send the updated configuration to the backend
      console.log('Saving updated configuration:', editedConfig);

      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000));

      setGeneratedConfig(editedConfig);
      setEditingMode(false);
    } catch (error) {
      console.error('Failed to save configuration:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setEditedConfig(generatedConfig);
    setEditingMode(false);
  };

  const updateField = (path: string, value: any) => {
    if (!editedConfig) return;

    const pathArray = path.split('.');
    const newConfig = { ...editedConfig };
    let current: any = newConfig;

    for (let i = 0; i < pathArray.length - 1; i++) {
      current = current[pathArray[i]];
    }

    current[pathArray[pathArray.length - 1]] = value;
    setEditedConfig(newConfig);
  };

  const handleViewCandidates = () => {
    // Navigate to company dashboard and show candidates view
    setLocation('/company-dashboard/candidates');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
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
                <h2 className="text-2xl font-bold text-white mb-2">
                  Generating Your Interview Configuration
                </h2>
                <p className="text-slate-300">
                  Our AI is analyzing your job requirements and creating a comprehensive interview
                  setup...
                </p>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between text-sm text-slate-400">
                  <span>Processing job description...</span>
                  <span>✓</span>
                </div>
                <div className="flex justify-between text-sm text-slate-400">
                  <span>Analyzing candidate resumes...</span>
                  <span>✓</span>
                </div>
                <div className="flex justify-between text-sm text-slate-400">
                  <span>Generating interview rounds...</span>
                  <span className="animate-pulse">⟳</span>
                </div>
                <div className="flex justify-between text-sm text-slate-400">
                  <span>Creating interview characters...</span>
                  <span className="animate-pulse">⟳</span>
                </div>
              </div>

              <Progress value={75} className="w-full" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!generatedConfig) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <Card className="w-full max-w-md bg-slate-800 border-slate-700">
          <CardContent className="pt-6">
            <div className="text-center">
              <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">Configuration Not Found</h3>
              <p className="text-slate-300">
                Unable to load the generated interview configuration.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const config = editingMode ? editedConfig! : generatedConfig;

  // Handle the actual API response structure with fallbacks
  const interviewData =
    config?.simulation_config?.interview_data || config?.simulation_config || {};
  const rounds = interviewData.interview_round_details?.rounds || {};
  const characters = interviewData.character_data?.data || [];

  // Add fallback data if the API response is missing expected structure
  const hasValidData =
    config &&
    (config.simulation_config ||
      config.generated_question ||
      config.generated_characters ||
      config.candidate_profile);

  const totalRounds = Object.keys(rounds).length;
  const totalCharacters = characters.length;
  const totalDuration = Object.values(rounds).reduce((total: number, round: any) => {
    const topicInfo = round.topic_info || [];
    return (
      total +
      topicInfo.reduce((roundTotal: number, topic: any) => roundTotal + (topic.time_limit || 0), 0)
    );
  }, 0);

  // Show message if no configuration data is available
  if (!hasValidData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <Card className="w-full max-w-2xl bg-slate-800 border-slate-700">
          <CardContent className="pt-8 pb-8">
            <div className="text-center space-y-6">
              <div className="w-24 h-24 mx-auto bg-gradient-to-br from-red-500 to-red-600 rounded-full flex items-center justify-center">
                <AlertCircle className="w-12 h-12 text-white" />
              </div>

              <div>
                <h2 className="text-2xl font-bold text-white mb-2">
                  No Configuration Data Available
                </h2>
                <p className="text-slate-300">
                  The interview configuration generation may have failed or the data is not yet
                  available.
                </p>
              </div>

              <Button
                onClick={() => setLocation('/configure')}
                className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-8"
                size="lg"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Configuration
              </Button>
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
            <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl mb-6 shadow-2xl">
              <CheckCircle className="h-10 w-10 text-white" />
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-white to-green-200 bg-clip-text text-transparent">
              Interview Configuration Generated!
            </h1>
            <p className="text-slate-300 text-lg max-w-2xl mx-auto">
              Your AI-powered interview setup is ready. Review the details below and make any
              adjustments before finalizing.
            </p>

            {/* Action Buttons */}
            <div className="flex gap-4 justify-center">
              {editingMode ? (
                <>
                  <Button
                    onClick={handleSave}
                    disabled={isSaving}
                    className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white px-8"
                    size="lg"
                  >
                    {isSaving ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                        Saving...
                      </>
                    ) : (
                      <>
                        <Save className="w-4 h-4 mr-2" />
                        Save Changes
                      </>
                    )}
                  </Button>
                  <Button
                    onClick={handleCancel}
                    variant="outline"
                    className="border-slate-600 text-slate-200 hover:bg-slate-700 px-8"
                    size="lg"
                  >
                    <X className="w-4 h-4 mr-2" />
                    Cancel
                  </Button>
                </>
              ) : (
                <Button
                  onClick={handleEdit}
                  className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-8"
                  size="lg"
                >
                  <Edit3 className="w-4 h-4 mr-2" />
                  Edit Configuration
                </Button>
              )}
            </div>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Card className="bg-gradient-to-br from-blue-900/50 to-blue-800/50 border-blue-700">
              <CardContent className="pt-6 text-center">
                <div className="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center mx-auto mb-3">
                  <Users className="w-6 h-6 text-blue-400" />
                </div>
                <div className="text-2xl font-bold text-blue-300">{totalRounds}</div>
                <div className="text-sm text-blue-200">Interview Rounds</div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-green-900/50 to-green-800/50 border-green-700">
              <CardContent className="pt-6 text-center">
                <div className="w-12 h-12 bg-green-500/20 rounded-lg flex items-center justify-center mx-auto mb-3">
                  <User className="w-6 h-6 text-green-400" />
                </div>
                <div className="text-2xl font-bold text-green-300">{totalCharacters}</div>
                <div className="text-sm text-green-200">Interviewers</div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-orange-900/50 to-orange-800/50 border-orange-700">
              <CardContent className="pt-6 text-center">
                <div className="w-12 h-12 bg-orange-500/20 rounded-lg flex items-center justify-center mx-auto mb-3">
                  <Clock className="w-6 h-6 text-orange-400" />
                </div>
                <div className="text-2xl font-bold text-orange-300">{totalDuration}m</div>
                <div className="text-sm text-orange-200">Total Duration</div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-purple-900/50 to-purple-800/50 border-purple-700">
              <CardContent className="pt-6 text-center">
                <div className="w-12 h-12 bg-purple-500/20 rounded-lg flex items-center justify-center mx-auto mb-3">
                  <Zap className="w-6 h-6 text-purple-400" />
                </div>
                <div className="text-2xl font-bold text-purple-300">AI</div>
                <div className="text-sm text-purple-200">Powered</div>
              </CardContent>
            </Card>
          </div>

          {/* Job Details */}
          <Card className="bg-gradient-to-br from-slate-900/90 to-slate-800/90 border-slate-700">
            <CardHeader>
              <CardTitle className="flex items-center gap-3 text-xl text-white">
                <Building className="w-6 h-6 text-blue-400" />
                Job Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-slate-300 mb-2 block">Job Title</label>
                  {editingMode ? (
                    <Input
                      value={interviewData.job_details?.job_title || ''}
                      onChange={(e) =>
                        updateField(
                          'simulation_config.interview_data.job_details.job_title',
                          e.target.value
                        )
                      }
                      className="bg-slate-800 border-slate-600 text-white"
                    />
                  ) : (
                    <div className="p-3 bg-slate-800 border border-slate-600 rounded-lg text-white">
                      {interviewData.job_details?.job_title || 'Job Title'}
                    </div>
                  )}
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-300 mb-2 block">Company</label>
                  {editingMode ? (
                    <Input
                      value={interviewData.job_details?.company_name || ''}
                      onChange={(e) =>
                        updateField(
                          'simulation_config.interview_data.job_details.company_name',
                          e.target.value
                        )
                      }
                      className="bg-slate-800 border-slate-600 text-white"
                    />
                  ) : (
                    <div className="p-3 bg-slate-800 border border-slate-600 rounded-lg text-white">
                      {interviewData.job_details?.company_name || 'Company Name'}
                    </div>
                  )}
                </div>
              </div>

              <div>
                <label className="text-sm font-medium text-slate-300 mb-2 block">
                  Job Description
                </label>
                {editingMode ? (
                  <Textarea
                    value={interviewData.job_details?.job_description || ''}
                    onChange={(e) =>
                      updateField(
                        'simulation_config.interview_data.job_details.job_description',
                        e.target.value
                      )
                    }
                    className="min-h-[100px] bg-slate-800 border-slate-600 text-white"
                  />
                ) : (
                  <div className="p-3 bg-slate-800 border border-slate-600 rounded-lg text-white">
                    {interviewData.job_details?.job_description ||
                      'Job description will appear here...'}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Interview Rounds */}
          <Card className="bg-gradient-to-br from-slate-900/90 to-slate-800/90 border-slate-700">
            <CardHeader>
              <CardTitle className="flex items-center gap-3 text-xl text-white">
                <MessageSquare className="w-6 h-6 text-green-400" />
                Interview Structure
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {Object.entries(rounds).map(
                ([roundKey, round]: [string, any], roundIndex: number) => (
                  <div key={roundKey} className="border border-slate-600 rounded-lg p-4">
                    <div className="flex items-center gap-3 mb-4">
                      <Badge
                        variant="secondary"
                        className="bg-blue-500/20 text-blue-300 border-blue-500/30"
                      >
                        Round {roundIndex + 1}
                      </Badge>
                      <h3 className="text-lg font-semibold text-white">{round.description}</h3>
                    </div>

                    <p className="text-slate-300 mb-4">{round.objective}</p>

                    <div className="space-y-3">
                      {round.topic_info.map((topic: any, topicIndex: number) => (
                        <div
                          key={topicIndex}
                          className="bg-slate-800/50 rounded-lg p-3 border border-slate-600"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-medium text-white">{topic.name}</h4>
                            <Badge
                              variant="outline"
                              className="text-orange-300 border-orange-500/30"
                            >
                              {topic.time_limit}m
                            </Badge>
                          </div>
                          <p className="text-sm text-slate-400 mb-3">{topic.description}</p>

                          {topic.subtopics && (
                            <div className="space-y-2">
                              {topic.subtopics.map((subtopic: any, subtopicIndex: number) => (
                                <div key={subtopicIndex} className="bg-slate-700/50 rounded p-2">
                                  <div className="flex items-center justify-between">
                                    <span className="text-sm text-slate-300">{subtopic.name}</span>
                                    {subtopic.time_limit && (
                                      <span className="text-xs text-slate-500">
                                        {subtopic.time_limit}m
                                      </span>
                                    )}
                                  </div>
                                  <p className="text-xs text-slate-500 mt-1">
                                    {subtopic.description}
                                  </p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )
              )}
            </CardContent>
          </Card>

          {/* Interview Characters */}
          <Card className="bg-gradient-to-br from-slate-900/90 to-slate-800/90 border-slate-700">
            <CardHeader>
              <CardTitle className="flex items-center gap-3 text-xl text-white">
                <Users className="w-6 h-6 text-purple-400" />
                Interview Panel
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {characters.map((character: any, index: number) => (
                  <div
                    key={character.character_id}
                    className="bg-gradient-to-br from-slate-800 to-slate-700 rounded-lg p-4 border border-slate-600"
                  >
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-full flex items-center justify-center">
                        <User className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-white">{character.character_name}</h4>
                        <p className="text-sm text-purple-300">{character.role}</p>
                      </div>
                    </div>

                    <p className="text-sm text-slate-300 mb-3">{character.objective}</p>

                    <Badge variant="outline" className="text-xs text-slate-400 border-slate-500">
                      {character.interview_round_part_of.replace('_', ' ')}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Activity Details */}
          <Card className="bg-gradient-to-br from-slate-900/90 to-slate-800/90 border-slate-700">
            <CardHeader>
              <CardTitle className="flex items-center gap-3 text-xl text-white">
                <Code className="w-6 h-6 text-orange-400" />
                Technical Challenge
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-slate-300 mb-2 block">Scenario</label>
                {editingMode ? (
                  <Textarea
                    value={interviewData.activity_details?.scenario || ''}
                    onChange={(e) =>
                      updateField(
                        'simulation_config.interview_data.activity_details.scenario',
                        e.target.value
                      )
                    }
                    className="min-h-[80px] bg-slate-800 border-slate-600 text-white"
                  />
                ) : (
                  <div className="p-3 bg-slate-800 border border-slate-600 rounded-lg text-white">
                    {interviewData.activity_details?.scenario ||
                      'Activity scenario will appear here...'}
                  </div>
                )}
              </div>

              <div>
                <label className="text-sm font-medium text-slate-300 mb-2 block">Task</label>
                {editingMode ? (
                  <Textarea
                    value={interviewData.activity_details?.task_for_the_candidate || ''}
                    onChange={(e) =>
                      updateField(
                        'simulation_config.interview_data.activity_details.task_for_the_candidate',
                        e.target.value
                      )
                    }
                    className="min-h-[80px] bg-slate-800 border-slate-600 text-white"
                  />
                ) : (
                  <div className="p-3 bg-slate-800 border border-slate-600 rounded-lg text-white">
                    {interviewData.activity_details?.task_for_the_candidate ||
                      'Task description will appear here...'}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Configuration Sharing */}
          <Card className="bg-gradient-to-br from-slate-800/90 to-slate-700/90 border-slate-600">
            <CardHeader>
              <CardTitle className="text-xl text-white flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-blue-400" />
                Share This Interview
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Prominent Invitation Code Display */}
              <div className="bg-gradient-to-r from-blue-900/50 to-purple-900/50 border-2 border-blue-500/50 rounded-lg p-6 text-center">
                <label className="text-sm font-medium text-blue-300 mb-3 block uppercase tracking-wide">
                  Interview Code
                </label>
                <div className="text-5xl font-bold text-white tracking-widest mb-4 font-mono">
                  {config.invitation_code || 'N/A'}
                </div>
                <Button
                  onClick={() => {
                    if (config.invitation_code) {
                      navigator.clipboard.writeText(config.invitation_code);
                    }
                  }}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                  size="lg"
                >
                  Copy Code
                </Button>
                <p className="text-xs text-blue-200 mt-3">
                  Candidates can use this code to join the interview
                </p>
              </div>

              <div>
                <label className="text-sm font-medium text-slate-300 mb-2 block">
                  Configuration ID
                </label>
                <div className="flex gap-2">
                  <Input
                    value={config.configuration_id || 'No ID available'}
                    readOnly
                    className="bg-slate-700 border-slate-600 text-white font-mono text-sm"
                  />
                  <Button
                    onClick={() => {
                      if (config.configuration_id) {
                        navigator.clipboard.writeText(config.configuration_id);
                      }
                    }}
                    variant="outline"
                    className="border-slate-600 text-slate-200 hover:bg-slate-700"
                  >
                    Copy
                  </Button>
                </div>
              </div>

              <div>
                <label className="text-sm font-medium text-slate-300 mb-2 block">
                  Direct Interview Link
                </label>
                <div className="flex gap-2">
                  <Input
                    value={
                      config.configuration_id
                        ? `${window.location.origin}/interview?config_id=${config.configuration_id}`
                        : 'No link available'
                    }
                    readOnly
                    className="bg-slate-700 border-slate-600 text-white text-sm"
                  />
                  <Button
                    onClick={() => {
                      if (config.configuration_id) {
                        const link = `${window.location.origin}/interview?config_id=${config.configuration_id}`;
                        navigator.clipboard.writeText(link);
                      }
                    }}
                    variant="outline"
                    className="border-slate-600 text-slate-200 hover:bg-slate-700"
                  >
                    Copy Link
                  </Button>
                </div>
                <p className="text-xs text-slate-400 mt-2">
                  Or share this direct link with candidates
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Final Actions */}
          <div className="text-center space-y-4">
            <div className="flex gap-4 justify-center flex-wrap">
              <Button
                onClick={() => {
                  if (config.configuration_id) {
                    setLocation(`/interview?config_id=${config.configuration_id}`);
                  }
                }}
                className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white px-12"
                size="lg"
                disabled={!config.configuration_id}
              >
                <Zap className="w-5 h-5 mr-2" />
                Start Interview Now
              </Button>

              <Button
                onClick={handleViewCandidates}
                className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-12"
                size="lg"
              >
                <Users className="w-5 h-5 mr-2" />
                View Dashboard
              </Button>
            </div>

            <div className="text-sm text-slate-400">
              Your interview configuration is ready! Start the interview or share the link with
              candidates.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
