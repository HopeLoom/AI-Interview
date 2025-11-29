import React, { useEffect, useState } from 'react';
import { useConfiguration } from '@/contexts/ConfigurationContext';
import { useUser } from '@/contexts/UserContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
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
  Play,
  FileText,
  Target
} from 'lucide-react';

export function ReviewAndGenerateStep() {
  const { state, actions } = useConfiguration();
  const { user } = useUser();

  const [jobAnalysis, setJobAnalysis] = useState<any>(null);

  // Validate configuration when component mounts
  useEffect(() => {
    actions.validateConfiguration();
  }, []);

  const { currentConfig, generatedConfig, isGenerating, generationProgress, generationStep } = state;
  const isCompany = user?.userType === 'company';

  // Parse job description for company mode
  useEffect(() => {
    if (isCompany && currentConfig.job_details.job_description && !jobAnalysis) {
      parseJobDescription();
    }
  }, [isCompany, currentConfig.job_details.job_description, jobAnalysis]);

  const parseJobDescription = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/configurations/parse-job-description`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_description: currentConfig.job_details.job_description
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setJobAnalysis(data);
      }
    } catch (error) {
      console.error('Failed to parse job description:', error);
    }
  };



  const handleStartInterview = () => {
    // Navigate to interview - this would be implemented based on your routing
    console.log('Starting interview with configuration:', generatedConfig);
  };

  const downloadConfiguration = () => {
    if (!generatedConfig?.simulation_config) return;
    
    const dataStr = JSON.stringify(generatedConfig.simulation_config, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `interview-config-${Date.now()}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  if (generatedConfig?.success) {
    return (
      <div className="space-y-6">
        {/* Success Message */}
        <Card className="border-0 shadow-xl bg-gradient-to-br from-slate-900/90 to-slate-800/90 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500/20 rounded-lg border border-green-500/30">
                <CheckCircle className="w-6 h-6 text-green-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">
                  Configuration Generated Successfully!
                </h3>
                <p className="text-green-200">
                  Your interview setup is ready. You can now start the interview or download the configuration.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Configuration Summary */}


        {/* Action Buttons */}
        <div className="flex gap-4">
          <Button
            onClick={handleStartInterview}
            className="flex-1 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white"
            size="lg"
          >
            <Play className="w-5 h-5 mr-2" />
            Start Interview
          </Button>
          <Button
            onClick={downloadConfiguration}
            variant="outline"
            className="flex-1 border-slate-600 text-slate-200 hover:bg-slate-700"
            size="lg"
          >
            <Download className="w-5 h-5 mr-2" />
            Download Config
          </Button>
        </div>
      </div>
    );
  }

  if (isGenerating) {
    return (
      <div className="space-y-6">
        <Card className="border-0 shadow-xl bg-gradient-to-br from-slate-900/90 to-slate-800/90 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">Generating Interview Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Progress value={generationProgress} className="w-full" />
            <div className="text-center text-slate-300">
              <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
              <p className="text-sm">{generationStep}</p>
              <p className="text-xs text-slate-400 mt-1">{generationProgress}% complete</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="border-0 shadow-xl bg-gradient-to-br from-slate-900/90 to-slate-800/90 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            {isCompany ? (
              <>
                <Building className="w-6 h-6 text-blue-400" />
                Company Interview Configuration Review
              </>
            ) : (
              <>
                <Target className="w-6 h-6 text-green-400" />
                Interview Configuration Review
              </>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-slate-300">
            {isCompany 
              ? "Review your job details and candidate resumes before generating the interview configuration."
              : "Review your interview configuration before starting the practice session."
            }
          </p>
        </CardContent>
      </Card>

      {/* Configuration Summary */}
      <Card className="border-0 shadow-xl bg-gradient-to-br from-slate-900/90 to-slate-800/90 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">Configuration Summary</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Job Details Summary */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Briefcase className="w-4 h-4 text-slate-400" />
              <h4 className="font-medium text-white">Job Details</h4>
            </div>
            <div className="pl-6 space-y-2 text-sm text-slate-200">
              <div><strong>Input Method:</strong> {currentConfig.job_details.input_type.toUpperCase()}</div>
              {currentConfig.job_details.source_filename && (
                <div><strong>Source File:</strong> {currentConfig.job_details.source_filename}</div>
              )}
              {currentConfig.job_details.source_url && (
                <div><strong>Source URL:</strong> {currentConfig.job_details.source_url}</div>
              )}
              {currentConfig.job_details.job_description && (
                <div><strong>Description Preview:</strong> {currentConfig.job_details.job_description.slice(0, 150)}...</div>
              )}
            </div>
          </div>

          {/* Job Analysis for Company Mode */}
          {isCompany && jobAnalysis && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4 text-blue-400" />
                <h4 className="font-medium text-white">AI Job Analysis</h4>
              </div>
              <div className="pl-6 space-y-2 text-sm text-slate-200">
                {jobAnalysis.skills && (
                  <div>
                    <strong>Key Skills:</strong> 
                    <div className="flex flex-wrap gap-1 mt-1">
                      {jobAnalysis.skills.slice(0, 8).map((skill: string, index: number) => (
                        <Badge key={index} variant="secondary" className="text-xs">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
                {jobAnalysis.difficulty && (
                  <div><strong>Difficulty Level:</strong> {jobAnalysis.difficulty}</div>
                )}
                {jobAnalysis.estimated_duration && (
                  <div><strong>Estimated Duration:</strong> {jobAnalysis.estimated_duration} minutes</div>
                )}
              </div>
            </div>
          )}



          {/* Resume Information */}
          {currentConfig.resume_data && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-slate-400" />
                <h4 className="font-medium text-white">Candidate Resumes</h4>
              </div>
              <div className="pl-6 text-sm text-slate-200">
                <div><strong>Total Files:</strong> {currentConfig.resume_data.file_count} resume{currentConfig.resume_data.file_count !== 1 ? 's' : ''}</div>
                <div className="text-xs text-slate-400 mt-1">
                  These resumes will be processed by our AI to create targeted interview questions for each candidate.
                </div>
              </div>
            </div>
          )}

          {/* Configuration Stats */}
          <div className="border-t border-slate-600 pt-4">
            <div className="grid grid-cols-2 gap-4 text-center">
              <div className="p-3 bg-blue-500/20 rounded-lg border border-blue-500/30">
                <div className="text-xl font-bold text-blue-300">
                  {currentConfig.resume_data?.file_count || 0}
                </div>
                <div className="text-xs text-blue-200">Resume Files</div>
              </div>
              <div className="p-3 bg-green-500/20 rounded-lg border border-green-500/30">
                <div className="text-xl font-bold text-green-300">
                  {currentConfig.job_details.input_type.toUpperCase()}
                </div>
                <div className="text-xs text-green-200">Job Input Method</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>



      {/* Validation Errors */}
      {state.validationErrors.length > 0 && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <ul className="list-disc list-inside">
              {state.validationErrors.map((error, index) => (
                <li key={index}>{error}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {/* Validation Warnings */}
      {state.validationWarnings.length > 0 && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <ul className="list-disc list-inside">
              {state.validationWarnings.map((warning, index) => (
                <li key={index}>{warning}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
