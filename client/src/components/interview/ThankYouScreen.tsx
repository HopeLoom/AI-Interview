import React from 'react';

interface ThankYouScreenProps {
  isVisible?: boolean;
  interviewDuration?: string;
  role?: string;
  company?: string;
  onClose?: () => void;
}

export default function ThankYouScreen({
  interviewDuration,
  role,
  company,
  onClose
}: ThankYouScreenProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 text-white p-8">
      <div className="text-center max-w-2xl space-y-6">
        <div className="text-6xl mb-4">🙏</div>
        <h1 className="text-4xl font-bold">Thank You!</h1>
        <p className="text-xl text-blue-200">
          Your interview has been completed. We appreciate your time and participation.
        </p>
        {company && role && (
          <p className="text-lg text-blue-300">
            {company} - {role}
          </p>
        )}
        {interviewDuration && (
          <p className="text-lg text-blue-300">
            Interview Duration: {interviewDuration}
          </p>
        )}
        {onClose && (
          <button
            onClick={onClose}
            className="mt-6 px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-medium transition-colors"
          >
            Close
          </button>
        )}
        {!onClose && (
          <p className="text-lg text-blue-300">
            You can close this window now.
          </p>
        )}
      </div>
    </div>
  );
}

