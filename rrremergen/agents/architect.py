#!/usr/bin/env python3
"""
Architect Agent — Analyzes requirements and creates app blueprints.
"""

import json
from typing import Dict, Any, List
from dataclasses import dataclass, field
from rrremergen.output import json_object


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
        'frontend': 'React',
        'backend': 'FastAPI',
        'database': 'schema_only',
        'auth': 'not_configured',
    })
    constraints: List[str] = field(default_factory=list)
    deployment_platform: str = 'Vercel'


class Architect:
    """Analyzes user prompts and generates app blueprints."""

    def __init__(self, router):
        self.router = router

    @staticmethod
    def _blueprint_from_text(text: str, app_id: str) -> AppBlueprint:
        """Validate generated JSON without inventing missing blueprint content."""
        analysis = json_object(text)
        for key in ('title', 'description'):
            if not isinstance(analysis.get(key), str) or not analysis[key].strip():
                raise ValueError(f'Blueprint privo di {key}')
        for key in ('requirements', 'ui_components', 'integrations', 'constraints'):
            if not isinstance(analysis.get(key, []), list) or any(not isinstance(x, str) for x in analysis.get(key, [])):
                raise ValueError(f'Blueprint: {key} deve essere una lista di stringhe')
        if not analysis.get('ui_components'):
            raise ValueError('Blueprint privo di componenti UI')
        for key in ('api_routes', 'data_models'):
            if not isinstance(analysis.get(key, []), list) or any(not isinstance(x, dict) for x in analysis.get(key, [])):
                raise ValueError(f'Blueprint: {key} deve essere una lista di oggetti')
        return AppBlueprint(
            id=app_id,
            title=analysis['title'],
            description=analysis['description'],
            requirements=analysis.get('requirements', []),
            data_models=analysis.get('data_models', []),
            api_routes=analysis.get('api_routes', []),
            ui_components=analysis.get('ui_components', []),
            integrations=analysis.get('integrations', []),
            constraints=analysis.get('constraints', []),
        )

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

        # Call LLM to analyze. Local structured output gets one bounded retry on
        # validation failure; the retry stays on the same local runner and never
        # substitutes defaults or falls back to a cloud provider.
        token_limit = 2000
        attempts = 1
        if self.router.mode == 'local':
            analysis_prompt = ('Architect agent. Return ONLY compact JSON with lowercase keys: '
                'title, description (strings), requirements, ui_components, integrations, constraints (string lists), '
                'data_models, api_routes (object lists). Routes use path and method. '
                'Each data_models item MUST be an object like {"model":"Task","fields":{"id":"integer"}}; '
                'each api_routes item MUST be an object like {"path":"/api/tasks","method":"GET"}. '
                'Use at most 3 requirements, 1 component, 1 model, 2 routes. No markdown. App request:\n' + user_prompt)
            token_limit = 350
            attempts = 2
        for attempt in range(attempts):
            prompt = analysis_prompt
            if attempt:
                prompt = ('Architect agent retry. The previous response failed strict schema validation. '
                    'Return ONLY one compact JSON object with exactly this shape: '
                    '{"title":"name","description":"summary","requirements":["item"],'
                    '"ui_components":["TaskList"],"integrations":[],"constraints":[],'
                    '"data_models":[{"model":"Task","fields":{"id":"integer"}}],'
                    '"api_routes":[{"path":"/api/tasks","method":"GET"}]}. '
                    'Every list item must have the shown JSON type. No markdown. App request:\n' + user_prompt)
            response = await self.router.complete(
                prompt=prompt,
                model=self.router.select_model('analysis'),
                temperature=0.7,
                max_tokens=token_limit
            )
            try:
                return self._blueprint_from_text(response['text'], app_id)
            except (TypeError, ValueError):
                if attempt + 1 == attempts:
                    raise
        raise AssertionError('unreachable')
