# Network Error Mediation Strategies

This document describes the temporary mediation strategies implemented to handle network errors in the Factual Precedence API system.

## Error Types Addressed

1. **ERR_NETWORK**: Complete network failure or unreachable server
2. **ECONNABORTED**: Request timeout
3. **Server errors**: 5xx status codes
4. **Service unavailability**: Circuit breaker pattern

## Implemented Solutions

### 1. Retry Logic with Exponential Backoff

- **Location**: `src/components/find_factual_precedence/components/modules/FactualPrecedence/APIFactualPrecedence.js`
- **Strategy**: Automatically retry failed requests up to 3 times with exponential backoff
- **Delay**: 1s, 2s, 4s between retries

```javascript
// Exponential backoff
await new Promise(resolve => setTimeout(resolve, RETRY_DELAY * Math.pow(2, retryCount)));
```

### 2. Cache-First Approach

- **Session Storage**: Caches successful responses for 30 minutes
- **Stale Cache Fallback**: Uses expired cache data when network fails
- **Cache Key**: Based on itemId and form values

### 3. Fallback Data Generation

Enhanced fallback data for common parameter types:
- Lifetime parameters
- Price parameters
- Carbon-related parameters
- Location/coordinate parameters
- Efficiency parameters
- Capacity parameters

### 4. Circuit Breaker Pattern

- **Location**: `src/utils/axiosConfig.js`
- **Threshold**: 5 consecutive failures
- **Timeout**: 60 seconds cooldown
- **States**: CLOSED → OPEN → HALF_OPEN

### 5. Global Axios Configuration

Created centralized axios instance with:
- Request/response interceptors
- Automatic retry on network errors
- Enhanced error objects
- Health check utilities

### 6. User Feedback

#### Network Status Indicator
- **Component**: `src/components/modules/NetworkStatusIndicator.js`
- **Features**:
  - Real-time network status display
  - Circuit breaker state visibility
  - Pending feedback queue
  - Manual retry options

#### Data Status Warnings
- Shows when using stale cache or fallback data
- Displays reason for degraded service
- Visual indicators in UI

### 7. Offline Feedback Storage

- Stores feedback in localStorage when network fails
- Automatic retry when connection restored
- Manual retry button in status indicator

## Usage

### In Components

```javascript
import { getAPIPrecedenceData } from './APIFactualPrecedence';

try {
  const data = await getAPIPrecedenceData(itemId, formValue);
  // Handle successful response
} catch (error) {
  // Error already handled by retry logic and fallbacks
  console.error('Final error after all retries:', error);
}
```

### Adding Network Status Indicator

```javascript
import NetworkStatusIndicator from './components/modules/NetworkStatusIndicator';

// In your app layout
<NetworkStatusIndicator serviceUrl="http://localhost:3060" />
```

## Benefits

1. **Improved Resilience**: Application continues working during network issues
2. **Better UX**: Users see clear status and have fallback data
3. **Automatic Recovery**: System self-heals when connection restored
4. **Data Persistence**: No loss of user feedback during outages

## Future Improvements

1. Implement service worker for true offline support
2. Add configurable retry policies per endpoint
3. Implement request queuing for offline mode
4. Add telemetry for network reliability monitoring
5. Consider implementing a local database fallback