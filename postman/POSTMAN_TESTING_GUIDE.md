# 🧪 Postman Testing Guide - Stock Research Chatbot v2.1

Complete guide for testing the Stock Research Chatbot API using Postman with smart correction features.

---

## 📦 Setup

### 1. Import Collection

1. Open Postman
2. Click **Import** button
3. Select `Stock_Research_Chatbot.postman_collection.json`
4. Collection will appear in your workspace

### 2. Import Environment

1. Click the **Environments** icon (⚙️)
2. Click **Import**
3. Select `Stock_Research_Chatbot.postman_environment.json`
4. Select "Stock Research Chatbot - Local" as active environment

### 3. Verify Backend is Running

Before testing, ensure the backend is running:

```bash
# Using Docker
docker-compose up

# Or locally
cd backend
uvicorn backend.app.main:app --reload
```

Verify at: http://localhost:8000/docs

---

## 🎯 Test Scenarios

### Test 1: Health Check ✅

**Purpose:** Verify backend is running and healthy

**Request:**
```
GET http://localhost:8000/api/v1/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-24T10:30:00Z",
  "service": "stock-research-chatbot"
}
```

**Tests:**
- ✅ Status code is 200
- ✅ Service status is "healthy"

---

### Test 2: Simple Analysis (No Typos) ✅

**Purpose:** Test normal analysis flow without typos

**Request:**
```json
POST /analyze
{
  "query": "Analyze AAPL for 1 month"
}
```

**Expected Response:**
```json
{
  "request_id": "uuid",
  "query": "Analyze AAPL for 1 month",
  "success": true,
  "needs_confirmation": false,
  "insights": [
    {
      "ticker": "AAPL",
      "company_name": "Apple Inc.",
      "stance": "buy",
      "confidence": "high",
      ...
    }
  ],
  "tickers_analyzed": ["AAPL"]
}
```

**Tests:**
- ✅ Status code is 200
- ✅ success is true
- ✅ insights array is not empty
- ✅ needs_confirmation is false

---

### Test 3: Single Typo Detection 🔍

**Purpose:** Test smart correction with single typo

**Request:**
```json
POST /analyze
{
  "query": "Analyze matae for 1 month"
}
```

**Expected Response:**
```json
{
  "request_id": "uuid",
  "query": "Analyze matae for 1 month",
  "success": false,
  "needs_confirmation": true,
  "confirmation_prompt": {
    "type": "confirmation",
    "message": "Did you mean **Meta Platforms Inc.** (META)?",
    "suggestion": {
      "original_input": "matae",
      "corrected_name": "Meta Platforms Inc.",
      "ticker": "META",
      "confidence": "high",
      "explanation": "Detected likely misspelling of Meta"
    },
    "conversation_id": "uuid-123"
  }
}
```

**Tests:**
- ✅ Status code is 200
- ✅ needs_confirmation is true
- ✅ suggestion.ticker is "META"
- ✅ conversation_id is saved to environment

**Note:** The `conversation_id` is automatically saved to the environment variable `CONVERSATION_ID` by the test script.

---

### Test 4: Confirm Single Correction ✅

**Purpose:** Confirm the correction and proceed with analysis

**Request:**
```json
POST /analyze
{
  "query": "Analyze matae for 1 month",
  "conversation_id": "{{CONVERSATION_ID}}",
  "confirmation_response": "Yes"
}
```

**Expected Response:**
```json
{
  "request_id": "uuid",
  "query": "Analyze matae for 1 month",
  "success": true,
  "needs_confirmation": false,
  "insights": [
    {
      "ticker": "META",
      ...
    }
  ],
  "tickers_analyzed": ["META"]
}
```

**Tests:**
- ✅ Status code is 200
- ✅ success is true
- ✅ tickers_analyzed includes "META"

---

### Test 5: Multiple Typos Detection 🔍🔍

**Purpose:** Test smart correction with multiple typos

**Request:**
```json
POST /analyze
{
  "query": "Analyze metae Apple and TSLAA"
}
```

**Expected Response (First Confirmation):**
```json
{
  "request_id": "uuid",
  "success": false,
  "needs_confirmation": true,
  "confirmation_prompt": {
    "type": "confirmation",
    "message": "I found 2 potential misspellings. Let's confirm them one by one.\n\nDid you mean **Meta Platforms Inc.** (META)?",
    "suggestion": {
      "original_input": "metae",
      "corrected_name": "Meta Platforms Inc.",
      "ticker": "META",
      "confidence": "high"
    },
    "conversation_id": "uuid-456"
  }
}
```

**Tests:**
- ✅ Status code is 200
- ✅ needs_confirmation is true
- ✅ First suggestion is META
- ✅ conversation_id is saved to `MULTI_CONVERSATION_ID`

---

### Test 6: Confirm First of Multiple ✅

**Purpose:** Confirm first correction, expect second confirmation

**Request:**
```json
POST /analyze
{
  "query": "Analyze metae Apple and TSLAA",
  "conversation_id": "{{MULTI_CONVERSATION_ID}}",
  "confirmation_response": "Yes"
}
```

**Expected Response (Second Confirmation):**
```json
{
  "request_id": "uuid",
  "success": false,
  "needs_confirmation": true,
  "confirmation_prompt": {
    "type": "confirmation",
    "message": "Did you mean **Tesla Inc.** (TSLA)?",
    "suggestion": {
      "original_input": "TSLAA",
      "corrected_name": "Tesla Inc.",
      "ticker": "TSLA",
      "confidence": "high"
    },
    "conversation_id": "uuid-456"
  }
}
```

**Tests:**
- ✅ Status code is 200
- ✅ needs_confirmation is true
- ✅ Second suggestion is TSLA

---

### Test 7: Confirm Second of Multiple ✅✅

**Purpose:** Confirm second correction, proceed with full analysis

**Request:**
```json
POST /analyze
{
  "query": "Analyze metae Apple and TSLAA",
  "conversation_id": "{{MULTI_CONVERSATION_ID}}",
  "confirmation_response": "Yes"
}
```

**Expected Response:**
```json
{
  "request_id": "uuid",
  "success": true,
  "needs_confirmation": false,
  "insights": [
    { "ticker": "META", ... },
    { "ticker": "AAPL", ... },
    { "ticker": "TSLA", ... }
  ],
  "tickers_analyzed": ["META", "AAPL", "TSLA"]
}
```

**Tests:**
- ✅ Status code is 200
- ✅ success is true
- ✅ All three tickers analyzed (META, AAPL, TSLA)

---

### Test 8: Reject Correction ❌

**Purpose:** Test rejection flow

**Request:**
```json
POST /analyze
{
  "query": "Analyze matae for 1 month",
  "conversation_id": "{{CONVERSATION_ID}}",
  "confirmation_response": "No"
}
```

**Expected Response:**
```json
{
  "request_id": "uuid",
  "success": false,
  "needs_confirmation": true,
  "confirmation_prompt": {
    "type": "clarification",
    "message": "Got it. Which company or ticker would you like to analyze?",
    "conversation_id": "uuid-123"
  }
}
```

**Tests:**
- ✅ Status code is 200
- ✅ needs_confirmation is true
- ✅ type is "clarification"

---

### Test 9: Complex Query with Multiple Companies 📊

**Purpose:** Test multi-company analysis without typos

**Request:**
```json
POST /analyze
{
  "query": "Compare AAPL, MSFT, and GOOGL for AI datacenter demand"
}
```

**Expected Response:**
```json
{
  "request_id": "uuid",
  "success": true,
  "insights": [
    { "ticker": "AAPL", ... },
    { "ticker": "MSFT", ... },
    { "ticker": "GOOGL", ... }
  ],
  "tickers_analyzed": ["AAPL", "MSFT", "GOOGL"]
}
```

**Tests:**
- ✅ Status code is 200
- ✅ success is true
- ✅ Multiple tickers analyzed

---

### Test 10: Phonetic Typo 🔤

**Purpose:** Test phonetic similarity detection

**Request:**
```json
POST /analyze
{
  "query": "Analyze microsft for 1 month"
}
```

**Expected Response:**
```json
{
  "request_id": "uuid",
  "success": false,
  "needs_confirmation": true,
  "confirmation_prompt": {
    "suggestion": {
      "ticker": "MSFT",
      "corrected_name": "Microsoft Corporation"
    }
  }
}
```

**Tests:**
- ✅ Status code is 200
- ✅ needs_confirmation is true
- ✅ Suggestion is MSFT

---

## 🔄 Complete Test Flow

### Scenario: Multiple Typos End-to-End

1. **Send initial query with typos**
   ```
   POST /analyze
   Body: {"query": "Analyze metae Apple and TSLAA"}
   ```

2. **Receive first confirmation**
   ```
   Response: "Did you mean Meta (META)?"
   Save conversation_id
   ```

3. **Confirm first correction**
   ```
   POST /analyze
   Body: {
     "query": "Analyze metae Apple and TSLAA",
     "conversation_id": "<saved-id>",
     "confirmation_response": "Yes"
   }
   ```

4. **Receive second confirmation**
   ```
   Response: "Did you mean Tesla (TSLA)?"
   ```

5. **Confirm second correction**
   ```
   POST /analyze
   Body: {
     "query": "Analyze metae Apple and TSLAA",
     "conversation_id": "<saved-id>",
     "confirmation_response": "Yes"
   }
   ```

6. **Receive final analysis**
   ```
   Response: Full analysis for META, AAPL, TSLA
   ```

---

## 🎨 Using Postman Test Scripts

The collection includes automated test scripts. To view results:

1. Run a request
2. Click the **Test Results** tab
3. See which tests passed/failed

### Example Test Script

```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Confirmation needed", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.needs_confirmation).to.eql(true);
});

// Save conversation_id for next request
var jsonData = pm.response.json();
if (jsonData.confirmation_prompt) {
    pm.environment.set("CONVERSATION_ID", jsonData.confirmation_prompt.conversation_id);
}
```

---

## 🚀 Running Collection with Newman

### Install Newman
```bash
npm install -g newman
```

### Run Collection
```bash
newman run Stock_Research_Chatbot.postman_collection.json \
  -e Stock_Research_Chatbot.postman_environment.json
```

### Generate HTML Report
```bash
newman run Stock_Research_Chatbot.postman_collection.json \
  -e Stock_Research_Chatbot.postman_environment.json \
  -r html
```

---

## 📊 Expected Results Summary

| Test | Expected Result | Status |
|------|----------------|--------|
| Health Check | Service healthy | ✅ |
| Simple Analysis | Direct analysis | ✅ |
| Single Typo | Confirmation prompt | ✅ |
| Confirm Single | Analysis proceeds | ✅ |
| Multiple Typos | First confirmation | ✅ |
| Confirm First | Second confirmation | ✅ |
| Confirm Second | Full analysis | ✅ |
| Reject Correction | Clarification prompt | ✅ |
| Complex Query | Multi-ticker analysis | ✅ |
| Phonetic Typo | Correct detection | ✅ |

---

## 🐛 Troubleshooting

### Issue: Connection Refused
**Solution:** Ensure backend is running on port 8000
```bash
curl http://localhost:8000/api/v1/health
```

### Issue: Conversation ID Not Found
**Solution:** Conversations expire after 30 minutes. Start a new test sequence.

### Issue: Smart Correction Not Working
**Solution:** Check GEMINI_API_KEY is set
```bash
docker-compose logs backend | grep GEMINI
```

### Issue: Tests Failing
**Solution:** 
1. Check backend logs for errors
2. Verify environment variables are set
3. Ensure Gemini API quota is not exceeded

---

## 📝 Notes

- **Conversation Timeout:** 30 minutes
- **Rate Limiting:** Not implemented in development
- **Concurrent Requests:** Supported
- **Environment Variables:** Automatically managed by test scripts

---

## 🎯 Best Practices

1. **Run tests in order** - Some tests depend on previous results
2. **Check test results** - Review the Test Results tab after each request
3. **Monitor backend logs** - Use `docker-compose logs -f backend`
4. **Clear environment** - Reset CONVERSATION_ID between test runs
5. **Use Newman** - Automate testing in CI/CD pipelines

---

**Version:** 2.1.0  
**Last Updated:** October 24, 2025  
**Status:** ✅ Production Ready

