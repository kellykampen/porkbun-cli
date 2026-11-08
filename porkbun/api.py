import os
import json
import httpx
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
import time
from functools import wraps

from porkbun.utils.exceptions import PorkbunAPIError, ConfigError
from porkbun.utils.logging import logger, log_api_request
from porkbun.utils.config import ConfigManager
from porkbun.utils.cache import cache_manager
from porkbun.utils.exceptions import APIError, RateLimitError

config_manager = ConfigManager()
config_manager.load()

def load_config() -> Dict[str, str]:
    """Load API configuration from file."""
    config_file = Path.home() / '.porkbun' / 'config.json'
    
    if not config_file.exists():
        logger.error(f"Config file not found: {config_file}")
        raise ConfigError("API configuration not found. Please run 'porkbun config init' first.")
    
    try:
        with open(config_file) as f:
            config = json.load(f)
            
        required_keys = ['apikey', 'secretapikey']
        if not all(key in config for key in required_keys):
            logger.error("Missing required keys in config file")
            raise ConfigError("Invalid configuration. Please run 'porkbun config init' to set up your API keys.")
            
        return config
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse config file: {e}")
        raise ConfigError(f"Invalid configuration file format: {e}")
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise ConfigError(f"Failed to load configuration: {e}")

def rate_limit(calls: int = 10, period: int = 60):
    """Rate limiting decorator."""
    def decorator(func):
        last_reset = time.time()
        calls_made = 0
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal last_reset, calls_made
            
            current_time = time.time()
            if current_time - last_reset >= period:
                calls_made = 0
                last_reset = current_time
                
            if calls_made >= calls:
                wait_time = period - (current_time - last_reset)
                if wait_time > 0:
                    logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
                    calls_made = 0
                    last_reset = time.time()
                    
            calls_made += 1
            return await func(*args, **kwargs)
            
        return wrapper
    return decorator

class APIClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
        
    @rate_limit()
    async def request(self, endpoint: str, data: Dict[str, Any] = None,
                     method: str = 'POST', use_cache: bool = True) -> Dict[str, Any]:
        """Make an async API request."""
        try:
            profile = config_manager.get_profile()
            base_url = profile.base_url.rstrip('/')
            url = f"{base_url}/{endpoint}"
            
            # Check cache for GET requests
            if method == 'GET' and use_cache:
                cached = cache_manager.get_api_response(endpoint, data or {})
                if cached:
                    return cached
                    
            # Prepare request data
            request_data = {
                'secretapikey': profile.secret_key,
                'apikey': profile.api_key
            }
            
            # Add any additional data
            if data:
                request_data.update(data)
            
            # Never log credentials, prefixes, or request payloads. Library callers
            # can use Loguru's default DEBUG sink without running setup_logging().
            logger.debug(f"Making API request to {url}")
            
            # Make request
            response = await self.client.request(
                method=method,
                url=url,
                json=request_data
            )
            
            # Handle response
            if response.status_code == 429:
                raise RateLimitError("API rate limit exceeded")
                
            response.raise_for_status()
            result = response.json()
            
            # Check for API error status
            status = result.get('status')
            if status and status.upper() != 'SUCCESS':
                message = result.get('message', 'Unknown error')
                raise APIError(f"{message}")
            
            # Cache successful GET responses
            if method == 'GET' and use_cache:
                cache_manager.set_api_response(endpoint, data or {}, result)
                
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            
            # Handle 403 Forbidden errors with specific guidance
            if e.response.status_code == 403:
                error_message = (
                    f"Access Forbidden (403). This could be due to:\n"
                    f"1. Invalid API keys - verify your API keys are correct\n"
                    f"2. IP restriction - your current IP address may not be allowed in the Porkbun API settings\n"
                    f"3. API access not enabled - make sure API access is enabled in your Porkbun account\n"
                    f"4. Using an outdated API version - the V3 Beta API might require updated credentials\n\n"
                    f"Please check your credentials and account settings at https://porkbun.com/account/api"
                )
                raise APIError(error_message)
            
            # Check for specific error message about domain not opted in to API access
            error_text = e.response.text.lower()
            if "domain is not opted in to api access" in error_text:
                # Extract domain from URL path
                domain = url.split('/')[-1]
                error_message = (
                    f"Domain {domain} is not opted in to API access.\n\n"
                    f"To fix this issue:\n"
                    f"1. Log in to your Porkbun dashboard at https://porkbun.com/account/login\n"
                    f"2. Navigate to the domain management page for {domain}\n"
                    f"3. Look for the 'API Access' option and enable it\n"
                    f"4. Try this command again after enabling API access"
                )
                raise APIError(error_message)
            raise APIError(f"API request failed: {e}")
        except Exception as e:
            logger.error(f"API error: {e}")
            raise APIError(f"API request failed: {e}")
            
    async def bulk_request(self, requests: List[Dict[str, Any]],
                          parallel: int = 3) -> List[Dict[str, Any]]:
        """Execute multiple API requests in parallel."""
        semaphore = asyncio.Semaphore(parallel)
        
        async def bounded_request(req: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                return await self.request(**req)
                
        return await asyncio.gather(
            *(bounded_request(req) for req in requests),
            return_exceptions=True
        )

async def make_request(endpoint: str, data: Dict[str, Any] = None,
                      method: str = 'POST', use_cache: bool = True) -> Dict[str, Any]:
    """Helper function for making a single API request."""
    async with APIClient() as client:
        return await client.request(endpoint, data, method, use_cache)

async def make_bulk_requests(requests: List[Dict[str, Any]],
                           parallel: int = 3) -> List[Dict[str, Any]]:
    """Helper function for making multiple API requests."""
    async with APIClient() as client:
        return await client.bulk_request(requests, parallel)
