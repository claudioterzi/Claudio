"""Expose Jev before the existing catch-all while preserving the original Letta/MCP app."""
import letta_bridge_v2
import typesafe_legacy

app = letta_bridge_v2.app
_before = len(app.router.routes)
app.include_router(typesafe_legacy.app.router, prefix="/jev")
app.router.routes[:] = app.router.routes[_before:] + app.router.routes[:_before]
