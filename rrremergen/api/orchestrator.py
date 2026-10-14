"""Compose source artifacts with explicit provenance and a blocking validation gate."""
import base64
from dataclasses import asdict
import hashlib
import io
import json
from uuid import uuid4
import zipfile

from rrremergen.agents.architect import Architect, AppBlueprint
from rrremergen.agents.designer import Designer
from rrremergen.agents.developer import Developer
from rrremergen.agents.integrator import Integrator
from rrremergen.agents.pm import PM
from rrremergen.api.router import LLMRouter, ProviderError


class RRRemeRgenOrchestrator:
    def __init__(self, router: LLMRouter):
        self.router = router
        self.architect = Architect(router)
        self.designer = Designer(router)
        self.developer = Developer(router)
        self.integrator = Integrator(router)
        self.pm = PM(router)

    async def compose_app(self, user_prompt: str, advanced_options: dict | None = None):
        options = advanced_options or {}
        if options and options.get('mode', self.router.mode) != self.router.mode:
            raise ValueError('Router e opzioni della richiesta non coerenti')
        stage = 'architect'
        app_id = 'APP-' + uuid4().hex
        try:
            yield {'type': 'stage_progress', 'stage': stage, 'mode': self.router.mode}
            blueprint = await self.architect.analyze(user_prompt, app_id)
            yield {'type': 'stage_output', 'stage': stage, 'data': asdict(blueprint)}
            stage = 'designer'
            yield {'type': 'stage_progress', 'stage': stage}
            ui_specs = await self.designer.design(blueprint)
            yield {'type': 'stage_output', 'stage': stage, 'data': ui_specs}
            stage = 'developer'
            yield {'type': 'stage_progress', 'stage': stage}
            code = await self.developer.generate_code(blueprint, ui_specs)
            yield {'type': 'stage_output', 'stage': stage, 'summary': f'{len(code)} sorgenti generati'}
            stage = 'integrator'
            yield {'type': 'stage_progress', 'stage': stage}
            integrations = await self.integrator.setup_integrations(blueprint)
            integrations['status'] = 'configuration_only'
            yield {'type': 'stage_output', 'stage': stage, 'data': integrations}
            stage = 'pm'
            yield {'type': 'stage_progress', 'stage': stage}
            validation = await self.pm.validate_and_debug(blueprint, code, ui_specs, user_prompt)
            for iteration in range(1, 4):
                if validation['is_valid']:
                    break
                yield {'type': 'debug_iteration', 'iteration': iteration, 'issues': validation['issues']}
                fixed = await self.developer.fix_issues(code, validation['issues'])
                if fixed == code:
                    break
                code = fixed
                validation = await self.pm.validate_and_debug(blueprint, code, ui_specs, user_prompt)
            if not validation['is_valid']:
                yield {'type': 'error', 'stage': stage, 'code': 'validation_failed',
                       'message': 'I sorgenti non superano i controlli statici.', 'issues': validation['issues']}
                return
            stage = 'export'
            yield {'type': 'stage_progress', 'stage': stage}
            artifact = self._export(app_id, blueprint, code, ui_specs, integrations, validation)
            yield {'type': 'completion', 'app': {
                'id': app_id, 'title': blueprint.title, 'description': blueprint.description,
                'mode': self.router.mode, 'simulation': self.router.mode == 'demo',
                'status': 'source_generated', 'deployment_status': 'not_deployed',
                'github_url': None, 'vercel_url': None, 'validation': validation,
                'code_preview': '\n'.join(code['frontend'].splitlines()[:20]), 'artifact': artifact}}
        except Exception as error:
            message = str(error) if isinstance(error, ProviderError) else 'Generazione interrotta: output o dati non validi.'
            yield {'type': 'error', 'stage': stage, 'code': type(error).__name__, 'message': message}

    def _export(self, app_id, blueprint, code, ui_specs, integrations, validation):
        manifest = {'app_id': app_id, 'mode': self.router.mode, 'simulation': self.router.mode == 'demo',
                    'model_calls': self.router.calls,
                    'deployment_status': 'not_deployed', 'blueprint': asdict(blueprint),
                    'ui_specs': ui_specs, 'integrations': integrations, 'validation': validation}
        files = {'frontend.jsx': code['frontend'], 'backend.py': code['backend'], 'database.py': code['database'],
                 'manifest.json': json.dumps(manifest, ensure_ascii=False, indent=2),
                 'README.txt': 'Sorgenti generati da RRREMERGEN. Nessun deployment eseguito.\n'
                               'Controlli statici superati; non equivalgono a validazione funzionale o sicurezza.\n'
                               'Revisionare dipendenze e configurazione prima di eseguire i sorgenti.\n'
                               f'Modalità: {self.router.mode}. Demo significa fixture deterministica, non inferenza.\n'}
        content = io.BytesIO()
        with zipfile.ZipFile(content, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name, text in files.items():
                archive.writestr(name, text)
        data = content.getvalue()
        return {'filename': app_id + '.zip', 'content_base64': base64.b64encode(data).decode('ascii'),
                'sha256': hashlib.sha256(data).hexdigest(), 'file_count': len(files)}


class ModelAssignmentStrategy:
    """Compatibility entry point; the request router owns provider selection."""
    @staticmethod
    def get_architect_model(router):
        return router.select_model('analysis')

    @staticmethod
    def get_designer_model(router):
        return router.select_model('design')

    @staticmethod
    def get_developer_model(router):
        return router.select_model('code_generation')

    @staticmethod
    def get_integrator_model(router):
        return router.select_model('integration')

    @staticmethod
    def get_pm_model(router):
        return router.select_model('validation')
