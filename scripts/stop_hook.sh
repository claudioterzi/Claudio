#!/bin/bash
# SDQ-1 Stop Hook — si attiva quando la sessione Claude si ferma
# Esegue il prossimo task autonomo disponibile e committa

cd /home/user/Claudio || exit 0

# Esegui task se API key disponibile
if [ -n "$ANTHROPIC_API_KEY" ]; then
    python scripts/agente_orario.py >> /tmp/sdq1-autonomo.log 2>&1 || true
fi

# Committa eventuali output generati
git add output/task_output/ TASK_AUTONOMI.md 2>/dev/null || true
if ! git diff --staged --quiet 2>/dev/null; then
    GIT_AUTHOR_NAME="Claude" \
    GIT_AUTHOR_EMAIL="noreply@anthropic.com" \
    GIT_COMMITTER_NAME="Claude" \
    GIT_COMMITTER_EMAIL="noreply@anthropic.com" \
    git commit -m "SDQ-1 autonomo post-sessione $(date +%Y-%m-%d\ %H:%M)" 2>/dev/null || true
    git push 2>/dev/null || true
fi
