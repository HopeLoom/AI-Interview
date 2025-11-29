import React, { useState, useEffect } from 'react';
import { useConfiguration } from '@/contexts/ConfigurationContext';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { 
  Upload, 
  FileText, 
  Building, 
  Briefcase
} from 'lucide-react';
import { interviewConfigurationService, JobType } from '../../services/interviewConfigurationService';

export function JobDetailsStep() {
  const { state, actions } = useConfiguration();
  const [inputMode, setInputMode] = useState<'pdf' | 'text'>('pdf');
  const [jobType, setJobType] = useState<string>(state.currentConfig.job_details.job_title || '');
  const [jobDescription, setJobDescription] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [availableJobTypes, setAvailableJobTypes] = useState<JobType[]>([]);
  const [loadingJobTypes, setLoadingJobTypes] = useState(true);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (file: File) => {
    // Validate file type
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain'
    ];
    
    if (!allowedTypes.includes(file.type)) {
      alert('Please select a PDF, Word document, or text file');
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      alert('File size must be less than 10MB');
      return;
    }

    setSelectedFile(file);
    
    // Store file metadata AND the File object in configuration context
    actions.updateJobDetails({
      job_title: jobType || undefined,
      job_description: '', // Leave empty - backend will process the file
      input_type: 'pdf',
      source_filename: file.name,
      file_size: file.size,
      file_type: file.type,
      uploaded_file: file // Store the actual File object
    });
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleTextSubmit = () => {
    if (jobDescription.trim()) {
      actions.updateJobDetails({
        job_title: jobType || undefined,
        job_description: jobDescription,
        input_type: 'text',
        source_filename: undefined, // Clear file-related fields
        file_size: undefined,
        file_type: undefined,
        uploaded_file: undefined // Clear the File object
      });
    }
  };


  const openFileDialog = () => {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.pdf,.doc,.docx,.txt';
    fileInput.onchange = (e) => {
      const target = e.target as HTMLInputElement;
      if (target.files && target.files[0]) {
        handleFileSelect(target.files[0]);
      }
    };
    fileInput.click();
  };

  const isStepComplete = () => {
    const hasJobType = jobType.trim().length > 0;
    switch (inputMode) {
      case 'pdf':
        return hasJobType && selectedFile !== null;
      case 'text':
        return hasJobType && jobDescription.trim().length > 0;
      default:
        return false;
    }
  };

  // Clear previous data when switching modes
  const handleModeChange = (mode: 'pdf' | 'text') => {
    setInputMode(mode);
    setSelectedFile(null);
    setJobDescription('');
    // Don't clear job type when switching modes - keep it persistent
    
    // Clear the configuration data when switching modes
    actions.updateJobDetails({
      job_title: jobType || undefined,
      job_description: '',
      input_type: mode,
      source_filename: undefined,
      file_size: undefined,
      file_type: undefined,
      uploaded_file: undefined // Clear the File object
    });
  };

  // Load job types on component mount
  useEffect(() => {
    const loadJobTypes = async () => {
      try {
        setLoadingJobTypes(true);
        const jobTypes = await interviewConfigurationService.getAvailableJobTypes();
        setAvailableJobTypes(jobTypes);
      } catch (error) {
        console.error('Failed to load job types:', error);
      } finally {
        setLoadingJobTypes(false);
      }
    };
    
    loadJobTypes();
  }, []);

  const getSelectedJobLabel = () => {
    const selectedJob = availableJobTypes.find(job => job.value === jobType);
    return selectedJob ? selectedJob.label : '';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="border-0 shadow-xl bg-gradient-to-br from-slate-900/90 to-slate-800/90 border-slate-700">
        <CardHeader>
          <div className="text-center">
            <div className="flex items-center justify-center mb-3">
              <Building className="w-8 h-8 text-blue-600 mr-3" />
              <h3 className="text-2xl font-bold text-white">Job Details</h3>
            </div>
            <p className="text-slate-300">
              Upload a file or enter text to provide the job description for your interview configuration
            </p>
          </div>
        </CardHeader>
      </Card>

      {/* Job Type Field */}
      <Card className="border-0 shadow-xl bg-gradient-to-br from-slate-900/90 to-slate-800/90 border-slate-700">
        <CardContent className="pt-6 space-y-4">
          <div className="space-y-3">
            <Label className="text-slate-200 font-semibold text-sm flex items-center gap-2">
              <Briefcase className="w-4 h-4 text-blue-400" />
              Job Type *
            </Label>
            <Select value={jobType} onValueChange={(value: string) => setJobType(value)}>
              <SelectTrigger className="h-12 border-slate-600 bg-slate-800/50 text-slate-200 placeholder:text-slate-400 focus:border-blue-500 focus:ring-blue-500/20 focus:bg-slate-700 transition-all duration-200 shadow-sm">
                <SelectValue placeholder={loadingJobTypes ? "Loading job types..." : "Select a job type..."} />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-slate-600">
                {availableJobTypes.map((job: JobType) => (
                  <SelectItem 
                    key={job.value} 
                    value={job.value}
                    className="text-slate-200 hover:bg-slate-700 focus:bg-slate-700"
                  >
                    <div>
                      <div className="font-medium">{job.label}</div>
                      <div className="text-xs text-slate-400">{job.description}</div>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-slate-400">
              Select the job type that best matches your interview requirements. This will determine the template used for the interview configuration.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Input Mode Selection */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* PDF Upload Option */}
        <Card 
          className={`border-2 transition-all duration-200 cursor-pointer ${
            inputMode === 'pdf' 
              ? 'border-blue-500 bg-blue-500/10' 
              : 'border-slate-700 bg-slate-800/90 hover:border-slate-600'
          }`}
          onClick={() => handleModeChange('pdf')}
        >
          <CardContent className="pt-6 text-center">
            <div className="p-3 bg-blue-500/20 rounded-lg w-fit mx-auto mb-3">
              <Upload className="w-8 h-8 text-blue-400" />
            </div>
            <h4 className="text-lg font-semibold text-white mb-2">Upload PDF</h4>
            <p className="text-sm text-slate-400">
              Upload a job description PDF or document
            </p>
          </CardContent>
        </Card>

        {/* Text Input Option */}
        <Card 
          className={`border-2 transition-all duration-200 cursor-pointer ${
            inputMode === 'text' 
              ? 'border-green-500 bg-green-500/10' 
              : 'border-slate-700 bg-slate-800/90 hover:border-slate-600'
          }`}
          onClick={() => handleModeChange('text')}
        >
          <CardContent className="pt-6 text-center">
            <div className="p-3 bg-green-500/20 rounded-lg w-fit mx-auto mb-3">
              <FileText className="w-8 h-8 text-green-400" />
            </div>
            <h4 className="text-lg font-semibold text-white mb-2">Add Text</h4>
            <p className="text-sm text-slate-400">
              Paste the job description text directly
            </p>
          </CardContent>
        </Card>

      </div>

      {/* PDF Upload Interface */}
      {inputMode === 'pdf' && (
        <Card className="border-0 shadow-xl bg-gradient-to-br from-slate-900/90 to-slate-800/90 border-slate-700">
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-xl text-white">
              <Upload className="w-6 h-6 text-blue-400" />
              Upload Job Description
            </CardTitle>
            <p className="text-slate-300 text-sm">
              Upload a PDF, Word document, or text file containing the job description. The file will be processed by our AI system.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            {!selectedFile ? (
              <div
                className={`border-2 border-dashed transition-colors rounded-lg p-8 text-center ${
                  dragActive ? 'border-blue-500 bg-blue-50' : 'border-slate-600'
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <Upload className={`w-12 h-12 mx-auto mb-4 ${
                  dragActive ? 'text-blue-500' : 'text-slate-400'
                }`} />
                
                <h4 className="text-lg font-medium mb-2 text-white">
                  Drop your job description file here
                </h4>
                <p className="text-slate-400 mb-4">
                  or click to browse files
                </p>
                
                <Button
                  onClick={openFileDialog}
                  variant="outline"
                  className="px-6"
                >
                  Select File
                </Button>
                
                <div className="text-sm text-slate-500 mt-4">
                  <p>Supported formats: PDF, Word (.doc, .docx), Text (.txt)</p>
                  <p>Maximum size: 10MB</p>
                </div>
              </div>
            ) : (
              <div className="p-4 bg-green-500/20 rounded-lg border border-green-500/30">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <FileText className="w-8 h-8 text-green-600" />
                    <div>
                      <p className="font-medium text-green-800">{selectedFile.name}</p>
                      <p className="text-sm text-green-600">
                        {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                      <p className="text-xs text-green-600">
                        Type: {selectedFile.type || 'Unknown'}
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSelectedFile(null);
                      actions.updateJobDetails({
                        job_title: jobType || undefined,
                        job_description: '',
                        input_type: 'pdf',
                        source_filename: undefined,
                        file_size: undefined,
                        file_type: undefined,
                        uploaded_file: undefined // Clear the File object
                      });
                    }}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    Remove
                  </Button>
                </div>
                <p className="text-sm text-green-700 mt-2">
                  File will be processed by our AI system to extract job details
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Text Input Interface */}
      {inputMode === 'text' && (
        <Card className="border-0 shadow-xl bg-gradient-to-br from-slate-900/90 to-slate-800/90 border-slate-700">
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-xl text-white">
              <FileText className="w-6 h-6 text-green-400" />
              Job Description Text
            </CardTitle>
            <p className="text-slate-300 text-sm">
              Paste the job description text below
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <Label className="text-slate-200 font-semibold text-sm">Job Description</Label>
              <Textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="Paste the complete job description here..."
                className="min-h-[300px] border-slate-600 bg-slate-800/50 text-slate-200 placeholder:text-slate-400 focus:border-green-500 focus:ring-green-500/20 focus:bg-slate-700 transition-all duration-200 resize-none shadow-sm"
              />
              <div className="flex justify-between items-center">
                <p className="text-xs text-slate-400">
                  Character count: {jobDescription.length}
                </p>
                <Button
                  onClick={handleTextSubmit}
                  disabled={!jobDescription.trim()}
                  className="px-6 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white"
                >
                  Save Description
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}


      {/* Status Indicator */}
      {isStepComplete() && (
        <Card className="border-0 shadow-xl bg-gradient-to-br from-green-900/90 to-emerald-800/90 border-green-700">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500/20 rounded-lg border border-green-500/30">
                <Briefcase className="w-6 h-6 text-green-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">
                  Job Details Ready
                </h3>
                <p className="text-green-200">
                  Job title: "{getSelectedJobLabel()}" - {inputMode === 'pdf' && 'File uploaded successfully - will be processed by AI'}
                  {inputMode === 'text' && 'Text description saved'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
