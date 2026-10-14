#!/usr/bin/env python3
"""
Developer Agent — Generates full-stack code (React + FastAPI + MongoDB).
"""

import json
from typing import Dict, Any


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

        response = await self.router.complete(
            prompt=prompt,
            model='gpt-4-turbo',
            temperature=0.7,
            max_tokens=3000
        )

        return response.get('text', '// Frontend code placeholder')

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

        response = await self.router.complete(
            prompt=prompt,
            model='gpt-4-turbo',
            temperature=0.7,
            max_tokens=3000
        )

        return response.get('text', '# Backend code placeholder')

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

Return only JavaScript/Python for MongoDB.
"""

        response = await self.router.complete(
            prompt=prompt,
            model='gpt-4-turbo',
            temperature=0.7,
            max_tokens=1500
        )

        return response.get('text', '// Database schema placeholder')

    async def fix_issues(self, code: Dict[str, str], issues: list) -> Dict[str, str]:
        """Fix issues identified during validation."""
        # Placeholder - would iterate through code fixing issues
        return code
