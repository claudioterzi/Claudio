"""Explicit deterministic fixture: tests the pipeline, never claims AI generation."""
import json

FRONTEND = '''import React, { useState } from 'react';
export default function Dashboard() {
  const [tasks, setTasks] = useState([]);
  const [title, setTitle] = useState('');
  return <main><h1>Demo attività</h1><form onSubmit={event => {
    event.preventDefault();
    if (title.trim()) setTasks([...tasks, title.trim()]);
    setTitle('');
  }}><input value={title} onChange={event => setTitle(event.target.value)}
    aria-label="Nuova attività" /><button>Aggiungi</button></form>
    <ul>{tasks.map((task, index) => <li key={index}>{task}</li>)}</ul></main>;
}
'''
BACKEND = '''from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
app = FastAPI()
tasks = []
class Task(BaseModel):
    title: str
@app.get('/api/tasks')
def list_tasks():
    return tasks
@app.post('/api/tasks')
def create_task(task: Task):
    try:
        title = task.title.strip()
        if not title:
            raise ValueError('Titolo vuoto')
        tasks.append({'title': title})
        return tasks[-1]
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
'''
DATABASE = 'SCHEMA = {"tasks": {"title": "string"}}\n'


def completion(prompt: str) -> str:
    if 'Architect agent' in prompt:
        return json.dumps(dict(title='Demo attività', description='Esempio deterministico per verificare la pipeline.',
            requirements=['Elenco attività', 'Aggiunta attività'], data_models=[{'model': 'Task', 'fields': {'title': 'string'}}],
            api_routes=[{'path': '/api/tasks', 'method': 'GET'}], ui_components=['Dashboard'], integrations=[], constraints=[]))
    if 'Designer agent' in prompt:
        return json.dumps({'color_palette': {'primary': '#00d4ff'}, 'typography': {'body_font': 'system-ui'}})
    if 'React component' in prompt:
        return FRONTEND
    if 'FastAPI Python' in prompt:
        return BACKEND
    if 'MongoDB' in prompt:
        return DATABASE
    raise ValueError('Prompt non previsto dalla modalità demo')
