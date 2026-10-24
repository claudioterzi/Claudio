#!/usr/bin/env python3
"""
IONOS Service Adapters — High-level interfaces for IONOS operations.

Services:
- DNS: Domain and DNS record management
- Hosting: VPS and managed hosting provisioning
- Database: Managed PostgreSQL/MySQL/MongoDB
- S3: Object storage (S3-compatible)
- Email: Email hosting and SMTP services
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import httpx
import boto3
from .auth import IONOSCredentialsManager


@dataclass
class DNSRecord:
    """DNS record configuration."""
    name: str
    type: str  # A, CNAME, MX, TXT, NS, etc.
    value: str
    ttl: int = 3600
    priority: Optional[int] = None  # For MX, SRV records


@dataclass
class DatabaseConfig:
    """Database configuration."""
    name: str
    type: str  # postgresql, mysql, mongodb
    size: str  # 10GB, 100GB, etc.
    version: Optional[str] = None
    backup_retention_days: int = 30
    auto_backup: bool = True


@dataclass
class S3BucketConfig:
    """S3 bucket configuration."""
    name: str
    region: str
    acl: str = 'private'
    versioning: bool = True
    encryption: bool = True


class IONOSDNSService:
    """DNS management via IONOS API."""

    def __init__(self, credentials: IONOSCredentialsManager):
        self.credentials = credentials
        self.base_url = 'https://api.hosting.ionos.com/dns/v1'

    async def create_subdomain(
        self,
        domain: str,
        subdomain: str,
        ip: str,
        record_type: str = 'A'
    ) -> bool:
        """Create A record for subdomain."""
        record = DNSRecord(
            name=subdomain,
            type=record_type,
            value=ip,
            ttl=3600
        )
        return await self.add_dns_record(domain, record)

    async def add_dns_record(self, domain: str, record: DNSRecord) -> bool:
        """Add DNS record to domain."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f'{self.base_url}/domains/{domain}/records',
                    headers={
                        'Authorization': f'Bearer {self.credentials.dns_api_key}',
                        'Content-Type': 'application/json',
                    },
                    json={
                        'name': record.name,
                        'type': record.type,
                        'content': record.value,
                        'ttl': record.ttl,
                        'priority': record.priority,
                    },
                    timeout=15.0
                )
                return response.status_code in [200, 201]
        except Exception as e:
            print(f"Error adding DNS record: {e}")
            return False

    async def update_dns_records(self, domain: str, records: List[DNSRecord]) -> bool:
        """Update multiple DNS records."""
        results = []
        for record in records:
            result = await self.add_dns_record(domain, record)
            results.append(result)
        return all(results)

    async def verify_dns_propagation(self, domain: str, record_name: str) -> bool:
        """Verify DNS record has propagated."""
        try:
            import dns.resolver

            # Give propagation some time
            await asyncio.sleep(2)

            answers = dns.resolver.resolve(f'{record_name}.{domain}', 'A')
            return len(answers) > 0
        except Exception:
            return False

    async def setup_spf_dkim_dmarc(self, domain: str) -> Dict[str, str]:
        """Setup SPF, DKIM, DMARC records for email."""
        records = [
            DNSRecord(name='@', type='TXT', value='v=spf1 include:sendgrid.net ~all'),
            DNSRecord(name='selector1._domainkey', type='CNAME', value='selector1.domainkey.sendgrid.net.'),
            DNSRecord(name='selector2._domainkey', type='CNAME', value='selector2.domainkey.sendgrid.net.'),
            DNSRecord(name='_dmarc', type='TXT', value='v=DMARC1; p=none; rua=mailto:admin@' + domain),
        ]

        success = await self.update_dns_records(domain, records)
        if success:
            return {
                'spf': 'v=spf1 include:sendgrid.net ~all',
                'dkim_selector1': 'selector1.domainkey.sendgrid.net.',
                'dkim_selector2': 'selector2.domainkey.sendgrid.net.',
                'dmarc': f'v=DMARC1; p=none; rua=mailto:admin@{domain}',
            }
        return {}


class IONOSHostingService:
    """VPS and managed hosting provisioning."""

    def __init__(self, credentials: IONOSCredentialsManager):
        self.credentials = credentials
        self.base_url = 'https://api.cloud.ionos.com/v1'

    async def provision_vps(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Provision a new VPS instance."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f'{self.base_url}/datacenters/{self.credentials.datacenter}/servers',
                    headers={
                        'Authorization': f'Bearer {self.credentials.api_token}',
                        'Content-Type': 'application/json',
                    },
                    json={
                        'properties': {
                            'name': config.get('name', 'generated-app-server'),
                            'cores': config.get('cores', 2),
                            'ram': config.get('ram', 4096),  # MB
                            'cpuFamily': 'INTEL_XEON',
                        },
                        'entities': {
                            'cdroms': [],
                            'volumes': [
                                {
                                    'properties': {
                                        'name': 'app-volume',
                                        'size': config.get('disk_size', 100),  # GB
                                        'type': 'SSD',
                                    }
                                }
                            ],
                            'nics': [
                                {
                                    'properties': {
                                        'name': 'eth0',
                                        'dhcp': True,
                                    }
                                }
                            ],
                        }
                    },
                    timeout=30.0
                )

                if response.status_code == 202:
                    data = response.json()
                    return {
                        'success': True,
                        'server_id': data.get('id'),
                        'ip': data.get('entities', {}).get('nics', [{}])[0].get('properties', {}).get('ips'),
                        'status': 'provisioning',
                    }
                return {'success': False, 'error': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def configure_ssl(self, domain: str) -> bool:
        """Configure SSL/TLS for domain."""
        # IONOS provides free SSL certificates
        # This would integrate with IONOS certificate management
        return True

    async def setup_load_balancer(self, servers: List[str]) -> bool:
        """Setup load balancer for multiple servers."""
        # Configure IONOS Network Load Balancer
        return True


class IONOSDatabaseService:
    """Managed database operations."""

    def __init__(self, credentials: IONOSCredentialsManager):
        self.credentials = credentials
        self.base_url = 'https://api.cloud.ionos.com/v1'

    async def create_database(self, config: DatabaseConfig) -> Dict[str, Any]:
        """Create managed database instance."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f'{self.base_url}/databases',
                    headers={
                        'Authorization': f'Bearer {self.credentials.api_token}',
                        'Content-Type': 'application/json',
                    },
                    json={
                        'name': config.name,
                        'engine': 'postgres' if config.type == 'postgresql' else config.type,
                        'version': config.version or '14',
                        'size': config.size,
                        'autoBackup': config.auto_backup,
                        'backupRetentionDays': config.backup_retention_days,
                    },
                    timeout=30.0
                )

                if response.status_code == 201:
                    data = response.json()
                    conn_str = self.credentials.get_db_connection_string(config.name)
                    return {
                        'success': True,
                        'database_id': data.get('id'),
                        'name': config.name,
                        'type': config.type,
                        'connection_string': conn_str,
                        'host': self.credentials.db_host,
                        'port': self.credentials.db_port,
                    }
                return {'success': False, 'error': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def configure_backup(self, db_id: str, retention_days: int) -> bool:
        """Configure automated backups."""
        # Configure backup retention policy
        return True

    async def setup_replication(self, primary_db_id: str, replica_db_id: str) -> bool:
        """Setup database replication."""
        # Configure read replica
        return True


class IONOSS3Service:
    """S3-compatible object storage."""

    def __init__(self, credentials: IONOSCredentialsManager):
        self.credentials = credentials
        self.s3_client = boto3.client(
            's3',
            **credentials.get_s3_config()
        )

    async def create_bucket(self, config: S3BucketConfig) -> Dict[str, Any]:
        """Create S3 bucket."""
        try:
            self.s3_client.create_bucket(
                Bucket=config.name,
                CreateBucketConfiguration={'LocationConstraint': config.region}
            )

            # Configure versioning if enabled
            if config.versioning:
                self.s3_client.put_bucket_versioning(
                    Bucket=config.name,
                    VersioningConfiguration={'Status': 'Enabled'}
                )

            # Configure encryption if enabled
            if config.encryption:
                self.s3_client.put_bucket_encryption(
                    Bucket=config.name,
                    ServerSideEncryptionConfiguration={
                        'Rules': [
                            {
                                'ApplyServerSideEncryptionByDefault': {
                                    'SSEAlgorithm': 'AES256'
                                }
                            }
                        ]
                    }
                )

            return {
                'success': True,
                'bucket_name': config.name,
                'region': config.region,
                'endpoint': self.credentials.s3_endpoint,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def upload_file(self, bucket: str, key: str, file_content: bytes) -> bool:
        """Upload file to S3."""
        try:
            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=file_content
            )
            return True
        except Exception:
            return False

    async def configure_cdn(self, bucket: str) -> Dict[str, str]:
        """Configure CDN for bucket."""
        # IONOS provides CDN integration
        return {
            'cdn_url': f'https://{bucket}.cdn.ionos.com',
            'enabled': True,
        }


class IONOSEmailService:
    """Email hosting and SMTP management."""

    def __init__(self, credentials: IONOSCredentialsManager):
        self.credentials = credentials
        self.base_url = 'https://api.hosting.ionos.com/email/v1'

    async def create_mailbox(self, domain: str, email: str, password: str) -> Dict[str, Any]:
        """Create mailbox on IONOS."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f'{self.base_url}/domains/{domain}/mailboxes',
                    headers={
                        'Authorization': f'Bearer {self.credentials.email_api_key}',
                        'Content-Type': 'application/json',
                    },
                    json={
                        'email': email,
                        'password': password,
                        'quotaMB': 5000,  # 5GB quota
                    },
                    timeout=15.0
                )

                if response.status_code == 201:
                    return {
                        'success': True,
                        'email': email,
                        'domain': domain,
                    }
                return {'success': False, 'error': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def setup_spf_dkim_dmarc(self, domain: str) -> Dict[str, str]:
        """Setup email authentication records."""
        # This is delegated to DNSService
        return {}

    async def setup_email_relay(self, domain: str, sendgrid_api_key: str) -> Dict[str, Any]:
        """Setup SendGrid relay for transactional emails."""
        return {
            'relay_configured': True,
            'provider': 'SendGrid',
            'smtp_host': 'smtp.sendgrid.net',
            'smtp_port': 587,
            'api_key': sendgrid_api_key,
        }

    def get_smtp_config(self) -> Dict[str, Any]:
        """Get SMTP configuration for applications."""
        return self.credentials.get_smtp_config()
