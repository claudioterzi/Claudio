#!/usr/bin/env python3
"""
IONOS Credentials Manager — Secure handling of IONOS API credentials.

Supports all IONOS services:
- API Token for general operations
- DNS API Key for domain management
- Database credentials
- S3 Access Keys
- Email API credentials
"""

import os
import json
from typing import Dict, Optional
from datetime import datetime, timedelta
import httpx


class IONOSCredentialsManager:
    """Manages IONOS API credentials securely."""

    def __init__(self):
        """Initialize with credentials from environment."""
        self.api_token = os.getenv('IONOS_API_TOKEN')
        self.dns_api_key = os.getenv('IONOS_DNS_API_KEY')
        self.account_id = os.getenv('IONOS_ACCOUNT_ID')
        self.datacenter = os.getenv('IONOS_DATACENTER', 'de')

        # Database
        self.db_host = os.getenv('IONOS_DB_HOST')
        self.db_user = os.getenv('IONOS_DB_USER')
        self.db_password = os.getenv('IONOS_DB_PASSWORD')
        self.db_port = int(os.getenv('IONOS_DB_PORT', '5432'))

        # S3 Storage
        self.s3_access_key = os.getenv('IONOS_S3_ACCESS_KEY')
        self.s3_secret_key = os.getenv('IONOS_S3_SECRET_KEY')
        self.s3_region = os.getenv('IONOS_S3_REGION', 'eu-central-1')
        self.s3_endpoint = os.getenv('IONOS_S3_ENDPOINT', 'https://s3.eu-central-1.ionos.com')

        # Email
        self.email_api_key = os.getenv('IONOS_EMAIL_API_KEY')
        self.smtp_host = os.getenv('IONOS_SMTP_HOST', 'smtp.ionos.com')
        self.smtp_port = int(os.getenv('IONOS_SMTP_PORT', '465'))

        # Primary domain
        self.primary_domain = os.getenv('IONOS_PRIMARY_DOMAIN')

        # Credentials last validated
        self._last_validation = None

    async def validate_credentials(self) -> Dict[str, bool]:
        """Validate all IONOS credentials are functional."""
        results = {
            'api_token': await self._test_api_token(),
            'dns_api': await self._test_dns_api(),
            'database': await self._test_db_connection(),
            's3': await self._test_s3_connection(),
            'email': await self._test_email_api(),
        }

        self._last_validation = datetime.now()
        return results

    async def _test_api_token(self) -> bool:
        """Test main API token validity."""
        if not self.api_token:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    'https://api.ionos.com/v1.0/user/info',
                    headers={
                        'X-API-Key': self.api_token,
                        'Accept': 'application/json'
                    },
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception:
            return False

    async def _test_dns_api(self) -> bool:
        """Test DNS API key validity."""
        if not self.dns_api_key or not self.primary_domain:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f'https://api.hosting.ionos.com/dns/v1/domains/{self.primary_domain}',
                    headers={
                        'Authorization': f'Bearer {self.dns_api_key}',
                        'Accept': 'application/json'
                    },
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception:
            return False

    async def _test_db_connection(self) -> bool:
        """Test database connection."""
        if not all([self.db_host, self.db_user, self.db_password]):
            return False

        try:
            import psycopg2
            conn = psycopg2.connect(
                host=self.db_host,
                user=self.db_user,
                password=self.db_password,
                port=self.db_port,
                connect_timeout=10
            )
            conn.close()
            return True
        except Exception:
            return False

    async def _test_s3_connection(self) -> bool:
        """Test S3 (IONOS storage) connection."""
        if not all([self.s3_access_key, self.s3_secret_key]):
            return False

        try:
            import boto3
            from botocore.exceptions import NoCredentialsError

            client = boto3.client(
                's3',
                endpoint_url=self.s3_endpoint,
                aws_access_key_id=self.s3_access_key,
                aws_secret_access_key=self.s3_secret_key,
                region_name=self.s3_region,
            )

            # List buckets to test connection
            client.list_buckets()
            return True
        except Exception:
            return False

    async def _test_email_api(self) -> bool:
        """Test email API validity."""
        if not self.email_api_key:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    'https://api.hosting.ionos.com/email/v1/mailboxes',
                    headers={
                        'Authorization': f'Bearer {self.email_api_key}',
                        'Accept': 'application/json'
                    },
                    timeout=10.0
                )
                return response.status_code in [200, 400]  # 400 is OK if auth passed
        except Exception:
            return False

    def get_db_connection_string(self, database_name: str) -> str:
        """Get PostgreSQL connection string."""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{database_name}"

    def get_s3_config(self) -> Dict[str, str]:
        """Get S3 configuration for boto3."""
        return {
            'endpoint_url': self.s3_endpoint,
            'aws_access_key_id': self.s3_access_key,
            'aws_secret_access_key': self.s3_secret_key,
            'region_name': self.s3_region,
        }

    def get_smtp_config(self) -> Dict[str, any]:
        """Get SMTP configuration."""
        return {
            'host': self.smtp_host,
            'port': self.smtp_port,
            'use_tls': True,
            'ssl': self.smtp_port == 465,
        }

    async def rotate_api_token(self, new_token: str) -> bool:
        """Rotate API token (manual operation)."""
        if await self._test_api_token_validity(new_token):
            self.api_token = new_token
            return True
        return False

    async def _test_api_token_validity(self, token: str) -> bool:
        """Test if a new API token is valid."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    'https://api.ionos.com/v1.0/user/info',
                    headers={
                        'X-API-Key': token,
                        'Accept': 'application/json'
                    },
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception:
            return False

    def is_valid(self) -> bool:
        """Check if all required credentials are present."""
        required = [
            self.api_token,
            self.account_id,
        ]
        return all(required)

    def get_validation_status(self) -> Dict[str, any]:
        """Get last validation status."""
        return {
            'is_valid': self.is_valid(),
            'last_validated': self._last_validation,
            'requires_validation': (
                self._last_validation is None or
                datetime.now() - self._last_validation > timedelta(hours=24)
            ),
        }
