#!/usr/bin/env python3
"""
Developer Agent — Generates full-stack code (React + FastAPI + MongoDB).
"""

import json
from typing import Dict, Any
from rrremergen.output import json_object, unfence


class Developer:
    """Generates application code."""

    def __init__(self, router):
        self.router = router

    async def generate_code(self, blueprint, ui_specs: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate full-stack code.

        Returns:
            {'frontend': '...', 'backend': '...', 'database': '...'}
        """
        # Generate frontend (React/Next.js)
        frontend_code = await self._generate_frontend(blueprint, ui_specs)

        # Generate backend (FastAPI)
        backend_code = await self._generate_backend(blueprint)

        # Generate database schema
        database_schema = await self._generate_database(blueprint)

        return {
            'frontend': frontend_code,
            'backend': backend_code,
            'database': database_schema,
        }

    async def _generate_frontend(self, blueprint, ui_specs: Dict[str, Any]) -> str:
        """Generate React/Next.js frontend code."""
        prompt = f"""
Generate React component code for: {blueprint.title}

Components needed: {', '.join(blueprint.ui_components)}

Design specs:
- Primary color: {ui_specs.get('color_palette', {}).get('primary', '#00d4ff')}
- Font: {ui_specs.get('typography', {}).get('body_font', 'System fonts')}

Generate clean, modern React code with:
1. Component structure
2. Styled components or Tailwind CSS
3. State management hooks
4. Props typing
5. Responsive design

Return only JSX/JavaScript code.
"""

        token_limit = 3000
        if self.router.mode == 'local':
            prompt = ('Return only complete compact React JSX, no markdown. Import React hooks. '
                'Export default component ' + blueprint.ui_components[0] + '. App: ' + blueprint.title + '. '
                'Requirements: ' + json.dumps(blueprint.requirements) + '. Limit to 35 lines; implement working state and controls.')
            token_limit = 450
        response = await self.router.complete(
            prompt=prompt,
            model=self.router.select_model('code_generation'),
            temperature=0.7,
            max_tokens=token_limit
        )

        return unfence(response['text'])

    async def _generate_backend(self, blueprint) -> str:
        """Generate FastAPI backend code."""
        prompt = f"""
Generate FastAPI Python code for: {blueprint.title}

API routes needed:
{json.dumps(blueprint.api_routes[:5], indent=2)}

Data models:
{json.dumps(blueprint.data_models[:3], indent=2)}

Generate:
1. FastAPI app setup
2. Pydantic models for data validation
3. Route handlers with proper error handling
4. Authentication (JWT)
5. CORS configuration

Return only Python code.
"""

        token_limit = 3000
        if self.router.mode == 'local':
            prompt = ('Return ONLY complete compact FastAPI Python source, no markdown. Import dependencies; app=FastAPI(). '
                'Use in-memory data and Pydantic models, include try/except error handling. '
                'Routes: ' + json.dumps(blueprint.api_routes) + '. Models: ' + json.dumps(blueprint.data_models) + '. Limit to 40 lines.')
            token_limit = 450
        response = await self.router.complete(
            prompt=prompt,
            model=self.router.select_model('code_generation'),
            temperature=0.7,
            max_tokens=token_limit
        )

        return unfence(response['text'])

    async def _generate_database(self, blueprint) -> str:
        """Generate MongoDB schema/initialization code."""
        prompt = f"""
Generate MongoDB schema and initialization code for: {blueprint.title}

Data models needed:
{json.dumps(blueprint.data_models, indent=2)}

Generate:
1. MongoDB collection schemas (JSON Schema validation)
2. Indexes for performance
3. Initialization script
4. Relationships between collections

Return only Python for MongoDB, without markdown fences.
"""

        token_limit = 1500
        if self.router.mode == 'local':
            prompt = ('Return ONLY a Python SCHEMA dictionary with field types for these models: '
                + json.dumps(blueprint.data_models) + '. No markdown, no prose, maximum 8 lines.')
            token_limit = 140
        response = await self.router.complete(
            prompt=prompt,
            model=self.router.select_model('code_generation'),
            temperature=0.7,
            max_tokens=token_limit
        )

        return unfence(response['text'])

    async def fix_issues(self, code: Dict[str, str], issues: list) -> Dict[str, str]:
        """Fix issues identified during validation."""
        response = await self.router.complete(
            prompt='Repair this application. Return one JSON object with frontend, backend, database as complete source strings. '
                   'Database must be Python. No explanations.\nIssues: ' + json.dumps(issues) + '\nCode: ' + json.dumps(code),
            model=self.router.select_model('code_generation'), temperature=0.2, max_tokens=1000)
        fixed = json_object(response['text'])
        if any(not isinstance(fixed.get(key), str) or not fixed[key].strip() for key in ('frontend', 'backend', 'database')):
            raise ValueError('Riparazione incompleta')
        return {key: unfence(fixed[key]) for key in ('frontend', 'backend', 'database')}
