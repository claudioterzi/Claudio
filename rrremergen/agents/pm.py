#!/usr/bin/env python3
"""
PM Agent — Validates generated code and runs self-debugging loop.
"""

import json
import ast
from typing import Dict, Any


class PM:
    """Validates and debugs generated applications."""

    def __init__(self, router):
        self.router = router

    async def validate_and_debug(
        self,
        blueprint,
        code: Dict[str, str],
        ui_specs: Dict[str, Any],
        original_prompt: str
    ) -> Dict[str, Any]:
        """
        Validate generated code and identify issues.

        Returns:
            Validation results with issues list (empty if valid)
        """
        validation_results = {
            'is_valid': True,
            'issues': [],
            'warnings': [],
            'score': 100,
            'verification_mode': 'deterministic_structural',
            'requirements_review': 'not_executed',
            'runtime_verified': False,
        }

        # Check 1: Code completeness
        completeness_issues = await self._check_completeness(blueprint, code)
        validation_results['issues'].extend(completeness_issues)

        # Check 2: Code quality
        quality_issues = await self._check_quality(code)
        validation_results['issues'].extend(quality_issues)

        # Check 3: Alignment with requirements
        alignment_issues = await self._check_alignment(blueprint, original_prompt, code)
        validation_results['issues'].extend(alignment_issues)

        # Check 4: Security
        security_warnings = await self._check_security(code)
        validation_results['warnings'].extend(security_warnings)

        # Update validity status
        validation_results['is_valid'] = len(validation_results['issues']) == 0
        validation_results['score'] = max(0, 100 - (len(validation_results['issues']) * 15))

        return validation_results

    async def _check_completeness(self, blueprint, code: Dict[str, str]) -> list:
        """Check if all required components are present."""
        issues = []

        # Check frontend completeness
        frontend = code.get('frontend', '')
        for component in blueprint.ui_components:
            if component.lower() not in frontend.lower():
                issues.append({
                    'severity': 'warning',
                    'type': 'missing_component',
                    'message': f'Component "{component}" may be incomplete in frontend',
                })

        # Check backend completeness
        backend = code.get('backend', '')
        for route in blueprint.api_routes:
            path = route.get('path', '')
            if path.lower() not in backend.lower():
                issues.append({
                    'severity': 'warning',
                    'type': 'missing_route',
                    'message': f'API route "{path}" may be incomplete in backend',
                })

        # Check authentication
        if 'auth' in blueprint.requirements or any('auth' in r.lower() for r in blueprint.requirements):
            if 'jwt' not in backend.lower() and 'token' not in backend.lower():
                issues.append({
                    'severity': 'error',
                    'type': 'missing_auth',
                    'message': 'Authentication not implemented (JWT or similar required)',
                })

        return issues

    async def _check_quality(self, code: Dict[str, str]) -> list:
        """Check code quality issues."""
        issues = []

        frontend = code.get('frontend', '')
        backend = code.get('backend', '')

        # Check for basic structure
        for name in ('frontend', 'backend', 'database'):
            source = code.get(name, '')
            if not isinstance(source, str) or not source.strip() or 'placeholder' in source.lower() or source.startswith('// Error'):
                issues.append({'severity': 'error', 'type': 'missing_code', 'message': f'Sorgente {name} incompleto'})
        for name in ('backend', 'database'):
            try:
                ast.parse(code.get(name, ''))
            except (SyntaxError, TypeError):
                issues.append({'severity': 'error', 'type': 'invalid_syntax', 'message': f'Sintassi Python non valida in {name}'})
        if len(frontend) < 200:
            issues.append({
                'severity': 'error',
                'type': 'insufficient_code',
                'message': 'Frontend code too short (likely incomplete)',
            })

        if len(backend) < 200:
            issues.append({
                'severity': 'error',
                'type': 'insufficient_code',
                'message': 'Backend code too short (likely incomplete)',
            })

        # Check for error handling
        if 'try' not in backend and 'except' not in backend:
            issues.append({
                'severity': 'warning',
                'type': 'missing_error_handling',
                'message': 'No error handling patterns detected in backend',
            })

        return issues

    async def _check_alignment(self, blueprint, original_prompt: str, code: Dict[str, str]) -> list:
        """Check if generated code aligns with original requirements."""
        # In a real implementation, this would use LLM to check alignment
        # Semantic alignment is not verified by these structural checks.
        return []

    async def _check_security(self, code: Dict[str, str]) -> list:
        """Check for security issues."""
        warnings = []
        warnings.append({'severity': 'info', 'type': 'verification_scope',
                         'message': 'Controlli statici: esecuzione, sintassi JSX e aderenza completa ai requisiti restano da verificare.'})

        backend = code.get('backend', '')
        frontend = code.get('frontend', '')

        # Check for SQL injection vulnerability mentions
        if 'sql' in backend.lower() and 'parameterized' not in backend.lower():
            warnings.append({
                'severity': 'warning',
                'type': 'security',
                'message': 'SQL queries should use parameterized queries to prevent injection',
            })

        # Check for CORS
        if 'cors' not in backend.lower():
            warnings.append({
                'severity': 'info',
                'type': 'security',
                'message': 'Configure CORS properly for production',
            })

        # Check for environment variable usage
        if 'env' not in backend.lower():
            warnings.append({
                'severity': 'warning',
                'type': 'security',
                'message': 'Consider using environment variables for secrets',
            })

        return warnings
