"""SMB/NAS and Nextcloud sync service for syncing documents and logs."""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
import mimetypes

try:
    from smb.SMBConnection import SMBConnection
    from smb.smb_structs import OperationFailure
    HAS_SMB = True
except ImportError:
    HAS_SMB = False

try:
    from webdav3.client import Client as WebDAVClient
    HAS_WEBDAV = True
except ImportError:
    HAS_WEBDAV = False


class SyncService:
    """Handle sync to SMB/NAS shares."""
    
    def __init__(self, smb_host: str, smb_port: int, smb_username: str, 
                 smb_password: str, smb_share: str, smb_path: str):
        """Initialize SMB connection parameters."""
        self.smb_host = str(smb_host).strip() if smb_host else ""
        self.smb_port = int(smb_port) if smb_port else 445
        self.smb_username = str(smb_username).strip() if smb_username else ""
        self.smb_password = str(smb_password).strip() if smb_password else ""
        self.smb_share = str(smb_share).strip() if smb_share else ""
        self.smb_path = str(smb_path).strip() if smb_path else "/DMS"
        self.connection = None
    
    def _connect(self) -> bool:
        """Establish SMB connection."""
        if not HAS_SMB:
            raise ImportError("pysmb library not installed. Install with: pip install pysmb")
        
        # Validate connection parameters
        if not self.smb_host or not isinstance(self.smb_host, str):
            raise ValueError(f"Invalid SMB host: {self.smb_host}")
        if not self.smb_username or not isinstance(self.smb_username, str):
            raise ValueError(f"Invalid SMB username: {self.smb_username}")
        if not self.smb_password or not isinstance(self.smb_password, str):
            raise ValueError(f"Invalid SMB password")
        if not self.smb_share or not isinstance(self.smb_share, str):
            raise ValueError(f"Invalid SMB share: {self.smb_share}")
        
        try:
            self.connection = SMBConnection(
                username=str(self.smb_username),
                password=str(self.smb_password),
                my_name="DMS_APP",
                remote_name=str(self.smb_host),
                use_ntlm_v2=True
            )
            # Connect with host and port as separate arguments
            connected = self.connection.connect(str(self.smb_host), int(self.smb_port))
            if not connected:
                raise Exception(f"Connection to {self.smb_host}:{self.smb_port} failed")
            return True
        except ValueError as ve:
            raise ValueError(f"Invalid SMB configuration: {str(ve)}")
        except Exception as e:
            raise Exception(f"Failed to connect to SMB at {self.smb_host}:{self.smb_port}: {str(e)}")
    
    def _disconnect(self) -> None:
        """Close SMB connection."""
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
    
    def sync_documents(self, source_dir: str) -> Dict:
        """Sync documents to SMB share."""
        if not self._connect():
            return {'success': False, 'message': 'Failed to connect to SMB'}
        
        try:
            sync_log = {
                'timestamp': datetime.now().isoformat(),
                'files_synced': 0,
                'files_failed': 0,
                'files': [],
                'errors': []
            }
            
            if not os.path.exists(source_dir):
                return {'success': False, 'message': f'Source directory not found: {source_dir}'}
            
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    if file.startswith('.'):
                        continue
                    
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, source_dir)
                    smb_target = f"{self.smb_path}/{relative_path}".replace('\\', '/')
                    smb_dir = '/'.join(smb_target.split('/')[:-1])
                    
                    try:
                        # Create directory structure on SMB
                        self._create_smb_dir(smb_dir)
                        
                        # Upload file
                        with open(file_path, 'rb') as f:
                            self.connection.storeFile(
                                self.smb_share,
                                smb_target,
                                f
                            )
                        
                        sync_log['files_synced'] += 1
                        sync_log['files'].append({
                            'name': file,
                            'path': relative_path,
                            'size': os.path.getsize(file_path)
                        })
                    except Exception as e:
                        sync_log['files_failed'] += 1
                        sync_log['errors'].append({
                            'file': relative_path,
                            'error': str(e)
                        })
            
            return {
                'success': True,
                'message': f"Synced {sync_log['files_synced']} files",
                'log': sync_log
            }
        
        finally:
            self._disconnect()
    
    def _create_smb_dir(self, smb_path: str) -> None:
        """Create directory structure on SMB share."""
        parts = smb_path.split('/')
        current_path = ''
        
        for part in parts:
            if not part:
                continue
            current_path = f"{current_path}/{part}"
            
            try:
                self.connection.createDirectory(self.smb_share, current_path)
            except OperationFailure:
                # Directory might already exist
                pass
            except Exception as e:
                raise Exception(f"Failed to create SMB directory {current_path}: {str(e)}")
    
    def sync_logs(self, log_file: str) -> Dict:
        """Sync log file to SMB share."""
        if not self._connect():
            return {'success': False, 'message': 'Failed to connect to SMB'}
        
        try:
            if not os.path.exists(log_file):
                return {'success': False, 'message': f'Log file not found: {log_file}'}
            
            # Create logs directory on SMB
            logs_smb_path = f"{self.smb_path}/logs"
            self._create_smb_dir(logs_smb_path)
            
            # Copy log with timestamp
            log_filename = os.path.basename(log_file)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            target_name = f"{log_filename.replace('.log', '')}_{timestamp}.log"
            smb_target = f"{logs_smb_path}/{target_name}"
            
            with open(log_file, 'rb') as f:
                self.connection.storeFile(self.smb_share, smb_target, f)
            
            return {
                'success': True,
                'message': f"Log synced: {target_name}",
                'file': {
                    'name': target_name,
                    'size': os.path.getsize(log_file)
                }
            }
        
        finally:
            self._disconnect()
    
    def verify_connection(self) -> Dict:
        """Test SMB connection."""
        try:
            # Validate input first
            if not self.smb_host or not str(self.smb_host).strip():
                return {'success': False, 'message': 'SMB host is required'}
            if not self.smb_username or not str(self.smb_username).strip():
                return {'success': False, 'message': 'SMB username is required'}
            if not self.smb_password or not str(self.smb_password).strip():
                return {'success': False, 'message': 'SMB password is required'}
            if not self.smb_share or not str(self.smb_share).strip():
                return {'success': False, 'message': 'SMB share is required'}
            
            if self._connect():
                # List shares to verify
                shares = self.connection.listShares()
                share_names = [share.name for share in shares]
                self._disconnect()
                
                if self.smb_share not in share_names:
                    return {
                        'success': False,
                        'message': f"Share '{self.smb_share}' not found",
                        'available_shares': share_names
                    }
                
                return {
                    'success': True,
                    'message': 'Connected successfully',
                    'share': self.smb_share
                }
        except ValueError as ve:
            return {'success': False, 'message': f'Configuration error: {str(ve)}'}
        except Exception as e:
            return {'success': False, 'message': f'Connection error: {str(e)}'}


class LocalBackupSync:
    """Local backup sync without SMB (file copy)."""
    
    @staticmethod
    def sync_to_local(source_dir: str, target_dir: str) -> Dict:
        """Sync documents to local directory."""
        try:
            os.makedirs(target_dir, exist_ok=True)
            
            sync_log = {
                'timestamp': datetime.now().isoformat(),
                'files_synced': 0,
                'files_failed': 0,
                'files': [],
                'errors': []
            }
            
            if not os.path.exists(source_dir):
                return {'success': False, 'message': f'Source directory not found: {source_dir}'}
            
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    if file.startswith('.'):
                        continue
                    
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, source_dir)
                    target_path = os.path.join(target_dir, relative_path)
                    
                    try:
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        shutil.copy2(file_path, target_path)
                        
                        sync_log['files_synced'] += 1
                        sync_log['files'].append({
                            'name': file,
                            'path': relative_path,
                            'size': os.path.getsize(file_path)
                        })
                    except Exception as e:
                        sync_log['files_failed'] += 1
                        sync_log['errors'].append({
                            'file': relative_path,
                            'error': str(e)
                        })
            
            return {
                'success': True,
                'message': f"Synced {sync_log['files_synced']} files to {target_dir}",
                'log': sync_log
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}


class NextcloudSync:
    """Nextcloud/WebDAV sync service."""
    
    def __init__(self, url: str, username: str, password: str, base_path: str = "/DMS"):
        """Initialize Nextcloud connection parameters."""
        self.url = str(url).strip().rstrip('/') if url else ""
        self.username = str(username).strip() if username else ""
        self.password = str(password).strip() if password else ""
        self.base_path = str(base_path).strip() if base_path else "/DMS"
        self.client = None
    
    def _connect(self) -> bool:
        """Establish WebDAV connection to Nextcloud."""
        if not HAS_WEBDAV:
            raise ImportError("webdavclient3 library not installed. Install with: pip install webdavclient3")
        
        # Validate connection parameters
        if not self.url or not isinstance(self.url, str):
            raise ValueError(f"Invalid Nextcloud URL: {self.url}")
        if not self.username or not isinstance(self.username, str):
            raise ValueError(f"Invalid Nextcloud username: {self.username}")
        if not self.password or not isinstance(self.password, str):
            raise ValueError(f"Invalid Nextcloud password")
        
        try:
            # Nextcloud WebDAV endpoint is at /remote.php/dav/files/USERNAME/
            webdav_url = f"{self.url}/remote.php/dav/files/{self.username}/"
            
            options = {
                'webdav_hostname': webdav_url,
                'webdav_login': self.username,
                'webdav_password': self.password,
                'webdav_timeout': 30
            }
            
            self.client = WebDAVClient(options)
            
            # Test connection by checking if root exists
            if not self.client.check('/'):
                raise Exception("WebDAV root directory not accessible")
            
            return True
        except ValueError as ve:
            raise ValueError(f"Invalid Nextcloud configuration: {str(ve)}")
        except Exception as e:
            raise Exception(f"Failed to connect to Nextcloud at {self.url}: {str(e)}")
    
    def _create_remote_dir(self, remote_path: str) -> None:
        """Create directory structure on Nextcloud."""
        parts = [p for p in remote_path.split('/') if p]
        current_path = ''
        
        for part in parts:
            current_path = f"{current_path}/{part}"
            try:
                if not self.client.check(current_path):
                    self.client.mkdir(current_path)
            except Exception as e:
                # Directory might already exist
                pass
    
    def sync_documents(self, source_dir: str) -> Dict:
        """Sync documents to Nextcloud."""
        if not self._connect():
            return {'success': False, 'message': 'Failed to connect to Nextcloud'}
        
        try:
            sync_log = {
                'timestamp': datetime.now().isoformat(),
                'files_synced': 0,
                'files_failed': 0,
                'files': [],
                'errors': []
            }
            
            if not os.path.exists(source_dir):
                return {'success': False, 'message': f'Source directory not found: {source_dir}'}
            
            # Create base directory on Nextcloud
            self._create_remote_dir(self.base_path)
            
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    if file.startswith('.'):
                        continue
                    
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, source_dir)
                    remote_path = f"{self.base_path}/{relative_path}".replace('\\', '/')
                    remote_dir = '/'.join(remote_path.split('/')[:-1])
                    
                    try:
                        # Create directory structure
                        self._create_remote_dir(remote_dir)
                        
                        # Upload file
                        self.client.upload_sync(remote_path=remote_path, local_path=file_path)
                        
                        sync_log['files_synced'] += 1
                        sync_log['files'].append({
                            'name': file,
                            'path': relative_path,
                            'size': os.path.getsize(file_path),
                            'remote_path': remote_path
                        })
                    except Exception as e:
                        sync_log['files_failed'] += 1
                        sync_log['errors'].append({
                            'file': relative_path,
                            'error': str(e)
                        })
            
            return {
                'success': True,
                'message': f"Synced {sync_log['files_synced']} files to Nextcloud",
                'log': sync_log
            }
        
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def sync_logs(self, log_file: str) -> Dict:
        """Sync log file to Nextcloud."""
        if not self._connect():
            return {'success': False, 'message': 'Failed to connect to Nextcloud'}
        
        try:
            if not os.path.exists(log_file):
                return {'success': False, 'message': f'Log file not found: {log_file}'}
            
            # Create logs directory
            logs_remote_path = f"{self.base_path}/logs"
            self._create_remote_dir(logs_remote_path)
            
            # Copy log with timestamp
            log_filename = os.path.basename(log_file)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            target_name = f"{log_filename.replace('.log', '')}_{timestamp}.log"
            remote_path = f"{logs_remote_path}/{target_name}"
            
            self.client.upload_sync(remote_path=remote_path, local_path=log_file)
            
            return {
                'success': True,
                'message': f"Log synced to Nextcloud: {target_name}",
                'file': {
                    'name': target_name,
                    'size': os.path.getsize(log_file),
                    'remote_path': remote_path
                }
            }
        
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def verify_connection(self) -> Dict:
        """Test Nextcloud connection."""
        try:
            # Validate input first
            if not self.url or not str(self.url).strip():
                return {'success': False, 'message': 'Nextcloud URL is required'}
            if not self.username or not str(self.username).strip():
                return {'success': False, 'message': 'Nextcloud username is required'}
            if not self.password or not str(self.password).strip():
                return {'success': False, 'message': 'Nextcloud password is required'}
            
            if self._connect():
                # Check available space
                try:
                    info = self.client.info('/')
                    return {
                        'success': True,
                        'message': 'Connected to Nextcloud successfully',
                        'url': self.url,
                        'username': self.username
                    }
                except:
                    return {
                        'success': True,
                        'message': 'Connected to Nextcloud successfully',
                        'url': self.url,
                        'username': self.username
                    }
        except ValueError as ve:
            return {'success': False, 'message': f'Configuration error: {str(ve)}'}
        except Exception as e:
            return {'success': False, 'message': f'Connection error: {str(e)}'}

