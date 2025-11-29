import React, { useEffect, useState } from 'react';
import { useConfiguration } from '@/contexts/ConfigurationContext';
import { useUser } from '@/contexts/UserContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { ChevronLeft, ChevronRight, CheckCircle, AlertCircle, Building, User, Target, Award, ArrowRight, RefreshCw, Upload } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';

// Step components
import { JobDetailsStep } from './JobDetailsStep';
import { ResumeUploadStep } from './ResumeUploadStep';
import { ReviewAndGenerateStep } from './ReviewAndGenerateStep';
import { InterviewConfigurationResults } from './InterviewConfigurationResults';

// Simplified 3-step configuration
const STEP_CONFIGS = {
  titles: ['Job Details', 'Upload Resumes', 'Review & Submit'],
  descriptions: [
    'Provide the job description via PDF, text, or URL',
    'Upload candidate resumes for processing',
    'Review and submit to generate interview setup'
  ],
  icons: [Target, Upload, Award]
};

export function ConfigurationWizard() {
  const { state, actions } = useConfiguration();
  const { user, isLoading } = useUser();
  const [showResults, setShowResults] = useState(false);
  
  // Debug logging
  console.log('ConfigurationWizard render:', { 
    user, 
    userType: user?.userType, 
    stateUserMode: state.userMode,
    isUserLoading: !user,
    isLoading,
    state: state
  });
  
  // Automatically set user mode based on logged-in user
  useEffect(() => {
    console.log('ConfigurationWizard: useEffect triggered with:', {
      user: user?.userType,
      currentStateUserMode: state.userMode,
      shouldUpdate: user && user.userType !== state.userMode
    });
    
    if (user && user.userType !== state.userMode) {
      console.log('ConfigurationWizard: Updating user mode from', state.userMode, 'to', user.userType);
      // Increase delay to ensure user context is fully loaded
      setTimeout(() => {
        console.log('ConfigurationWizard: Executing updateUserMode with delay');
        actions.updateUserMode(user.userType);
      }, 200);
    }
  }, [user, state.userMode, actions]);
  
  // Additional effect to force user mode sync if needed
  useEffect(() => {
    if (user && state.userMode !== user.userType) {
      console.log('ConfigurationWizard: Force syncing user mode:', {
        userType: user.userType,
        stateUserMode: state.userMode
      });
      actions.updateUserMode(user.userType);
    }
  }, [user, state.userMode, actions]);
  
  // Debug step configuration
  console.log('ConfigurationWizard: Step config:', {
    userMode: state.userMode,
    currentStep: state.currentStep,
    maxSteps: state.maxSteps,
    titles: STEP_CONFIGS.titles,
    descriptions: STEP_CONFIGS.descriptions
  });
  
  // Show loading only while UserContext is initializing or if no user is logged in
  if (isLoading) {
    console.log('ConfigurationWizard: UserContext is loading, showing loading state');
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <Card className="w-full max-w-md bg-slate-800 border-slate-700">
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-slate-200">Loading ...</p>
              <p className="text-sm text-slate-400 mt-2">Please wait while we load your information.</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }
  
  // If not loading but no user, redirect to login
  if (!user) {
    console.log('ConfigurationWizard: No user found, should redirect to login');
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <Card className="w-full max-w-md bg-slate-800 border-slate-700">
          <CardContent className="pt-6">
            <div className="text-center">
              <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
              <p className="text-slate-200">No user found in the server</p>
              <p className="text-sm text-slate-400 mt-2">Please log in to access the configuration wizard.</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }
  
  const renderCurrentStep = () => {
    // Show results page if configuration has been generated
    if (showResults) {
      return <InterviewConfigurationResults />;
    }
    
    // Simplified 3-step process for all users
    switch (state.currentStep) {
      case 1: return <JobDetailsStep />;
      case 2: return <ResumeUploadStep />;
      case 3: return <ReviewAndGenerateStep />;
      default: return <JobDetailsStep />;
    }
  };

  const canProceed = () => {
    console.log('ConfigurationWizard: canProceed called with:', {
      userMode: state.userMode,
      currentStep: state.currentStep,
      jobDetails: state.currentConfig.job_details,
      resumeData: state.currentConfig.resume_data
    });

    // Simplified 3-step process validation
    switch (state.currentStep) {
      case 1:
        // Step 1: Job description is provided (either as text, file, or URL)
        const step1Valid = (
          // Text input: has job description text
          (state.currentConfig.job_details.input_type === 'text' && 
           state.currentConfig.job_details.job_description && 
           state.currentConfig.job_details.job_description.trim().length > 0) ||
          // File upload: has uploaded file
          (state.currentConfig.job_details.input_type === 'pdf' && 
           state.currentConfig.job_details.uploaded_file) ||
          // URL input: has source URL
          (state.currentConfig.job_details.input_type === 'url' && 
           state.currentConfig.job_details.source_url)
        );
        console.log('Step 1 validation:', step1Valid, {
          inputType: state.currentConfig.job_details.input_type,
          hasText: state.currentConfig.job_details.job_description?.trim().length > 0,
          hasFile: !!state.currentConfig.job_details.uploaded_file,
          hasUrl: !!state.currentConfig.job_details.source_url
        });
        return step1Valid;
        
      case 2:
        // Step 2: At least one resume has been uploaded
        const step2Valid = state.currentConfig.resume_data && 
               state.currentConfig.resume_data.file_count &&
               state.currentConfig.resume_data.file_count > 0;
        console.log('Step 2 validation:', step2Valid, {
          resumeData: state.currentConfig.resume_data,
          fileCount: state.currentConfig.resume_data?.file_count
        });
        return step2Valid;
        
      case 3:
        // Step 3: Both job description and resume data are available
        const step3Valid = (
          // Job details validation (same as step 1)
          ((state.currentConfig.job_details.input_type === 'text' && 
            state.currentConfig.job_details.job_description && 
            state.currentConfig.job_details.job_description.trim().length > 0) ||
           (state.currentConfig.job_details.input_type === 'pdf' && 
            state.currentConfig.job_details.uploaded_file) ||
           (state.currentConfig.job_details.input_type === 'url' && 
            state.currentConfig.job_details.source_url)) &&
          // Resume data validation
          state.currentConfig.resume_data &&
          state.currentConfig.resume_data.file_count &&
          state.currentConfig.resume_data.file_count > 0
        );
        console.log('Step 3 validation:', step3Valid);
        return step3Valid;
        
      default:
        return false;
    }
  };

  const canGoBack = () => {
    return state.currentStep > 1;
  };

  const handleNext = async () => {
    if (canProceed()) {
      // If this is the final step, generate configuration instead of just moving to next
      if (state.currentStep === STEP_CONFIGS.titles.length) {
        try {
          await actions.generateFullConfiguration();            // this is the api call to generate the configuration.
          setShowResults(true); // Show results page after successful generation
        } catch (error) {
          console.error('Configuration generation failed:', error);
          // Error handling is done in the context
        }
      } else {
        actions.nextStep(); // this is just moving to the next step.
      }
    }
  };

  const handlePrevious = () => {
    if (canGoBack()) {
      actions.previousStep();
    }
  };

  const getStepIcon = (stepIndex: number) => {
    const IconComponent = STEP_CONFIGS.icons[stepIndex - 1];
    return IconComponent ? <IconComponent className="w-5 h-5" /> : null;
  };

  const getStepStatus = (stepIndex: number) => {
    if (stepIndex < state.currentStep) {
      return 'completed';
    } else if (stepIndex === state.currentStep) {
      return 'current';
    } else {
      return 'upcoming';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-2xl font-bold text-slate-100">
                  {state.userMode === 'company' ? 'Interview Configuration' : 'Practice Interview Setup'}
                </CardTitle>
                <p className="text-slate-300 mt-2">
                  {state.userMode === 'company' 
                    ? 'Configure your interview process and AI interviewers'
                    : 'Set up your personalized interview practice session'
                  }
                </p>
              </div>
              <div className="flex items-center gap-2">
                {state.userMode === 'company' ? (
                  <Building className="w-6 h-6 text-blue-400" />
                ) : (
                  <User className="w-6 h-6 text-green-400" />
                )}
                <Badge variant={state.userMode === 'company' ? 'default' : 'secondary'}>
                  {state.userMode === 'company' ? 'Company Mode' : 'Practice Mode'}
                </Badge>
              </div>
            </div>
          </CardHeader>
        </Card>



        {/* Progress Steps */}
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex-1">
                <div className="flex items-center space-x-4">
                  {STEP_CONFIGS.titles.map((title, index) => {
                    const stepNumber = index + 1;
                    const status = getStepStatus(stepNumber);
                    const isCompleted = status === 'completed';
                    const isCurrent = status === 'current';
                    
                    return (
                      <div key={stepNumber} className="flex items-center">
                        <div className={`flex items-center justify-center w-8 h-8 rounded-full border-2 ${
                          isCompleted 
                            ? 'bg-green-500 border-green-500 text-white' 
                            : isCurrent 
                            ? 'bg-blue-500 border-blue-500 text-white'
                            : 'bg-slate-600 border-slate-500 text-slate-300'
                        }`}>
                          {isCompleted ? (
                            <CheckCircle className="w-5 h-5" />
                          ) : (
                            <span className="text-sm font-medium">{stepNumber}</span>
                          )}
                        </div>
                        <div className="ml-3">
                          <p className={`text-sm font-medium ${
                            isCurrent ? 'text-blue-400' : 'text-slate-300'
                          }`}>
                            {title}
                          </p>
                          <p className="text-xs text-slate-400">
                            {STEP_CONFIGS.descriptions[index]}
                          </p>
                        </div>
                        {stepNumber < STEP_CONFIGS.titles.length && (
                          <div className="ml-4 w-8 h-0.5 bg-slate-600"></div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
            
            <Progress value={(state.currentStep / STEP_CONFIGS.titles.length) * 100} className="w-full" />
          </CardContent>
        </Card>

        {/* Current Step Content */}
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="pt-6">
            {renderCurrentStep()}
          </CardContent>
        </Card>

        {/* Navigation */}
        {/* Navigation Buttons - Only show when not in results mode */}
        {!showResults && (
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <Button
                  variant="outline"
                  onClick={handlePrevious}
                  disabled={!canGoBack()}
                  className="flex items-center gap-2"
                >
                  <ChevronLeft className="w-4 h-4" />
                  Previous
              </Button>
              
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-400">
                  Step {state.currentStep} of {STEP_CONFIGS.titles.length}
                </span>
              </div>
              
              <Button
                onClick={handleNext}
                disabled={!canProceed() || (state.currentStep === STEP_CONFIGS.titles.length && state.isGenerating)}
                className="flex items-center gap-2"
              >
                {state.currentStep === STEP_CONFIGS.titles.length ? (
                  <>
                    {state.isGenerating ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        Generate Interview Configuration
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </>
                ) : (
                  <>
                    Next
                    <ChevronRight className="w-4 h-4" />
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
        )}

        {/* Validation Errors */}
        {state.validationErrors.length > 0 && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <ul className="list-disc list-inside space-y-1">
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
              <ul className="list-disc list-inside space-y-1">
                {state.validationWarnings.map((warning, index) => (
                  <li key={index}>{warning}</li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}
      </div>
    </div>
  );
}
