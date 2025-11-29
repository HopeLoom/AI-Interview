import React, { useState, useRef } from 'react';
import { useConfiguration } from '@/contexts/ConfigurationContext';
import { useUser } from '@/contexts/UserContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Upload,
  FileText,
  CheckCircle,
  AlertCircle,
  X,
  User,
  Building,
  FolderOpen,
  Files,
} from 'lucide-react';

export function ResumeUploadStep() {
  const { state, actions } = useConfiguration();
  const { user } = useUser();
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isCompany = user?.userType === 'company';
  const isCandidate = user?.userType === 'candidate';

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(Array.from(e.target.files));
    }
  };

  const handleFiles = async (files: File[]) => {
    setError(null);
    setUploading(true);

    try {
      const validFiles: File[] = [];

      // Validate each file
      for (const file of files) {
        const allowedTypes = [
          'application/pdf',
          'application/msword',
          'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
          'text/plain',
        ];

        if (!allowedTypes.includes(file.type)) {
          throw new Error(
            `File ${file.name} is not a supported format. Please upload PDF, Word document, or text files only.`
          );
        }

        if (file.size > 10 * 1024 * 1024) {
          throw new Error(`File ${file.name} is too large. Maximum size is 10MB.`);
        }

        validFiles.push(file);
      }

      // Add valid files to the list
      const newFileList = [...uploadedFiles, ...validFiles];
      setUploadedFiles(newFileList);

      // Update resume data with file count and File objects
      actions.setResumeData({
        file_count: newFileList.length,
        uploaded_files: newFileList, // Store all File objects for backend upload
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process files');
    } finally {
      setUploading(false);
    }
  };

  const removeFile = (index: number) => {
    const newFiles = [...uploadedFiles];
    const removedFile = newFiles.splice(index, 1)[0];
    setUploadedFiles(newFiles);

    // Update resume data to reflect the new file list
    if (newFiles.length === 0) {
      actions.setResumeData({
        file_count: 0,
        uploaded_files: [],
      });
    } else {
      actions.setResumeData({
        file_count: newFiles.length,
        uploaded_files: newFiles, // Update with remaining File objects
      });
    }
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  const clearAllFiles = () => {
    setUploadedFiles([]);
    actions.setResumeData({
      file_count: 0,
      uploaded_files: [],
    });
  };

  const getHeaderContent = () => {
    if (isCompany) {
      return {
        title: 'Upload Candidate Resumes',
        description:
          'Upload candidate resumes to create personalized interview experiences. You can upload multiple files at once.',
      };
    } else {
      return {
        title: 'Upload Your Resume',
        description: 'Upload your resume to help us create a personalized interview experience',
      };
    }
  };

  const getTipsContent = () => {
    if (isCompany) {
      return {
        title: 'Resume Upload Tips',
        tips: [
          'Upload multiple candidate resumes at once',
          'Supported formats: PDF, Word documents, and text files',
          'Maximum file size: 10MB per file',
          'The AI will process all resumes to create targeted interview questions',
          'You can review the uploaded files before proceeding',
        ],
      };
    } else {
      return {
        title: 'Resume Tips',
        tips: [
          'Ensure your resume is up-to-date with your latest experience',
          "Include relevant skills and projects for the role you're practicing",
          'Make sure contact information is current',
          'The AI will use this to create a personalized interview experience',
        ],
      };
    }
  };

  const headerContent = getHeaderContent();
  const tipsContent = getTipsContent();

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="border-0 shadow-xl bg-gradient-to-br from-slate-900/90 to-slate-800/90 border-slate-700">
        <CardHeader>
          <div className="text-center">
            <div className="flex items-center justify-center mb-3">
              {isCompany ? (
                <Files className="w-8 h-8 text-blue-600 mr-3" />
              ) : (
                <User className="w-8 h-8 text-green-600 mr-3" />
              )}
              <h3 className="text-2xl font-bold text-white">{headerContent.title}</h3>
            </div>
            <p className="text-slate-300">{headerContent.description}</p>
          </div>
        </CardHeader>
      </Card>

      {/* File Upload Area */}
      {uploadedFiles.length === 0 && (
        <Card
          className={`border-2 border-dashed transition-colors rounded-lg ${
            dragActive ? 'border-blue-500 bg-blue-500/20' : 'border-slate-600 bg-slate-800/90'
          }`}
        >
          <CardContent className="pt-6">
            <div
              className="text-center p-8"
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <Upload
                className={`w-12 h-12 mx-auto mb-4 ${
                  dragActive ? 'text-blue-500' : 'text-slate-400'
                }`}
              />

              <h4 className="text-lg font-medium mb-2 text-white">
                {isCompany ? 'Drop candidate resumes here' : 'Drop your resume here'}
              </h4>
              <p className="text-slate-400 mb-4">or click to browse files</p>

              <Button
                onClick={openFileDialog}
                variant="outline"
                className="px-6 border-slate-600 text-slate-300 hover:border-blue-400 hover:text-blue-400"
                disabled={uploading}
              >
                {isCompany ? 'Select Resume Files' : 'Select Resume'}
              </Button>

              <input
                ref={fileInputRef}
                type="file"
                multiple={isCompany}
                accept=".pdf,.doc,.docx,.txt"
                onChange={handleFileInput}
                className="hidden"
              />

              <div className="text-sm text-slate-500 mt-4">
                <p>Supported formats: PDF, Word (.doc, .docx), Text (.txt)</p>
                <p>Maximum size: 10MB per file</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Uploaded Files List */}
      {uploadedFiles.length > 0 && (
        <Card className="border-0 shadow-xl bg-gradient-to-br from-slate-900/90 to-slate-800/90 border-slate-700">
          <CardHeader>
            <CardTitle className="flex items-center text-xl text-white">
              <FileText className="w-6 h-6 mr-3 text-blue-400" />
              Uploaded Files ({uploadedFiles.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              {uploadedFiles.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-4 bg-slate-800/50 rounded-lg border border-slate-600"
                >
                  <div className="flex items-center space-x-3">
                    <FileText className="w-6 h-6 text-blue-400" />
                    <div>
                      <p className="font-medium text-white">{file.name}</p>
                      <p className="text-sm text-slate-400">
                        {(file.size / 1024 / 1024).toFixed(2)} MB • {file.type || 'Unknown type'}
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeFile(index)}
                    className="text-red-400 hover:text-red-300 hover:bg-red-500/20"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>

            {isCompany && (
              <div className="mt-4 p-4 bg-blue-500/20 rounded-lg border border-blue-500/30">
                <p className="text-sm text-blue-200">
                  <strong>Note:</strong> {uploadedFiles.length} resume
                  {uploadedFiles.length !== 1 ? 's' : ''} uploaded. These will be processed by our
                  AI to create targeted interview questions for each candidate.
                </p>
              </div>
            )}

            <div className="mt-4 flex space-x-3">
              <Button
                onClick={openFileDialog}
                variant="outline"
                disabled={uploading}
                className="border-slate-600 text-slate-300 hover:border-blue-400 hover:text-blue-400"
              >
                Add More Files
              </Button>
              {uploadedFiles.length > 0 && (
                <Button
                  onClick={clearAllFiles}
                  variant="outline"
                  className="text-red-400 hover:text-red-300 border-red-500/30 hover:border-red-400/50"
                >
                  Clear All
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tips */}
      <Card className="border-0 shadow-xl bg-gradient-to-br from-slate-900/90 to-slate-800/90 border-slate-700">
        <CardHeader>
          <CardTitle className="flex items-center text-xl text-white">
            <CheckCircle className="w-5 h-5 mr-3 text-green-400" />
            {tipsContent.title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-3">
            {tipsContent.tips.map((tip, index) => (
              <li key={index} className="flex items-start space-x-3">
                <div className="w-2 h-2 bg-green-400 rounded-full mt-2 flex-shrink-0"></div>
                <span className="text-sm text-slate-300">{tip}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert variant="destructive" className="border-red-500 bg-red-500/20">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="text-red-200">{error}</AlertDescription>
        </Alert>
      )}

      {/* Loading State */}
      {uploading && (
        <Alert className="border-blue-500 bg-blue-500/20">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-blue-200">Processing files...</span>
          </div>
        </Alert>
      )}
    </div>
  );
}
