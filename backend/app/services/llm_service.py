"""LLM service with multiple provider support"""
from typing import Optional, List, Dict, Any, AsyncGenerator
from enum import Enum
import httpx
import json
import logging
from datetime import datetime, timedelta
import redis.asyncio as redis
from app.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OLLAMA = "ollama"
    GROQ = "groq"
    CLAUDE = "claude"
    OPENROUTER = "openrouter"


class LLMService:
    """Service for interacting with multiple LLM providers"""
    
    def __init__(self):
        """Initialize LLM service"""
        self.redis_client: Optional[redis.Redis] = None
        self.token_counts: Dict[str, int] = {}
        self.rate_limits: Dict[str, List[datetime]] = {}
        
        # Provider configurations
        self.providers = {
            LLMProvider.OLLAMA: {
                "base_url": settings.OLLAMA_BASE_URL,
                "models": ["llama3.3", "qwen2.5:7b"],
                "default_model": "llama3.3",
                "rate_limit": None,  # No rate limit for local
            },
            LLMProvider.GROQ: {
                "base_url": "https://api.groq.com/openai/v1",
                "api_key": settings.GROQ_API_KEY,
                "models": ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"],
                "default_model": "llama-3.3-70b-versatile",
                "rate_limit": 30,  # requests per minute
            },
            LLMProvider.CLAUDE: {
                "base_url": "https://api.anthropic.com/v1",
                "api_key": settings.ANTHROPIC_API_KEY,
                "models": ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
                "default_model": "claude-3-5-sonnet-20241022",
                "rate_limit": 50,
            },
        }
    
    async def _get_redis(self) -> redis.Redis:
        """Get Redis client for caching"""
        if self.redis_client is None:
            self.redis_client = await redis.from_url(settings.REDIS_URL)
        return self.redis_client
    
    def _check_rate_limit(self, provider: LLMProvider) -> bool:
        """Check if rate limit allows request"""
        config = self.providers.get(provider)
        if not config or not config.get("rate_limit"):
            return True
        
        rate_limit = config["rate_limit"]
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old timestamps
        if provider.value in self.rate_limits:
            self.rate_limits[provider.value] = [
                ts for ts in self.rate_limits[provider.value]
                if ts > minute_ago
            ]
        else:
            self.rate_limits[provider.value] = []
        
        # Check limit
        if len(self.rate_limits[provider.value]) >= rate_limit:
            return False
        
        self.rate_limits[provider.value].append(now)
        return True
    
    async def _get_cached_response(self, cache_key: str) -> Optional[str]:
        """Get cached response"""
        try:
            redis_client = await self._get_redis()
            cached = await redis_client.get(cache_key)
            if cached:
                return cached.decode('utf-8')
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
        return None
    
    async def _set_cached_response(self, cache_key: str, response: str, ttl: int = 3600):
        """Set cached response"""
        try:
            redis_client = await self._get_redis()
            await redis_client.setex(cache_key, ttl, response)
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
    
    async def generate(
        self,
        prompt: str,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        use_cache: bool = True,
    ) -> str:
        """
        Generate text completion
        
        Args:
            prompt: User prompt
            provider: LLM provider (auto-select if None)
            model: Model name (use default if None)
            system_prompt: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            use_cache: Whether to use caching
            
        Returns:
            Generated text
        """
        # Check cache
        if use_cache:
            cache_key = f"llm:{provider}:{model}:{hash(prompt)}"
            cached = await self._get_cached_response(cache_key)
            if cached:
                logger.info(f"Cache hit for prompt")
                return cached
        
        # Auto-select provider if not specified
        if provider is None:
            provider = await self._select_provider()
        
        # Try primary provider
        try:
            response = await self._generate_with_provider(
                provider=provider,
                prompt=prompt,
                model=model,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Cache response
            if use_cache and response:
                await self._set_cached_response(cache_key, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error with {provider}: {e}")
            
            # Fallback to next provider
            fallback_provider = await self._get_fallback_provider(provider)
            if fallback_provider:
                logger.info(f"Falling back to {fallback_provider}")
                return await self._generate_with_provider(
                    provider=fallback_provider,
                    prompt=prompt,
                    model=model,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            
            raise Exception(f"All LLM providers failed: {e}")
    
    async def _select_provider(self) -> LLMProvider:
        """Auto-select best available provider"""
        # Prefer Ollama (local, free, fast)
        if settings.OLLAMA_BASE_URL:
            return LLMProvider.OLLAMA
        
        # Then Groq (fast, free tier)
        if settings.GROQ_API_KEY:
            return LLMProvider.GROQ
        
        # Then Claude (high quality)
        if settings.ANTHROPIC_API_KEY:
            return LLMProvider.CLAUDE
        
        return LLMProvider.OLLAMA  # Default
    
    async def _get_fallback_provider(self, failed_provider: LLMProvider) -> Optional[LLMProvider]:
        """Get fallback provider"""
        fallback_order = [
            LLMProvider.OLLAMA,
            LLMProvider.GROQ,
            LLMProvider.CLAUDE,
        ]
        
        # Remove failed provider and return next
        try:
            idx = fallback_order.index(failed_provider)
            for provider in fallback_order[idx + 1:]:
                config = self.providers.get(provider)
                if config and (not config.get("api_key") or config["api_key"]):
                    return provider
        except ValueError:
            pass
        
        return None
    
    async def _generate_with_provider(
        self,
        provider: LLMProvider,
        prompt: str,
        model: Optional[str],
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Generate with specific provider"""
        # Check rate limit
        if not self._check_rate_limit(provider):
            raise Exception(f"Rate limit exceeded for {provider}")
        
        config = self.providers[provider]
        model = model or config["default_model"]
        
        if provider == LLMProvider.OLLAMA:
            return await self._generate_ollama(prompt, model, system_prompt, temperature, max_tokens)
        elif provider == LLMProvider.GROQ:
            return await self._generate_openai_compatible(config, prompt, model, system_prompt, temperature, max_tokens)
        elif provider == LLMProvider.CLAUDE:
            return await self._generate_claude(config, prompt, model, system_prompt, temperature, max_tokens)
        
        raise Exception(f"Unsupported provider: {provider}")
    
    async def _generate_ollama(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Generate with Ollama"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "model": model,
                "prompt": prompt,
                "system": system_prompt,
                "temperature": temperature,
                "num_predict": max_tokens,
                "stream": False,
            }
            
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
    
    async def _generate_openai_compatible(
        self,
        config: Dict[str, Any],
        prompt: str,
        model: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Generate with OpenAI-compatible API (Groq)"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            headers = {
                "Authorization": f"Bearer {config['api_key']}",
                "Content-Type": "application/json",
            }
            
            response = await client.post(
                f"{config['base_url']}/chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
    
    async def _generate_claude(
        self,
        config: Dict[str, Any],
        prompt: str,
        model: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Generate with Claude"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            headers = {
                "x-api-key": config['api_key'],
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            }
            
            response = await client.post(
                f"{config['base_url']}/messages",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            result = response.json()
            return result["content"][0]["text"]
    
    async def stream_generate(
        self,
        prompt: str,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncGenerator[str, None]:
        """
        Generate text with streaming
        
        Yields:
            Text chunks
        """
        if provider is None:
            provider = await self._select_provider()
        
        config = self.providers[provider]
        model = model or config["default_model"]
        
        if provider == LLMProvider.OLLAMA:
            async for chunk in self._stream_ollama(prompt, model, system_prompt, temperature, max_tokens):
                yield chunk
        else:
            # For non-streaming providers, yield full response
            response = await self.generate(prompt, provider, model, system_prompt, temperature, max_tokens, use_cache=False)
            yield response


    async def _stream_ollama(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[str, None]:
        """Stream from Ollama"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload = {
                "model": model,
                "prompt": prompt,
                "system": system_prompt,
                "temperature": temperature,
                "num_predict": max_tokens,
                "stream": True,
            }
            
            async with client.stream(
                "POST",
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                        except json.JSONDecodeError:
                            continue


# Global instance
llm_service = LLMService()
