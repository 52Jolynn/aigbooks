import axios, { type AxiosInstance } from 'axios';
import { consoleMessages } from '@/i18n/zh';

const api: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 30000,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 429) {
      console.warn(consoleMessages.apiRateLimited);
    } else if (error.response?.status >= 500) {
      console.error(consoleMessages.apiServerError);
    }
    return Promise.reject(error);
  },
);

export default api;