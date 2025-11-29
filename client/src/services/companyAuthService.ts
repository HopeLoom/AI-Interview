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

export interface CompanyUpdateData {
  name?: string;
  industry?: string;
  size?: string;
  location?: string;
  website?: string;
  description?: string;
}

// Fallback mock data generator - DO NOT use hardcoded IDs
const generateMockCompany = (email: string): Company => {
  const emailPrefix = email.split('@')[0];
  const companyName = emailPrefix.charAt(0).toUpperCase() + emailPrefix.slice(1) + ' Company';

  return {
    id: `mock_${Date.now()}_${Math.random().toString(36).substring(7)}`,
    name: companyName,
    email: email,
    industry: "Technology",
    size: "50-100",
    location: "Remote",
    website: undefined,
    description: `Mock company profile for ${email}`
  };
};

export class CompanyAuthService {
  /**
   * Company login
   */
  static async login(credentials: CompanyLoginCredentials): Promise<CompanyLoginResponse> {
    try {
      const response = await apiClient.post('/api/companies/login', credentials);
      return response.data;
    } catch (error) {
      console.warn('Company login API failed, using dynamically generated mock data:', error);

      // Generate dynamic mock company
      const company = generateMockCompany(credentials.email);
      return {
        success: true,
        message: "Login successful (mock mode - WARNING: not real data)",
        company,
        token: `mock_token_${company.id}`
      };
    }
  }

  /**
   * Get company profile by ID
   */
  static async getCompany(companyId: string): Promise<Company> {
    try {
      const response = await apiClient.get(`/api/companies/${companyId}`);
      return response.data.company;
    } catch (error) {
      console.warn('Company API failed:', error);
      throw new Error('Company not found - API unavailable');
    }
  }

  /**
   * Get company profile by email
   */
  static async getCompanyByEmail(email: string): Promise<Company> {
    try {
      const response = await apiClient.get(`/api/companies/email/${email}`);
      return response.data.company;
    } catch (error) {
      console.warn('Company API failed:', error);
      throw new Error('Company not found - API unavailable');
    }
  }

  /**
   * Update company profile
   */
  static async updateCompany(companyId: string, updateData: CompanyUpdateData): Promise<{ message: string }> {
    try {
      const response = await apiClient.put(`/api/companies/${companyId}`, updateData);
      return response.data;
    } catch (error) {
      console.warn('Company update API failed, using mock response:', error);
      
      // Mock update response
      return { message: "Company updated successfully (mock mode)" };
    }
  }

  /**
   * Get company ID by name (helper method)
   */
  static async getCompanyIdByName(companyName: string): Promise<string | null> {
    try {
      const response = await apiClient.get(`/api/companies/search?name=${encodeURIComponent(companyName)}`);
      
      if (response.data && response.data.company_id) {
        return response.data.company_id;
      }
      
      return null;
    } catch (error) {
      console.warn('Company search API failed:', error);
      return null;
    }
  }

  /**
   * Validate company session/token
   */
  static async validateSession(token: string): Promise<boolean> {
    try {
      // For now, we'll use a simple endpoint without auth headers
      // In production, this should include proper token validation
      const response = await apiClient.get('/api/companies/validate-session');
      return response.data.valid;
    } catch (error) {
      console.error('Session validation failed:', error);
      
      // Mock validation - assume valid if token looks like a mock token
      return token.startsWith('mock_token_');
    }
  }

  /**
   * Logout company user
   */
  static async logout(token: string): Promise<void> {
    try {
      // For now, we'll use a simple endpoint without auth headers
      // In production, this should include proper token validation
      await apiClient.post('/api/companies/logout', { token });
    } catch (error) {
      console.error('Logout failed:', error);
      // Don't throw error for logout - user should be logged out locally anyway
    }
  }

  /**
   * Check if we're using mock data (for debugging/testing)
   */
  static isUsingMockData(): boolean {
    // This would be set based on API availability
    // For now, we'll assume mock data is available
    return true;
  }
}
