import axios, { type AxiosInstance } from 'axios';

const api: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 30000,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 429) {
      console.warn('请求过于频繁，请稍后再试');
    } else if (error.response?.status >= 500) {
      console.error('服务器错误');
    }
    return Promise.reject(error);
  },
);

export default api;
