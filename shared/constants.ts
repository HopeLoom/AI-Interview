// Job types available for interview configuration
// These correspond to template folders in onboarding_data/templates/
export const AVAILABLE_JOB_TYPES = [
  {
    value: 'ml_engineer',
    label: 'Machine Learning Engineer',
    description: 'AI/ML focused engineering roles'
  },
  {
    value: 'senior_ml_engineer', 
    label: 'Senior Machine Learning Engineer',
    description: 'Advanced ML engineering positions'
  },
  {
    value: 'data_scientist',
    label: 'Data Scientist',
    description: 'Data analysis and modeling roles'
  },
  {
    value: 'software_engineer',
    label: 'Software Engineer',
    description: 'General software development roles'
  },
  {
    value: 'ai_engineer',
    label: 'AI Engineer',
    description: 'Artificial intelligence focused roles'
  },
  {
    value: 'data_engineer',
    label: 'Data Engineer',
    description: 'Data infrastructure and pipeline roles'
  },
  {
    value: 'product_manager',
    label: 'Product Manager',
    description: 'Product strategy and management roles'
  },
  {
    value: 'devops_engineer',
    label: 'DevOps Engineer',
    description: 'Infrastructure and deployment roles'
  },
  {
    value: 'frontend_engineer',
    label: 'Frontend Engineer',
    description: 'User interface and web development roles'
  },
  {
    value: 'backend_engineer',
    label: 'Backend Engineer',
    description: 'Server-side and API development roles'
  }
] as const;

export type JobType = typeof AVAILABLE_JOB_TYPES[number]['value'];

// Helper function to get job type by value
export function getJobTypeByValue(value: string): typeof AVAILABLE_JOB_TYPES[number] | undefined {
  return AVAILABLE_JOB_TYPES.find(job => job.value === value);
}

// Helper function to get job type by label
export function getJobTypeByLabel(label: string): typeof AVAILABLE_JOB_TYPES[number] | undefined {
  return AVAILABLE_JOB_TYPES.find(job => job.label.toLowerCase() === label.toLowerCase());
}
