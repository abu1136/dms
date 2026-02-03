"""Sync API endpoints for SMB/NAS, Nextcloud and local backup."""

import os
import logging
from typing import Optional
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator

from app.auth.security import get_current_active_user
from app.config import get_settings
from app.database.session import get_db
from app.models.user import User
from app.services.sync import SyncService, LocalBackupSync, NextcloudSync

settings = get_settings()
router = APIRouter(prefix="/api/admin/sync", tags=["Sync"])
logger = logging.getLogger(__name__)


class SyncType(str, Enum):
    """Valid sync types."""
    documents = "documents"
    logs = "logs"
    all = "all"


class SMBConfig(BaseModel):
    """SMB/NAS configuration."""
    host: str = Field(..., description="SMB server hostname or IP", min_length=1)
    port: int = Field(default=445, description="SMB port", ge=1, le=65535)
    username: str = Field(..., description="SMB username", min_length=1)
    password: str = Field(..., description="SMB password", min_length=1)
    share: str = Field(..., description="SMB share name", min_length=1)
    path: str = Field(default="/DMS", description="Path within SMB share")
    
    @field_validator('path')
    @classmethod
    def validate_path(cls, v):
        """Ensure path is relative and safe."""
        if not v:
            return "/DMS"
        # Reject absolute paths and traversal attempts
        if v.startswith('../') or '/..' in v or v.endswith('..'):
            raise ValueError('Path cannot contain ".." sequences')
        return v.rstrip('/') or '/DMS'


class NextcloudConfig(BaseModel):
    """Nextcloud configuration."""
    url: str = Field(..., description="Nextcloud server URL (e.g., https://cloud.example.com)", min_length=1)
    username: str = Field(..., description="Nextcloud username", min_length=1)
    password: str = Field(..., description="Nextcloud app password", min_length=1)
    path: str = Field(default="/DMS", description="Path within Nextcloud")
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        """Ensure URL starts with http/https."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v.rstrip('/')
    
    @field_validator('path')
    @classmethod
    def validate_path(cls, v):
        """Ensure path is relative and safe."""
        if not v:
            return "/DMS"
        if v.startswith('../') or '/..' in v or v.endswith('..'):
            raise ValueError('Path cannot contain ".." sequences')
        return v.rstrip('/') or '/DMS'


class SyncRequest(BaseModel):
    """Sync request parameters."""
    sync_type: SyncType = Field(..., description="Type of sync: documents, logs, or all")
    target: Optional[str] = Field(default=None, description="Local directory for local sync")


def check_admin(current_user: User) -> None:
    """Verify user is admin."""
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )


@router.post("/test-smb")
async def test_smb_connection(
    config: SMBConfig,
    current_user: User = Depends(get_current_active_user)
):
    """Test SMB connection."""
    check_admin(current_user)
    
    try:
        sync_service = SyncService(
            smb_host=config.host,
            smb_port=config.port,
            smb_username=config.username,
            smb_password=config.password,
            smb_share=config.share,
            smb_path=config.path
        )
        result = sync_service.verify_connection()
        return result
    except Exception as e:
        # Log detailed error, return generic message
        logger.error(f"SMB connection test failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Connection test failed. Please check your configuration and try again."
        )


@router.post("/smb")
async def sync_to_smb(
    config: SMBConfig,
    request: SyncRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Sync documents and logs to SMB share."""
    check_admin(current_user)
    
    try:
        sync_service = SyncService(
            smb_host=config.host,
            smb_port=config.port,
            smb_username=config.username,
            smb_password=config.password,
            smb_share=config.share,
            smb_path=config.path
        )
        
        results = {}
        
        if request.sync_type in ['documents', 'all']:
            docs_dir = settings.storage_dir  # Already /app/storage/uploads
            result = sync_service.sync_documents(docs_dir)
            results['documents'] = result
        
        if request.sync_type in ['logs', 'all']:
            # Sync application logs
            log_dir = os.path.join(settings.storage_dir, '../logs')
            if os.path.exists(log_dir):
                for log_file in os.listdir(log_dir):
                    if log_file.endswith('.log'):
                        log_path = os.path.join(log_dir, log_file)
                        result = sync_service.sync_logs(log_path)
                        if 'logs' not in results:
                            results['logs'] = []
                        results['logs'].append(result)
        
        return {
            'success': True,
            'message': 'Sync completed',
            'results': results
        }
    
    except Exception as e:
        logger.error(f"SMB sync failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sync operation failed. Please check your configuration and try again."
        )


@router.post("/local")
async def sync_to_local(
    request: SyncRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Sync documents to local directory."""
    check_admin(current_user)
    
    if not request.target:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="target directory required"
        )
    
    try:
        results = {}
        
        if request.sync_type in ['documents', 'all']:
            docs_dir = settings.storage_dir  # Already /app/storage/uploads
            result = LocalBackupSync.sync_to_local(docs_dir, request.target)
            results['documents'] = result
        
        if request.sync_type in ['logs', 'all']:
            log_dir = os.path.join(settings.storage_dir, '../logs')
            logs_target = os.path.join(request.target, 'logs')
            if os.path.exists(log_dir):
                result = LocalBackupSync.sync_to_local(log_dir, logs_target)
                results['logs'] = result
        
        return {
            'success': True,
            'message': 'Local sync completed',
            'results': results
        }
    
    except Exception as e:
        logger.error(f"Local sync failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sync operation failed. Please check the target directory and try again."
        )


@router.get("/status")
async def get_sync_status(
    current_user: User = Depends(get_current_active_user)
):
    """Get sync configuration status."""
    check_admin(current_user)
    
    return {
        'smb_enabled': settings.smb_enabled,
        'smb_host': settings.smb_host if settings.smb_enabled else None,
        'smb_share': settings.smb_share if settings.smb_enabled else None,
        'storage_dir': settings.storage_dir,
        'backup_dir': os.path.join(settings.storage_dir, 'backups'),
        'uploads_dir': os.path.join(settings.storage_dir, 'uploads')
    }


@router.post("/test-nextcloud")
async def test_nextcloud_connection(
    config: NextcloudConfig,
    current_user: User = Depends(get_current_active_user)
):
    """Test Nextcloud connection."""
    check_admin(current_user)
    
    try:
        sync_service = NextcloudSync(
            url=config.url,
            username=config.username,
            password=config.password,
            base_path=config.path
        )
        result = sync_service.verify_connection()
        return result
    except Exception as e:
        logger.error(f"Nextcloud connection test failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Connection test failed. Please check your Nextcloud configuration and try again."
        )


@router.post("/nextcloud")
async def sync_to_nextcloud(
    config: NextcloudConfig,
    request: SyncRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Sync documents and logs to Nextcloud."""
    check_admin(current_user)
    
    try:
        sync_service = NextcloudSync(
            url=config.url,
            username=config.username,
            password=config.password,
            base_path=config.path
        )
        
        results = {}
        
        if request.sync_type in ['documents', 'all']:
            docs_dir = settings.storage_dir  # Already /app/storage/uploads
            result = sync_service.sync_documents(docs_dir)
            results['documents'] = result
        
        if request.sync_type in ['logs', 'all']:
            # Sync application logs
            log_dir = os.path.join(settings.storage_dir, '../logs')
            if os.path.exists(log_dir):
                for log_file in os.listdir(log_dir):
                    if log_file.endswith('.log'):
                        log_path = os.path.join(log_dir, log_file)
                        result = sync_service.sync_logs(log_path)
                        if 'logs' not in results:
                            results['logs'] = []
                        results['logs'].append(result)
        
        return {
            'success': True,
            'message': 'Nextcloud sync completed',
            'results': results
        }
    
    except Exception as e:
        logger.error(f"Nextcloud sync failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sync operation failed. Please check your Nextcloud configuration and try again."
        )

