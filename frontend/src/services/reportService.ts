import axios from 'axios';
import toast from 'react-hot-toast';

interface ReportOptions {
  imageId: number;
  format: 'PDF' | 'HTML';
  includeMetadata?: boolean;
  includeVisualizations?: boolean;
}

interface ReportResponse {
  reportId: number;
  imageId: number;
  reportPath: string;
  reportFormat: string;
  generatedAt: string;
  downloadUrl: string;
  shareUrl?: string;
}

export const reportService = {
  generateReport: async (options: ReportOptions): Promise<ReportResponse> => {
    try {
      const response = await axios.post('/api/v1/report/generate', {
        image_id: options.imageId,
        format: options.format,
        include_metadata: options.includeMetadata ?? true,
        include_visualizations: options.includeVisualizations ?? true,
      });
      toast.success('Report generated successfully!');
      return response.data;
    } catch (error) {
      toast.error('Failed to generate report');
      throw error;
    }
  },

  downloadReport: async (reportId: number, format: 'PDF' | 'HTML' = 'PDF'): Promise<void> => {
    try {
      const response = await axios.get(`/api/v1/report/${reportId}/download`, {
        responseType: 'blob',
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `report_${reportId}.${format.toLowerCase()}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('Report downloaded successfully!');
    } catch (error) {
      toast.error('Failed to download report');
      throw error;
    }
  },

  shareReport: async (imageId: number): Promise<string> => {
    try {
      const response = await axios.get(`/api/v1/report/${imageId}/share`);
      const shareUrl = response.data.share_url;
      const fullUrl = `${window.location.origin}${shareUrl}`;
      
      await navigator.clipboard.writeText(fullUrl);
      toast.success('Share link copied to clipboard!');
      
      return fullUrl;
    } catch (error) {
      toast.error('Failed to generate share link');
      throw error;
    }
  },

  getPatientReports: async (patientId: string): Promise<any[]> => {
    try {
      const response = await axios.get(`/api/v1/report/history/${patientId}`);
      return response.data;
    } catch (error) {
      toast.error('Failed to fetch patient reports');
      throw error;
    }
  },

  getSharedReport: async (token: string): Promise<Blob> => {
    try {
      const response = await axios.get(`/api/v1/report/shared/${token}`, {
        responseType: 'blob',
      });
      return response.data;
    } catch (error) {
      toast.error('Failed to load shared report');
      throw error;
    }
  },

  printReport: (reportId: number) => {
    window.open(`/api/v1/report/${reportId}/download?format=PDF`, '_blank');
  },
};

export default reportService;