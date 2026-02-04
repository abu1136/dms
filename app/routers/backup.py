import os
import shutil
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth.security import get_current_active_user
from app.config import get_settings
from app.database.session import get_db
from app.models.user import User

settings = get_settings()
router = APIRouter(prefix="/api/admin/backup", tags=["Backup"])


def check_admin(current_user: User) -> None:
    """Verify user is admin."""
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )


@router.post("/create")
async def create_backup(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a backup of documents, templates, and logs."""
    check_admin(current_user)
    
    try:
        backup_dir = os.path.join(settings.storage_dir, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Create zip file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"DMS_Backup_{timestamp}.zip"
        backup_path = os.path.join(backup_dir, backup_name)
        
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all files recursively from storage directory
            storage_path = settings.storage_dir
            if os.path.exists(storage_path):
                for root, dirs, files in os.walk(storage_path):
                    # Skip backups directory to avoid recursion
                    if 'backups' in root:
                        continue
                    
                    for file in files:
                        if file.startswith('.'):
                            continue
                        file_path = os.path.join(root, file)
                        # Create relative path for archive
                        arcname = os.path.relpath(file_path, storage_path)
                        zipf.write(file_path, arcname=arcname)
        
        return {
            'backup_file': backup_name,
            'path': backup_path,
            'size': os.path.getsize(backup_path),
            'timestamp': timestamp
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup creation failed: {str(e)}"
        )


@router.get("/list")
async def list_backups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List available backups."""
    check_admin(current_user)
    
    try:
        backup_dir = os.path.join(settings.storage_dir, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        backups = []
        if os.path.exists(backup_dir):
            for file in sorted(os.listdir(backup_dir), reverse=True):
                if file.endswith('.zip'):
                    file_path = os.path.join(backup_dir, file)
                    stat = os.stat(file_path)
                    backups.append({
                        'name': file,
                        'size': stat.st_size,
                        'date': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    })
        
        return {'backups': backups}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list backups: {str(e)}"
        )


@router.get("/download/{backup_name}")
async def download_backup(
    backup_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Download a backup file."""
    check_admin(current_user)
    
    try:
        backup_dir = os.path.join(settings.storage_dir, 'backups')
        backup_path = os.path.join(backup_dir, backup_name)
        
        # Security check
        backup_dir_abs = os.path.abspath(backup_dir)
        backup_path_abs = os.path.abspath(backup_path)
        if '..' in backup_name or not backup_path_abs.startswith(backup_dir_abs):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid backup name"
            )
        
        if not os.path.exists(backup_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup not found"
            )
        
        return FileResponse(
            path=backup_path,
            media_type='application/zip',
            filename=backup_name
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {str(e)}"
        )


@router.post("/restore")
async def restore_backup(
    backup_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Restore from a backup file."""
    check_admin(current_user)
    
    try:
        backup_name = backup_data.get('backup_file')
        if not backup_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="backup_file required"
            )
        
        backup_dir = os.path.join(settings.storage_dir, 'backups')
        backup_path = os.path.join(backup_dir, backup_name)
        
        # Security check
        backup_dir_abs = os.path.abspath(backup_dir)
        backup_path_abs = os.path.abspath(backup_path)
        if '..' in backup_name or not backup_path_abs.startswith(backup_dir_abs):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid backup name"
            )
        
        if not os.path.exists(backup_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup not found"
            )
        
        # Extract backup
        storage_dir = settings.storage_dir
        storage_dir_abs = os.path.abspath(storage_dir)
        
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            for file_info in zipf.infolist():
                if file_info.is_dir():
                    continue
                
                file_name = file_info.filename
                if not file_name or file_name.startswith('/') or '..' in Path(file_name).parts:
                    continue
                
                target_path = os.path.abspath(os.path.join(storage_dir, file_name))
                if not target_path.startswith(storage_dir_abs):
                    continue
                
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with zipf.open(file_info) as source:
                    with open(target_path, 'wb') as target:
                        target.write(source.read())
        
        return {'message': 'Backup restored successfully'}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Restore failed: {str(e)}"
        )
