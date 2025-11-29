import { useState, useCallback } from 'react';

interface ErrorState {
  hasError: boolean;
  message: string;
  title?: string;
}

export function useErrorHandler() {
  const [error, setError] = useState<ErrorState>({ hasError: false, message: '' });
  const [isLoading, setIsLoading] = useState(false);

  const handleError = useCallback((error: unknown, title?: string) => {
    let message = 'An unexpected error occurred. Please try again.';
    
    if (error instanceof Error) {
      message = error.message;
    } else if (typeof error === 'string') {
      message = error;
    }

    setError({ hasError: true, message, title });
    setIsLoading(false);
  }, []);

  const clearError = useCallback(() => {
    setError({ hasError: false, message: '' });
  }, []);

  const executeAsync = useCallback(async <T>(
    asyncOperation: () => Promise<T>,
    errorTitle?: string
  ): Promise<T | null> => {
    try {
      setIsLoading(true);
      clearError();
      const result = await asyncOperation();
      setIsLoading(false);
      return result;
    } catch (error) {
      handleError(error, errorTitle);
      return null;
    }
  }, [handleError, clearError]);

  return {
    error,
    isLoading,
    handleError,
    clearError,
    executeAsync
  };
}