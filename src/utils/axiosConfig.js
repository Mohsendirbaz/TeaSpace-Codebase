import axios from 'axios';

// Create axios instance with default config
const axiosInstance = axios.create({
  timeout: 10000, // 10 seconds default timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
axiosInstance.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
axiosInstance.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Check if it's a network error
    if (error.code === 'ERR_NETWORK' || error.code === 'ECONNABORTED') {
      console.error('Network error detected:', error.message);
      
      // Don't retry if we've already retried
      if (!originalRequest._retry && originalRequest._retryCount < 3) {
        originalRequest._retry = true;
        originalRequest._retryCount = (originalRequest._retryCount || 0) + 1;
        
        console.log(`Retrying request (attempt ${originalRequest._retryCount}/3)...`);
        
        // Exponential backoff
        const delay = 1000 * Math.pow(2, originalRequest._retryCount - 1);
        await new Promise(resolve => setTimeout(resolve, delay));
        
        return axiosInstance(originalRequest);
      }
    }

    // Check for timeout errors
    if (error.code === 'ECONNABORTED' && error.message.includes('timeout')) {
      console.error('Request timeout:', error.message);
      error.isTimeout = true;
    }

    // Enhanced error object
    const enhancedError = {
      ...error,
      isNetworkError: error.code === 'ERR_NETWORK',
      isTimeout: error.code === 'ECONNABORTED',
      isServerError: error.response && error.response.status >= 500,
      isClientError: error.response && error.response.status >= 400 && error.response.status < 500,
      statusCode: error.response?.status,
      message: error.message || 'Unknown error occurred',
    };

    return Promise.reject(enhancedError);
  }
);

// Helper function to make requests with fallback
export const makeRequestWithFallback = async (config, fallbackFn) => {
  try {
    const response = await axiosInstance(config);
    return response.data;
  } catch (error) {
    console.error('Request failed, using fallback:', error.message);
    
    if (fallbackFn && typeof fallbackFn === 'function') {
      return fallbackFn(error);
    }
    
    throw error;
  }
};

// Helper function to check if service is available
export const checkServiceHealth = async (url) => {
  try {
    const response = await axiosInstance.get(`${url}/health`, {
      timeout: 3000, // Quick timeout for health check
    });
    return response.status === 200;
  } catch (error) {
    console.error(`Service at ${url} is not healthy:`, error.message);
    return false;
  }
};

// Circuit breaker implementation
class CircuitBreaker {
  constructor(threshold = 5, timeout = 60000) {
    this.failureCount = 0;
    this.threshold = threshold;
    this.timeout = timeout;
    this.state = 'CLOSED'; // CLOSED, OPEN, HALF_OPEN
    this.nextAttempt = Date.now();
  }

  async call(fn) {
    if (this.state === 'OPEN') {
      if (Date.now() < this.nextAttempt) {
        throw new Error('Circuit breaker is OPEN');
      }
      this.state = 'HALF_OPEN';
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  onSuccess() {
    this.failureCount = 0;
    this.state = 'CLOSED';
  }

  onFailure() {
    this.failureCount++;
    if (this.failureCount >= this.threshold) {
      this.state = 'OPEN';
      this.nextAttempt = Date.now() + this.timeout;
      console.log(`Circuit breaker opened. Will retry after ${new Date(this.nextAttempt).toLocaleTimeString()}`);
    }
  }

  getState() {
    return {
      state: this.state,
      failureCount: this.failureCount,
      nextAttempt: this.state === 'OPEN' ? new Date(this.nextAttempt).toLocaleTimeString() : null,
    };
  }
}

// Export circuit breaker instance for API calls
export const apiCircuitBreaker = new CircuitBreaker();

export default axiosInstance;