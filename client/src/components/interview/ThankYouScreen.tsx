import React from 'react';

export default function ThankYouScreen() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 text-white p-8">
      <div className="text-center max-w-2xl space-y-6">
        <div className="text-6xl mb-4">🙏</div>
        <h1 className="text-4xl font-bold">Thank You!</h1>
        <p className="text-xl text-blue-200">
          Your interview has been completed. We appreciate your time and participation.
        </p>
        <p className="text-lg text-blue-300">
          You can close this window now.
        </p>
      </div>
    </div>
  );
}

