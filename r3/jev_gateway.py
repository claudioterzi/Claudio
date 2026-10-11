"""Expose Jev before the existing catch-all while preserving the original Letta/MCP app."""
from importlib import import_module

import typesafe_sister
import typesafe_legacy

# The environment-materialized historical wrapper imports the canonical package
# and reads ``typesafe_sister.app`` while it is being imported.  Keep the
# package itself intact (notably ``typesafe_sister.client``), and expose the
# already-loaded combined-runtime app object only at that compatibility seam.
typesafe_sister.app = typesafe_legacy.app
# The wrapper's root health endpoint delegates to the historical module too.
typesafe_sister.health = typesafe_legacy.health

letta_bridge_v2 = import_module("letta_bridge_v2")

app = letta_bridge_v2.app
_before = len(app.router.routes)
app.include_router(typesafe_legacy.app.router, prefix="/jev")
app.router.routes[:] = app.router.routes[_before:] + app.router.routes[:_before]
