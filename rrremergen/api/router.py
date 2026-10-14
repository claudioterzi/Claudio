#!/usr/bin/env python3
"""
LLM Router — Intelligently selects and routes requests to best-available LLM.

Integration with Claudio's multi-provider LLM router.
Supports: Anthropic Claude, OpenAI GPT, Google Gemini, DeepSeek, Mistral
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import os


@dataclass
class ModelAssignment:
    """Represents a model assignment for a specific task."""
    provider: str
    model: str
    reasoning: str


class LLMRouter:
    """Routes LLM requests to best-available provider."""

    def __init__(self):
        self.providers = {
            'anthropic': {
                'models': ['claude-3.5-sonnet', 'claude-3-opus', 'claude-3-haiku'],
                'api_key_env': 'ANTHROPIC_API_KEY',
                'priority': 1,  # Highest priority
            },
            'openai': {
                'models': ['gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo'],
                'api_key_env': 'OPENAI_API_KEY',
                'priority': 2,
            },
            'google': {
                'models': ['gemini-2.5-pro', 'gemini-1.5-pro', 'gemini-1.5-flash'],
                'api_key_env': 'GOOGLE_API_KEY',
                'priority': 3,
            },
            'deepseek': {
                'models': ['deepseek-chat', 'deepseek-coder'],
                'api_key_env': 'DEEPSEEK_API_KEY',
                'priority': 4,
            },
            'mistral': {
                'models': ['mistral-large', 'mistral-medium', 'mistral-small'],
                'api_key_env': 'MISTRAL_API_KEY',
                'priority': 5,
            },
        }

        self.circuit_breaker = {}
        self.response_cache = {}

    def select_model(
        self,
        task_type: str = 'general',
        required_context_length: int = 4000,
        preferred_model: Optional[str] = None,
    ) -> str:
        """
        Select best LLM for the task.

        Args:
            task_type: Type of task (analysis, code_generation, design, etc.)
            required_context_length: Minimum context window needed
            preferred_model: Preferred model if available

        Returns:
            Selected model identifier
        """
        # If preferred model is available and healthy, use it
        if preferred_model and self._is_model_healthy(preferred_model):
            return preferred_model

        # Fallback: select based on task type
        assignments = self._get_task_assignments()
        if task_type in assignments:
            return assignments[task_type]['model']

        # Ultimate fallback: first healthy model
        for provider, config in sorted(
            self.providers.items(),
            key=lambda x: x[1]['priority']
        ):
            if self._is_provider_healthy(provider):
                return config['models'][0]

        # Absolute fallback
        return 'claude-3.5-sonnet'

    def _is_model_healthy(self, model: str) -> bool:
        """Check if a model is healthy (not in circuit breaker)."""
        return model not in self.circuit_breaker or not self.circuit_breaker[model]['active']

    def _is_provider_healthy(self, provider: str) -> bool:
        """Check if a provider has valid API key and is reachable."""
        api_key_env = self.providers[provider]['api_key_env']
        return os.getenv(api_key_env) is not None

    def _get_task_assignments(self) -> Dict[str, Dict]:
        """
        Get optimal model assignments for different task types.

        Returns:
            Dictionary mapping task types to model assignments
        """
        return {
            'analysis': {
                'provider': 'anthropic',
                'model': 'claude-3.5-sonnet',
                'reasoning': 'Claude excels at analysis with strong reasoning'
            },
            'design': {
                'provider': 'google',
                'model': 'gemini-2.5-pro',
                'reasoning': 'Gemini has strong visual and design sense'
            },
            'code_generation': {
                'provider': 'openai',
                'model': 'gpt-4-turbo',
                'reasoning': 'GPT-4 is best for code generation and quality'
            },
            'integration': {
                'provider': 'anthropic',
                'model': 'claude-3.5-sonnet',
                'reasoning': 'Claude for structured, reliable outputs'
            },
            'validation': {
                'provider': 'anthropic',
                'model': 'claude-3.5-sonnet',
                'reasoning': 'Claude for critical thinking and debugging'
            },
            'general': {
                'provider': 'anthropic',
                'model': 'claude-3.5-sonnet',
                'reasoning': 'Balanced capability across tasks'
            },
        }

    async def complete(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> Dict[str, str]:
        """
        Get a completion from the specified model.

        Args:
            prompt: Input prompt
            model: Model identifier
            temperature: Temperature for response (0-1)
            max_tokens: Maximum tokens in response

        Returns:
            Dictionary with 'text' key containing the response
        """
        # Determine provider from model name
        provider = self._get_provider_for_model(model)

        if not provider:
            return {
                'text': f'// Placeholder response from {model}',
                'model': model,
                'tokens_used': 0,
            }

        # Route to appropriate provider
        if provider == 'anthropic':
            return await self._complete_anthropic(prompt, model, temperature, max_tokens)
        elif provider == 'openai':
            return await self._complete_openai(prompt, model, temperature, max_tokens)
        elif provider == 'google':
            return await self._complete_google(prompt, model, temperature, max_tokens)
        elif provider == 'deepseek':
            return await self._complete_deepseek(prompt, model, temperature, max_tokens)
        elif provider == 'mistral':
            return await self._complete_mistral(prompt, model, temperature, max_tokens)

        # Fallback
        return {
            'text': f'// Response from {model}',
            'model': model,
            'tokens_used': 0,
        }

    def _get_provider_for_model(self, model: str) -> str:
        """Determine provider from model identifier."""
        model_lower = model.lower()

        if 'claude' in model_lower or 'anthropic' in model_lower:
            return 'anthropic'
        elif 'gpt' in model_lower:
            return 'openai'
        elif 'gemini' in model_lower:
            return 'google'
        elif 'deepseek' in model_lower:
            return 'deepseek'
        elif 'mistral' in model_lower:
            return 'mistral'

        return None

    async def _complete_anthropic(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, str]:
        """Get completion from Anthropic Claude."""
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return {
                'text': response.content[0].text,
                'model': model,
                'tokens_used': response.usage.output_tokens,
            }
        except Exception as e:
            self.log_error(model, str(e))
            return {
                'text': f'// Error calling Anthropic: {str(e)}',
                'model': model,
                'tokens_used': 0,
            }

    async def _complete_openai(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, str]:
        """Get completion from OpenAI GPT."""
        try:
            import openai

            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            return {
                'text': response.choices[0].message.content,
                'model': model,
                'tokens_used': response.usage.completion_tokens,
            }
        except Exception as e:
            self.log_error(model, str(e))
            return {
                'text': f'// Error calling OpenAI: {str(e)}',
                'model': model,
                'tokens_used': 0,
            }

    async def _complete_google(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, str]:
        """Get completion from Google Gemini."""
        try:
            import google.generativeai as genai

            genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
            model_obj = genai.GenerativeModel(model)

            response = model_obj.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )
            )

            return {
                'text': response.text,
                'model': model,
                'tokens_used': 0,  # Google doesn't return token count easily
            }
        except Exception as e:
            self.log_error(model, str(e))
            return {
                'text': f'// Error calling Google Gemini: {str(e)}',
                'model': model,
                'tokens_used': 0,
            }

    async def _complete_deepseek(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, str]:
        """Get completion from DeepSeek."""
        try:
            import openai  # DeepSeek uses OpenAI SDK

            client = openai.OpenAI(
                api_key=os.getenv('DEEPSEEK_API_KEY'),
                base_url="https://api.deepseek.com"
            )

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            return {
                'text': response.choices[0].message.content,
                'model': model,
                'tokens_used': response.usage.completion_tokens,
            }
        except Exception as e:
            self.log_error(model, str(e))
            return {
                'text': f'// Error calling DeepSeek: {str(e)}',
                'model': model,
                'tokens_used': 0,
            }

    async def _complete_mistral(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, str]:
        """Get completion from Mistral."""
        try:
            from mistralai import Mistral

            client = Mistral(api_key=os.getenv('MISTRAL_API_KEY'))

            response = client.chat.complete(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            return {
                'text': response.choices[0].message.content,
                'model': model,
                'tokens_used': response.usage.completion_tokens,
            }
        except Exception as e:
            self.log_error(model, str(e))
            return {
                'text': f'// Error calling Mistral: {str(e)}',
                'model': model,
                'tokens_used': 0,
            }

    def log_error(self, model: str, error: str):
        """Log an error for a model and update circuit breaker."""
        if model not in self.circuit_breaker:
            self.circuit_breaker[model] = {'active': False, 'error_count': 0}

        self.circuit_breaker[model]['error_count'] += 1

        # Activate circuit breaker after 3 errors
        if self.circuit_breaker[model]['error_count'] >= 3:
            self.circuit_breaker[model]['active'] = True
