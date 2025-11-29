/**
 * Types and utilities for interview details
 */

export interface InterviewDetails {
  candidateName: string;
  role: string;
  company: string;
  duration: string;
  interviewType: string;
  expectations: string[];
  configurationId?: string; // Add configuration ID
}

/**
 * Synchronous version for backward compatibility
 * Uses fallback defaults immediately
 */
export function getInterviewDetails(): InterviewDetails {
  // Parse URL parameters
  let urlParams = new URLSearchParams('');

  // Check if window is defined (for client-side only)
  if (typeof window !== 'undefined') {
    urlParams = new URLSearchParams(window.location.search);
  }

  // Check if there's a configuration ID in URL
  const configId = urlParams.get('config_id');

  // Use default values if URL params are empty
  const candidateName = urlParams.get('name') || 'Candidate';
  const roleParam = urlParams.get('role') || 'ml-engineer';
  const company = urlParams.get('company') || 'HopeLoom';

  // For debugging
  console.log("URL Params:", { candidateName, roleParam, company, configId });


  return {
    candidateName,
    role: 'Technical Role',
    company: 'Company',
    duration: '30 minutes',
    interviewType: 'Technical Interview',
    expectations: [],
    configurationId: configId || undefined
  };
}

/**
 * Load configuration details from configuration ID
 * This will be called from InterviewContext to fetch full configuration
 */
export async function loadConfigurationById(configId: string): Promise<any> {
  try {
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'localhost:8000';
    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
    const url = `${protocol}//${apiBaseUrl}/api/configurations/${configId}`;

    console.log(`Loading configuration from: ${url}`);

    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`Failed to load configuration: ${response.statusText}`);
    }

    const data = await response.json();

    if (!data.success) {
      throw new Error('Configuration loading failed');
    }

    return data.configuration;
  } catch (error) {
    console.error('Error loading configuration:', error);
    throw error;
  }
}
