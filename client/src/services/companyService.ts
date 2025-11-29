import { apiClient } from './apiClient';

// Types for company authentication and profile
export interface Company {
  id: string;
  name: string;
  email: string;
  industry: string;
  size: string;
  location: string;
  website?: string;
  description?: string;
}

export interface CompanyLoginCredentials {
  email: string;
  password: string;
}

export interface CompanyLoginResponse {
  success: boolean;
  message: string;
  company: Company;
  token: string;
}

export interface CompanySignupData {
  name: string;
  email: string;
  userType: 'company';
  industry: string;
  size: string;
  location: string;
  website?: string;
  description?: string;
}

export interface CompanyRegistrationResponse {
  success: boolean;
  message: string;
  company_id: string;
  profile: any;
  next_steps: string;
}

export interface CompanyUpdateData {
  name?: string;
  industry?: string;
  size?: string;
  location?: string;
  website?: string;
  description?: string;
}


export class CompanyService {
  // ==================== AUTHENTICATION METHODS ====================
  
  /**
   * Company login
   */
  static async login(credentials: CompanyLoginCredentials): Promise<CompanyLoginResponse> {
    try {
      const response = await apiClient.post('/api/company/login', credentials);
      return response.data;
    } catch (error) {
      console.error('Company login failed:', error);
      throw new Error('Login failed. Please check your credentials and try again.');
    }
  }

  /**
   * Validate company session/token
   */
  static async validateSession(token: string): Promise<boolean> {
    try {
      const response = await apiClient.get('/api/company/validate-session');
      return response.data.valid;
    } catch (error) {
      console.error('Session validation failed:', error);
      throw new Error('Session validation failed. Please log in again.');
    }
  }

  /**
   * Logout company user
   */
  static async logout(token: string): Promise<void> {
    try {
      await apiClient.post('/api/company/logout', { token });
    } catch (error) {
      console.error('Logout failed:', error);
      throw new Error('Logout failed. Please try again.');
    }
  }

  // ==================== SIGNUP/REGISTRATION METHODS ====================
  
  /**
   * Register a new company user
   */
  static async registerCompany(
    companyData: CompanySignupData
  ): Promise<CompanyRegistrationResponse> {
    try {
      const response = await apiClient.post('/api/company/register-company', companyData);
      return response.data;
    } catch (error) {
      console.error('Company registration failed:', error);
      throw new Error('Failed to register company');
    }
  }

  /**
   * Complete company signup with profile creation
   */
  static async completeCompanySignup(
    companyData: CompanySignupData
  ): Promise<CompanyRegistrationResponse> {
    try {
      // Register the company user
      const registrationResponse = await this.registerCompany(companyData);
      
      if (registrationResponse.success) {
        // Additional company profile setup could go here
        // For example, creating company workspace, default settings, etc.
        console.log('Company registered successfully:', registrationResponse.company_id);
      }
      
      return registrationResponse;
    } catch (error) {
      console.error('Company signup failed:', error);
      throw new Error('Failed to complete company signup');
    }
  }

  /**
   * Validate company email availability
   */
  static async checkEmailAvailability(email: string): Promise<boolean> {
    try {
      const response = await apiClient.get(`/api/company/check-email-availability/${email}`);
      return response.data.available;
    } catch (error) {
      console.error('Email availability check failed:', error);
      throw new Error('Unable to check email availability. Please try again.');
    }
  }

  // ==================== PROFILE MANAGEMENT METHODS ====================
  
  /**
   * Get company profile by ID
   */
  static async getCompany(companyId: string): Promise<Company> {
    try {
      const response = await apiClient.get(`/api/company/${companyId}`);
      return response.data.company;
    } catch (error) {
      console.error('Failed to get company:', error);
      throw new Error('Unable to load company information. Please try again.');
    }
  }

  /**
   * Get company profile by email
   */
  static async getCompanyByEmail(email: string): Promise<Company> {
    try {
      const response = await apiClient.get(`/api/company/email/${email}`);
      return response.data.company;
    } catch (error) {
      console.error('Failed to get company by email:', error);
      throw new Error('Unable to load company information. Please try again.');
    }
  }

  /**
   * Update company profile
   */
  static async updateCompany(companyId: string, updateData: CompanyUpdateData): Promise<{ message: string }> {
    try {
      const response = await apiClient.put(`/api/company/${companyId}`, updateData);
      return response.data;
    } catch (error) {
      console.error('Company update failed:', error);
      throw new Error('Unable to update company information. Please try again.');
    }
  }

  /**
   * Get company ID by name (helper method)
   */
  static async getCompanyIdByName(companyName: string): Promise<string | null> {
    try {
      const response = await apiClient.get(`/api/company/search?name=${encodeURIComponent(companyName)}`);
      
      if (response.data && response.data.company_id) {
        return response.data.company_id;
      }
      
      return null;
    } catch (error) {
      console.error('Company search failed:', error);
      throw new Error('Unable to search for company. Please try again.');
    }
  }

  // ==================== UTILITY METHODS ====================
  
  /**
   * Get company industry options
   */
  static async getIndustryOptions(): Promise<string[]> {
    try {
      // This could fetch from an API or return predefined options
      return [
        'Technology',
        'Healthcare',
        'Finance',
        'Education',
        'Manufacturing',
        'Retail',
        'Consulting',
        'Media & Entertainment',
        'Real Estate',
        'Transportation',
        'Energy',
        'Other'
      ];
    } catch (error) {
      console.error('Failed to fetch industry options:', error);
      return [];
    }
  }

  /**
   * Get company size options
   */
  static async getCompanySizeOptions(): Promise<string[]> {
    try {
      // This could fetch from an API or return predefined options
      return [
        '1-10',
        '11-50',
        '51-200',
        '201-500',
        '501-1000',
        '1001-5000',
        '5000+'
      ];
    } catch (error) {
      console.error('Failed to fetch company size options:', error);
      return [];
    }
  }
}
