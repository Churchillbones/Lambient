# Security Audit Report - Hardcoded Endpoints & API Keys

## Audit Summary
**Date:** 2025-01-27  
**Scope:** All Python files in the project for hardcoded endpoints and API keys  
**Status:** ✅ Critical issues resolved

## Critical Issues Found & Fixed

### 🔴 CRITICAL: Government API Endpoint (FIXED)
**Files:** `src/utils/__init__.py`, `src/llm/embedding_service.py`  
**Issue:** VA government API endpoint hardcoded as default  
**Risk:** Unauthorized access to government systems  
**Fix:** Removed hardcoded endpoint, now requires `AZURE_EMBEDDING_ENDPOINT` environment variable

**Before:**
```python
endpoint = "https://va-east-apim.devtest.spd.vaec.va.gov/openai/deployments/text-embedding-3-large/embeddings"
```

**After:**
```python
endpoint = os.getenv("AZURE_EMBEDDING_ENDPOINT", "")
if not endpoint:
    logger.error("No embedding endpoint configured. Please set AZURE_EMBEDDING_ENDPOINT environment variable.")
    return None
```

### 🔴 CRITICAL: Production Azure Endpoint (FIXED)
**File:** `src/config/__init__.py`  
**Issue:** Production Azure endpoint hardcoded as fallback  
**Risk:** Unintended API calls to production systems  
**Fix:** Removed hardcoded endpoint, now requires environment variable

**Before:**
```python
"AZURE_ENDPOINT": os.getenv("AZURE_ENDPOINT", "https://spd-prod-openai-va-apim.azure-api.us/api")
```

**After:**
```python
"AZURE_ENDPOINT": os.getenv("AZURE_ENDPOINT", "")
```

## Development Endpoints (Lower Risk)
These localhost endpoints are acceptable for development but should be configurable:

- ✅ `http://localhost:8001/generate_note` - Properly configured via environment variables
- ✅ `http://localhost:11434/api/generate` - Ollama default, acceptable for local development
- ✅ `http://localhost:4200` - Frontend CORS, acceptable for development

## Environment Variables Required
After the security fixes, these environment variables are now **REQUIRED**:

```bash
# REQUIRED - No defaults provided
AZURE_API_KEY=your_azure_openai_api_key
AZURE_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_EMBEDDING_ENDPOINT=https://your-embedding-endpoint.azure.com/

# OPTIONAL - Have sensible defaults
LOCAL_MODEL_API_URL=http://localhost:8001/generate_note
MODEL_NAME=gpt-4o
DEBUG_MODE=False
```

## Security Best Practices Implemented

1. **No Hardcoded Production URLs:** All production endpoints require explicit configuration
2. **Environment Variable Validation:** Application will fail gracefully if required variables are missing
3. **Clear Error Messages:** Users receive helpful guidance when configuration is missing
4. **Updated Templates:** All setup scripts now generate secure `.env` templates

## Recommendations Going Forward

1. **Never commit `.env` files** - They are already in `.gitignore`
2. **Use different endpoints for dev/staging/production**
3. **Regularly audit for new hardcoded credentials**
4. **Consider using Azure Key Vault for production deployments**
5. **Implement configuration validation at startup**

## Files Modified
- `src/utils/__init__.py` - Removed hardcoded VA endpoint
- `src/llm/embedding_service.py` - Removed hardcoded VA endpoint, added env var support
- `src/config/__init__.py` - Removed hardcoded Azure production endpoint
- `setup.bat` - Updated .env template with new required variables

## Verification
Run the following to verify no hardcoded endpoints remain:
```bash
grep -r "https://.*\.gov" src/ --include="*.py"
grep -r "https://.*\.azure\.com" src/ --include="*.py" | grep -v "your-resource"
```

Both commands should return no results (except for comments/examples). 