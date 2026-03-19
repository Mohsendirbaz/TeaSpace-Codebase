// Only import Express on the server
let express;
let router;

// Check if we're in a server environment
if (typeof window === 'undefined' || process.env.NODE_ENV === 'server') {
  express = require('express');
  router = express.Router();
} else {
  // Create a mock router for client-side that will be excluded from the bundle
  router = {
    post: () => {},
    get: () => {},
    use: () => {},
  };
}

const { getLLMFactualPrecedence, getLLMFilteredFactualPrecedence } = require('../services/llmService');
const { factualPrecedenceData } = require('../data/factualPrecedenceData');

const cache = new Map();
const CACHE_DURATION = 24 * 60 * 60 * 1000;

router.post('/api/factual-precedence', async (req, res) => {
  try {
    const { itemId, formContext } = req.body;
    const cacheKey = `${itemId}-${JSON.stringify(formContext)}`;

    const cachedResult = cache.get(cacheKey);
    if (cachedResult && (Date.now() - cachedResult.timestamp < CACHE_DURATION)) {
      return res.json({ success: true, factualPrecedence: cachedResult.data });
    }

    const fallbackData = factualPrecedenceData[itemId];

    try {
      const factualPrecedence = await getLLMFactualPrecedence(itemId, formContext);

      cache.set(cacheKey, {
        data: factualPrecedence,
        timestamp: Date.now()
      });

      return res.json({ success: true, factualPrecedence });
    } catch (llmError) {
      console.error('LLM service error:', llmError);

      if (fallbackData) {
        return res.json({ 
          success: true, 
          factualPrecedence: fallbackData,
          note: "Using cached data due to LLM service unavailability"
        });
      }

      throw llmError;
    }
  } catch (error) {
    console.error('Error in factual precedence API:', error);
    res.status(500).json({ 
      success: false, 
      message: error.message || 'Failed to retrieve factual precedence'
    });
  }
});

router.post('/api/factual-precedence/filtered', async (req, res) => {
  try {
    const { itemId, formContext, filters } = req.body;
    const cacheKey = `${itemId}-${JSON.stringify(formContext)}-${JSON.stringify(filters)}`;

    const cachedResult = cache.get(cacheKey);
    if (cachedResult && (Date.now() - cachedResult.timestamp < CACHE_DURATION)) {
      return res.json({ success: true, factualPrecedence: cachedResult.data });
    }

    const factualPrecedence = await getLLMFilteredFactualPrecedence(itemId, formContext, filters);

    cache.set(cacheKey, {
      data: factualPrecedence,
      timestamp: Date.now()
    });

    return res.json({ success: true, factualPrecedence });
  } catch (error) {
    console.error('Error in filtered factual precedence API:', error);
    res.status(500).json({ 
      success: false, 
      message: error.message || 'Failed to retrieve filtered factual precedence'
    });
  }
});

router.post('/api/factual-precedence/feedback', (req, res) => {
  try {
    const { itemId, feedbackType, comment, timestamp } = req.body;

    const feedbackData = {
      itemId,
      feedbackType,
      comment,
      timestamp
    };

    // TODO: Implement feedback storage
    console.log('Feedback received:', feedbackData);

    res.json({ success: true });
  } catch (error) {
    console.error('Error saving feedback:', error);
    res.status(500).json({ success: false, message: error.message });
  }
});

module.exports = router;
