export type AppMode = 'candidate-practice' | 'company-interviewing' | 'company-candidate-interview';

export interface ModeConfig {
  mode: AppMode;
  title: string;
  description: string;
  features: {
    candidateSignup: boolean;
    companySignup: boolean;
    candidateDashboard: boolean;
    companyDashboard: boolean;
    interviewConfiguration: boolean;
    practiceMode: boolean;
    screeningMode: boolean;
  };
  routing: {
    defaultRoute: string;
    allowedRoutes: string[];
  };
}

export const MODE_CONFIGS: Record<AppMode, ModeConfig> = {
  'candidate-practice': {
    mode: 'candidate-practice',
    title: 'AI Interview Practice',
    description: 'Practice interviews with AI-powered interviewers',
    features: {
      candidateSignup: true,
      companySignup: false,
      candidateDashboard: true,
      companyDashboard: false,
      interviewConfiguration: true,
      practiceMode: true,
      screeningMode: false,
    },
    routing: {
      defaultRoute: '/candidate-dashboard',
      allowedRoutes: ['/login', '/candidate-dashboard', '/configure', '/interview', '/tutorial'],
    },
  },
  'company-interviewing': {
    mode: 'company-interviewing',
    title: 'AI Interview Screening',
    description: 'Create interviews and screen candidates with AI',
    features: {
      candidateSignup: true,
      companySignup: true,
      candidateDashboard: true,
      companyDashboard: true,
      interviewConfiguration: true,
      practiceMode: false,
      screeningMode: true,
    },
    routing: {
      defaultRoute: '/company-dashboard',
      allowedRoutes: ['/login', '/candidate-dashboard', '/company-dashboard', '/configure'],
    },
  },
  'company-candidate-interview': {
    mode: 'company-candidate-interview',
    title: 'Company Interview Session',
    description: 'Take your scheduled company interview',
    features: {
      candidateSignup: false,
      companySignup: false,
      candidateDashboard: false,
      companyDashboard: false,
      interviewConfiguration: false,
      practiceMode: false,
      screeningMode: true,
    },
    routing: {
      defaultRoute: '/tutorial',
      allowedRoutes: ['/login', '/interview','/tutorial'],
    },
  },
};

export function getCurrentMode(): AppMode {
  let mode = import.meta.env.VITE_APP_MODE as AppMode;
  
  // Fallback: try to detect mode from URL or other indicators
  if (!mode || !MODE_CONFIGS[mode]) {
    // Check if we're in development and try to infer from URL or other clues
    if (import.meta.env.DEV) {
      mode = 'candidate-practice';
    } else {
      console.warn('ModeConfig: Invalid or missing VITE_APP_MODE, defaulting to candidate-practice');
      mode = 'candidate-practice';
    }
  }
  
  return mode;
}

export function getModeConfig(): ModeConfig {
  const mode = getCurrentMode();
  return MODE_CONFIGS[mode];
}

export function isFeatureEnabled(feature: keyof ModeConfig['features']): boolean {
  const config = getModeConfig();
  return config.features[feature];
}

export function isRouteAllowed(route: string): boolean {
  const config = getModeConfig();
  return config.routing.allowedRoutes.includes(route);
}

export function getDefaultRoute(): string {
  const config = getModeConfig();
  return config.routing.defaultRoute;
}
