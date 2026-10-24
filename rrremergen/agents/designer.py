#!/usr/bin/env python3
"""
Designer Agent — Creates UI/UX specifications for applications.
"""

import json
from typing import Dict, Any
from rrremergen.output import json_object


class Designer:
    """Creates UI/UX specifications based on app blueprints."""

    def __init__(self, router):
        self.router = router

    async def design(self, blueprint) -> Dict[str, Any]:
        """
        Create UI/UX specifications based on technical blueprint.

        Args:
            blueprint: AppBlueprint from Architect

        Returns:
            UI/UX specifications including layout, colors, components
        """
        design_prompt = f"""
You are the Designer agent in RRREMERGEN (R³∞ web app composer).
Your role is to create detailed UI/UX specifications.

Application Blueprint:
- Title: {blueprint.title}
- Description: {blueprint.description}
- Components: {', '.join(blueprint.ui_components)}
- Requirements: {', '.join(blueprint.requirements[:5])}

Create comprehensive UI/UX specifications including:

1. **Color Palette**:
   Primary, secondary, accent, background, text colors (hex codes)

2. **Typography**:
   Heading font, body font, sizes (base, h1, h2, h3, body)

3. **Layout System**:
   Grid, spacing (unit), responsive breakpoints

4. **Component Specs**:
   For each UI component, specify:
   - Size (width/height constraints)
   - States (default, hover, active, disabled)
   - Typography styling
   - Spacing/padding

5. **Page Layouts**:
   Wireframes/descriptions of main pages

6. **Responsive Design**:
   Mobile (320px), tablet (768px), desktop (1024px) layouts

7. **Accessibility**:
   WCAG 2.1 compliance notes

8. **Animation/Transitions**:
   Micro-interactions and transitions

Return valid JSON with nested structure for easy component generation.
"""

        token_limit = 2500
        if self.router.mode == 'local':
            design_prompt = ('Designer agent. Return ONLY compact JSON: '
                '{"color_palette":{"primary":"hex","background":"hex"},"typography":{"body_font":"font"}}. '
                'Choose real colors and font for ' + blueprint.title + '. No markdown.')
            token_limit = 160
        response = await self.router.complete(
            prompt=design_prompt,
            model=self.router.select_model('design'),
            temperature=0.8,
            max_tokens=token_limit
        )

        ui_specs = json_object(response['text'])
        if not isinstance(ui_specs.get('color_palette'), dict) or not isinstance(ui_specs.get('typography'), dict):
            raise ValueError('Design privo di color_palette o typography')

        return ui_specs

    def _default_design_spec(self) -> Dict[str, Any]:
        """Default design specifications."""
        return {
            'color_palette': {
                'primary': '#00d4ff',
                'secondary': '#7c3aed',
                'accent': '#ff6b6b',
                'background': '#0a0e27',
                'surface': '#1a1f3a',
                'text': '#e0e0e0',
            },
            'typography': {
                'heading_font': 'Inter',
                'body_font': 'System fonts',
                'sizes': {
                    'h1': '2.5rem',
                    'h2': '2rem',
                    'h3': '1.5rem',
                    'body': '1rem',
                    'small': '0.875rem',
                }
            },
            'spacing': {
                'unit': '0.25rem',
                'scale': [0, 4, 8, 16, 24, 32, 48, 64],
            },
            'responsive_breakpoints': {
                'mobile': '320px',
                'tablet': '768px',
                'desktop': '1024px',
                'wide': '1280px',
            },
            'components': {
                'button': {
                    'padding': '0.75rem 1.5rem',
                    'border_radius': '0.5rem',
                    'font_weight': '600',
                },
                'input': {
                    'padding': '0.75rem 1rem',
                    'border_radius': '0.5rem',
                    'border': '1px solid rgba(255,255,255,0.2)',
                },
                'card': {
                    'padding': '1.5rem',
                    'border_radius': '0.75rem',
                    'background': 'rgba(255,255,255,0.02)',
                }
            }
        }
