"""IONOS Integration Bridge for RRREMERGEN.

Provides unified management of IONOS services:
- DNS (Domain management)
- Hosting (VPS & managed hosting)
- Database (PostgreSQL, MySQL, MongoDB)
- S3 Storage (Object storage)
- Email (Mailbox & SMTP services)
"""

from .auth import IONOSCredentialsManager
from .services import (
    IONOSDNSService,
    IONOSHostingService,
    IONOSDatabaseService,
    IONOSS3Service,
    IONOSEmailService,
)

__all__ = [
    'IONOSCredentialsManager',
    'IONOSDNSService',
    'IONOSHostingService',
    'IONOSDatabaseService',
    'IONOSS3Service',
    'IONOSEmailService',
]
