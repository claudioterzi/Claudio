#!/usr/bin/env python3
"""
RRREMERGEN Orchestrator — Coordinates multi-agent app composition.

Pipeline: Architect → Designer → Developer → Integrator → PM (with validation loop)
"""

import json
import asyncio
from dataclasses import dataclass, asdict
from typing import Dict, Any, AsyncGenerator
from datetime import datetime

from agents.architect import Architect
from agents.designer import Designer
from agents.developer import Developer
from agents.integrator import Integrator
from agents.pm import PM
from router import LLMRouter, ModelAssignment


@dataclass
class AppBlueprint:
    """Generated application blueprint."""
    id: str
    title: str
    description: str
    requirements: list
    data_models: list
    api_routes: list
    ui_components: list
    integrations: list
    tech_stack: Dict[str, str]


@dataclass
class CompositionContext:
    """Shared context across agents."""
    original_prompt: str
    blueprint: AppBlueprint = None
    ui_specs: Dict[str, Any] = None
    code: Dict[str, str] = None  # {frontend, backend, database}
    integration_config: Dict[str, Any] = None
    validation_results: Dict[str, Any] = None
    deployment_urls: Dict[str, str] = None


class RRRemeRgenOrchestrator:
    """Orchestrates multi-agent app composition."""

    def __init__(self, router: LLMRouter):
        self.router = router
        self.architect = Architect(router)
        self.designer = Designer(router)
        self.developer = Developer(router)
        self.integrator = Integrator(router)
        self.pm = PM(router)

    async def compose_app(self, user_prompt: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Compose an application from natural language description.

        Yields:
            - stage_progress events
            - completion event with final app details
        """
        ctx = CompositionContext(original_prompt=user_prompt)
        app_id = f"APP-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        try:
            # Stage 1: Architect analyzes requirements and creates blueprint
            yield {'type': 'stage_progress', 'stage': 'architect'}
            ctx.blueprint = await self.architect.analyze(user_prompt, app_id)
            yield {
                'type': 'stage_output',
                'stage': 'architect',
                'data': asdict(ctx.blueprint)
            }

            # Stage 2: Designer creates UI/UX specifications
            yield {'type': 'stage_progress', 'stage': 'designer'}
            ctx.ui_specs = await self.designer.design(ctx.blueprint)
            yield {
                'type': 'stage_output',
                'stage': 'designer',
                'data': ctx.ui_specs
            }

            # Stage 3: Developer generates full-stack code
            yield {'type': 'stage_progress', 'stage': 'developer'}
            ctx.code = await self.developer.generate_code(ctx.blueprint, ctx.ui_specs)
            yield {
                'type': 'stage_output',
                'stage': 'developer',
                'summary': f"Generated {sum(len(c) for c in ctx.code.values())} lines of code"
            }

            # Stage 4: Integrator sets up third-party services
            yield {'type': 'stage_progress', 'stage': 'integrator'}
            ctx.integration_config = await self.integrator.setup_integrations(ctx.blueprint)
            yield {
                'type': 'stage_output',
                'stage': 'integrator',
                'data': ctx.integration_config
            }

            # Stage 5: PM validates and runs self-debugging loop
            yield {'type': 'stage_progress', 'stage': 'pm'}
            ctx.validation_results = await self.pm.validate_and_debug(
                ctx.blueprint,
                ctx.code,
                ctx.ui_specs,
                user_prompt
            )

            if ctx.validation_results.get('issues'):
                # Run self-debugging iterations
                for iteration in range(1, 4):  # Max 3 iterations
                    yield {
                        'type': 'debug_iteration',
                        'iteration': iteration,
                        'issues': ctx.validation_results['issues'][:3]  # Top 3 issues
                    }

                    # Developer fixes issues
                    ctx.code = await self.developer.fix_issues(
                        ctx.code,
                        ctx.validation_results['issues']
                    )

                    # Re-validate
                    ctx.validation_results = await self.pm.validate_and_debug(
                        ctx.blueprint,
                        ctx.code,
                        ctx.ui_specs,
                        user_prompt
                    )

                    if not ctx.validation_results.get('issues'):
                        break

            # Stage 6: Deploy and push to GitHub
            yield {'type': 'stage_progress', 'stage': 'deploy'}
            ctx.deployment_urls = await self._deploy_app(app_id, ctx)

            # Final completion event
            yield {
                'type': 'completion',
                'app': {
                    'id': app_id,
                    'title': ctx.blueprint.title,
                    'description': ctx.blueprint.description,
                    'github_url': ctx.deployment_urls.get('github'),
                    'vercel_url': ctx.deployment_urls.get('vercel'),
                    'code_preview': self._generate_code_preview(ctx.code),
                }
            }

        except Exception as e:
            yield {
                'type': 'error',
                'message': str(e),
                'stage': getattr(self, '_current_stage', 'unknown')
            }
            raise

    async def _deploy_app(self, app_id: str, ctx: CompositionContext) -> Dict[str, str]:
        """Deploy generated app to Vercel and push code to GitHub."""
        # TODO: Implement GitHub push and Vercel deployment
        # For now, return placeholder URLs
        return {
            'github': f'https://github.com/claudio-ai/{app_id}',
            'vercel': f'https://{app_id}.vercel.app',
        }

    def _generate_code_preview(self, code: Dict[str, str]) -> str:
        """Generate a code preview for the frontend component."""
        frontend = code.get('frontend', '// Frontend code\n')
        lines = frontend.split('\n')[:20]  # First 20 lines
        return '\n'.join(lines) + '\n...'


class ModelAssignmentStrategy:
    """Intelligently assigns models to each agent based on task."""

    @staticmethod
    def get_architect_model(router: LLMRouter) -> str:
        """Best model for analyzing requirements: Claude (long context, reasoning)."""
        return router.select_model(
            task_type='analysis',
            required_context_length=8000,
            preferred_model='claude-3.5-sonnet'
        )

    @staticmethod
    def get_designer_model(router: LLMRouter) -> str:
        """Best model for UI/UX: Gemini (vision + design sense)."""
        return router.select_model(
            task_type='design',
            required_context_length=4000,
            preferred_model='gemini-2.5-pro'
        )

    @staticmethod
    def get_developer_model(router: LLMRouter) -> str:
        """Best model for code generation: GPT-4 (best for coding)."""
        return router.select_model(
            task_type='code_generation',
            required_context_length=16000,
            preferred_model='gpt-4-turbo'
        )

    @staticmethod
    def get_integrator_model(router: LLMRouter) -> str:
        """Best model for API integration: Claude (structured, reliable)."""
        return router.select_model(
            task_type='integration',
            required_context_length=4000,
            preferred_model='claude-3.5-sonnet'
        )

    @staticmethod
    def get_pm_model(router: LLMRouter) -> str:
        """Best model for validation: Claude (critical thinking, debugging)."""
        return router.select_model(
            task_type='validation',
            required_context_length=8000,
            preferred_model='claude-3.5-sonnet'
        )
