#!/usr/bin/env python3
"""
Architect Agent — Analyzes requirements and creates app blueprints.
"""

import json
from typing import Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class AppBlueprint:
    """Technical blueprint for an application."""
    id: str
    title: str
    description: str
    requirements: List[str] = field(default_factory=list)
    data_models: List[Dict[str, Any]] = field(default_factory=list)
    api_routes: List[Dict[str, str]] = field(default_factory=list)
    ui_components: List[str] = field(default_factory=list)
    integrations: List[str] = field(default_factory=list)
    tech_stack: Dict[str, str] = field(default_factory=lambda: {
        'frontend': 'React + Next.js',
        'backend': 'FastAPI',
        'database': 'MongoDB',
        'auth': 'JWT',
    })
    constraints: List[str] = field(default_factory=list)
    deployment_platform: str = 'Vercel'


class Architect:
    """Analyzes user prompts and generates app blueprints."""

    def __init__(self, router):
        self.router = router

    async def analyze(self, user_prompt: str, app_id: str) -> AppBlueprint:
        """
        Analyze user requirements and create technical blueprint.

        Args:
            user_prompt: Natural language description of the app
            app_id: Unique identifier for the application

        Returns:
            AppBlueprint with technical specifications
        """
        # Use Claude (Architect's preferred model) for analysis
        analysis_prompt = f"""
You are the Architect agent in RRREMERGEN (R³∞ web app composer).
Your role is to analyze user requirements and create a detailed technical blueprint.

User's Application Description:
{user_prompt}

Create a detailed blueprint including:

1. **Application Title**: A catchy, memorable name
2. **Core Description**: 2-3 sentences summarizing the app
3. **Key Requirements**: List of 5-10 functional requirements
4. **Data Models**: Schema design (entities, fields, relationships)
   Format: {{"model": "User", "fields": {{"id": "UUID", "email": "string", "name": "string"}}}}
5. **API Routes**: REST endpoints needed
   Format: {{"path": "/api/users", "method": "GET", "description": "Fetch all users"}}
6. **UI Components**: React components needed
   Format: ["UserProfile", "Dashboard", "Settings"]
7. **Third-party Integrations**: Services to integrate
   Format: ["Stripe", "SendGrid", "AWS S3"]
8. **Constraints**: Technical or business constraints
   Format: ["HIPAA compliance", "Real-time updates required", "Mobile-first design"]

Return valid JSON only, no markdown or explanations.
"""

        # Call LLM to analyze
        response = await self.router.complete(
            prompt=analysis_prompt,
            model='claude-3.5-sonnet',
            temperature=0.7,
            max_tokens=2000
        )

        # Parse response
        try:
            analysis = json.loads(response.get('text', '{}'))
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            analysis = self._parse_fallback_analysis(response.get('text', ''))

        # Build blueprint
        blueprint = AppBlueprint(
            id=app_id,
            title=analysis.get('title', 'Untitled App'),
            description=analysis.get('description', ''),
            requirements=analysis.get('requirements', []),
            data_models=analysis.get('data_models', []),
            api_routes=analysis.get('api_routes', []),
            ui_components=analysis.get('ui_components', []),
            integrations=analysis.get('integrations', []),
            constraints=analysis.get('constraints', []),
        )

        return blueprint

    def _parse_fallback_analysis(self, text: str) -> Dict[str, Any]:
        """Fallback parser if JSON fails."""
        return {
            'title': 'Generated Application',
            'description': 'Auto-composed application',
            'requirements': ['User authentication', 'Data persistence', 'Real-time updates'],
            'data_models': [{'model': 'User', 'fields': {}}],
            'api_routes': [],
            'ui_components': ['Dashboard', 'Settings'],
            'integrations': [],
            'constraints': [],
        }
