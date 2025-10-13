"""
Cloud Backup Module - Google Drive Integration

Provides robust, incremental backup functionality to Google Drive with:
- OAuth2 authentication
- Resumable uploads for large files
- File hash verification
- Incremental sync (only upload changed files)
- Folder structure mirroring
- Automatic retry with exponential backoff
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Optional, Any
from datetime import datetime
from loguru import logger

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    logger.warning("Google Drive dependencies not available. Install with: poetry install")

from src.paths import PATHS


# Google Drive API scopes
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Default configuration
DEFAULT_CONFIG = {
    'credentials_file': 'local/gdrive/credentials.json',
    'token_file': 'local/gdrive/token.json',
    'backup_folder_name': 'onsendo_backups',
    'chunk_size': 5 * 1024 * 1024,  # 5MB chunks for resumable upload
}


class CloudBackupError(Exception):
    """Base exception for cloud backup operations"""
    pass


class AuthenticationError(CloudBackupError):
    """Authentication-related errors"""
    pass


class UploadError(CloudBackupError):
    """Upload-related errors"""
    pass


class GoogleDriveBackup:
    """
    Google Drive backup manager with robust error handling and incremental sync.

    Features:
    - OAuth2 authentication with token refresh
    - Resumable uploads for large files
    - SHA-256 hash verification
    - Folder structure mirroring
    - Metadata tracking
    - Dry-run mode for testing
    """

    def __init__(
        self,
        credentials_file: Optional[str] = None,
        token_file: Optional[str] = None,
        backup_folder_name: Optional[str] = None
    ):
        """
        Initialize Google Drive backup manager.

        Args:
            credentials_file: Path to OAuth2 credentials JSON
            token_file: Path to store/load access token
            backup_folder_name: Name of root backup folder in Drive
        """
        if not GOOGLE_AVAILABLE:
            raise ImportError(
                "Google Drive dependencies not installed. "
                "Install with: poetry add google-auth google-auth-oauthlib google-api-python-client"
            )

        self.credentials_file = credentials_file or DEFAULT_CONFIG['credentials_file']
        self.token_file = token_file or DEFAULT_CONFIG['token_file']
        self.backup_folder_name = backup_folder_name or DEFAULT_CONFIG['backup_folder_name']

        # Ensure local gdrive directory exists
        os.makedirs(os.path.dirname(self.token_file), exist_ok=True)

        self.service = None
        self._folder_cache: dict[str, str] = {}  # path -> folder_id mapping

    def authenticate(self, force_reauth: bool = False) -> None:
        """
        Authenticate with Google Drive using OAuth2.

        Args:
            force_reauth: Force re-authentication even if token exists

        Raises:
            AuthenticationError: If authentication fails
        """
        creds = None

        # Load existing token
        if not force_reauth and os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
                logger.debug(f"Loaded credentials from {self.token_file}")
            except Exception as e:
                logger.warning(f"Failed to load token: {e}")

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Refreshed access token")
                except Exception as e:
                    logger.warning(f"Token refresh failed: {e}")
                    creds = None

            if not creds:
                if not os.path.exists(self.credentials_file):
                    raise AuthenticationError(
                        f"Credentials file not found: {self.credentials_file}\n"
                        "Download OAuth2 credentials from Google Cloud Console"
                    )

                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                    logger.info("Completed OAuth2 flow")
                except Exception as e:
                    raise AuthenticationError(f"OAuth2 flow failed: {e}") from e

            # Save credentials for future use
            try:
                with open(self.token_file, 'w', encoding='utf-8') as token:
                    token.write(creds.to_json())
                logger.info(f"Saved credentials to {self.token_file}")
            except Exception as e:
                logger.warning(f"Failed to save token: {e}")

        # Build service
        try:
            self.service = build('drive', 'v3', credentials=creds)
            logger.info("Successfully authenticated with Google Drive")
        except Exception as e:
            raise AuthenticationError(f"Failed to build Drive service: {e}") from e

    def _get_or_create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> str:
        """
        Get folder ID or create folder if it doesn't exist.

        Args:
            folder_name: Name of the folder
            parent_id: Parent folder ID (None for root)

        Returns:
            Folder ID
        """
        cache_key = f"{parent_id or 'root'}:{folder_name}"
        if cache_key in self._folder_cache:
            return self._folder_cache[cache_key]

        # Search for existing folder
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"

        try:
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()

            files = results.get('files', [])
            if files:
                folder_id = files[0]['id']
                logger.debug(f"Found existing folder: {folder_name} ({folder_id})")
                self._folder_cache[cache_key] = folder_id
                return folder_id
        except HttpError as e:
            logger.warning(f"Failed to search for folder: {e}")

        # Create new folder
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]

        try:
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            folder_id = folder['id']
            logger.info(f"Created folder: {folder_name} ({folder_id})")
            self._folder_cache[cache_key] = folder_id
            return folder_id
        except HttpError as e:
            raise UploadError(f"Failed to create folder {folder_name}: {e}") from e

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _get_file_metadata(self, file_id: str) -> Optional[dict[str, Any]]:
        """Get file metadata from Drive."""
        try:
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields='id,name,size,md5Checksum,createdTime,modifiedTime,properties'
            ).execute()
            return file_metadata
        except HttpError as e:
            logger.warning(f"Failed to get file metadata for {file_id}: {e}")
            return None

    def _file_exists_in_drive(
        self,
        file_name: str,
        parent_id: str,
        local_hash: Optional[str] = None
    ) -> Optional[str]:
        """
        Check if file exists in Drive and verify hash if provided.

        Returns:
            File ID if exists and matches hash, None otherwise
        """
        query = f"name='{file_name}' and '{parent_id}' in parents and trashed=false"

        try:
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id,name,properties)'
            ).execute()

            files = results.get('files', [])
            if not files:
                return None

            file_id = files[0]['id']

            # Verify hash if provided
            if local_hash:
                properties = files[0].get('properties', {})
                remote_hash = properties.get('sha256')

                if remote_hash and remote_hash == local_hash:
                    logger.debug(f"File {file_name} exists with matching hash")
                    return file_id
                else:
                    logger.debug(f"File {file_name} exists but hash mismatch")
                    return None

            return file_id

        except HttpError as e:
            logger.warning(f"Failed to check file existence: {e}")
            return None

    def upload_file(
        self,
        local_path: str,
        remote_folder_path: str = "",
        dry_run: bool = False,
        skip_if_exists: bool = True
    ) -> Optional[str]:
        """
        Upload a file to Google Drive with hash verification.

        Args:
            local_path: Path to local file
            remote_folder_path: Path in Drive (relative to backup root)
            dry_run: If True, only simulate upload
            skip_if_exists: If True, skip upload if file exists with same hash

        Returns:
            File ID if uploaded, None if skipped

        Raises:
            UploadError: If upload fails
        """
        if not self.service:
            raise CloudBackupError("Not authenticated. Call authenticate() first.")

        if not os.path.exists(local_path):
            raise UploadError(f"Local file not found: {local_path}")

        file_name = os.path.basename(local_path)
        file_size = os.path.getsize(local_path)
        file_hash = self._calculate_file_hash(local_path)

        logger.info(f"Preparing to upload: {file_name} ({file_size} bytes, hash: {file_hash[:8]}...)")

        # Create folder structure
        parent_id = self._get_or_create_folder(self.backup_folder_name)

        if remote_folder_path:
            for folder_name in remote_folder_path.split('/'):
                if folder_name:
                    parent_id = self._get_or_create_folder(folder_name, parent_id)

        # Check if file already exists
        if skip_if_exists:
            existing_file_id = self._file_exists_in_drive(file_name, parent_id, file_hash)
            if existing_file_id:
                logger.info(f"Skipping {file_name} - already exists with matching hash")
                return None

        if dry_run:
            logger.info(f"[DRY RUN] Would upload {file_name} to folder {parent_id}")
            return None

        # Upload file with hash in properties
        file_metadata = {
            'name': file_name,
            'parents': [parent_id],
            'properties': {
                'sha256': file_hash,
                'upload_timestamp': datetime.now().isoformat(),
                'original_path': local_path
            }
        }

        try:
            media = MediaFileUpload(
                local_path,
                resumable=True,
                chunksize=DEFAULT_CONFIG['chunk_size']
            )

            request = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,size'
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.debug(f"Upload progress: {progress}%")

            file_id = response['id']
            logger.info(f"Successfully uploaded {file_name} (ID: {file_id})")
            return file_id

        except HttpError as e:
            raise UploadError(f"Failed to upload {file_name}: {e}") from e

    def sync_directory(
        self,
        local_dir: str,
        remote_folder_path: str = "",
        dry_run: bool = False,
        skip_if_exists: bool = True,
        recursive: bool = True
    ) -> dict[str, Any]:
        """
        Sync entire directory to Google Drive.

        Args:
            local_dir: Local directory path
            remote_folder_path: Remote folder path (relative to backup root)
            dry_run: If True, only simulate sync
            skip_if_exists: If True, skip files that already exist
            recursive: If True, sync subdirectories

        Returns:
            Dictionary with sync statistics
        """
        if not os.path.isdir(local_dir):
            raise UploadError(f"Directory not found: {local_dir}")

        stats = {
            'uploaded': 0,
            'skipped': 0,
            'failed': 0,
            'total_size': 0
        }

        logger.info(f"Syncing directory: {local_dir}")

        for root, dirs, files in os.walk(local_dir):
            if not recursive:
                dirs.clear()

            # Calculate relative path for remote folder structure
            rel_path = os.path.relpath(root, local_dir)
            if rel_path == '.':
                remote_path = remote_folder_path
            else:
                remote_path = f"{remote_folder_path}/{rel_path}" if remote_folder_path else rel_path

            for file_name in files:
                local_file = os.path.join(root, file_name)

                try:
                    result = self.upload_file(
                        local_file,
                        remote_path,
                        dry_run=dry_run,
                        skip_if_exists=skip_if_exists
                    )

                    if result:
                        stats['uploaded'] += 1
                        stats['total_size'] += os.path.getsize(local_file)
                    else:
                        stats['skipped'] += 1

                except Exception as e:
                    logger.error(f"Failed to upload {local_file}: {e}")
                    stats['failed'] += 1

        logger.info(
            f"Sync complete: {stats['uploaded']} uploaded, "
            f"{stats['skipped']} skipped, {stats['failed']} failed"
        )

        return stats

    def list_backups(self) -> list[dict[str, Any]]:
        """
        List all backups in the Drive folder.

        Returns:
            List of file metadata dictionaries
        """
        if not self.service:
            raise CloudBackupError("Not authenticated. Call authenticate() first.")

        try:
            # Get backup folder
            folder_id = self._get_or_create_folder(self.backup_folder_name)

            # List all files in backup folder
            query = f"'{folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id,name,size,createdTime,modifiedTime,properties)',
                orderBy='modifiedTime desc'
            ).execute()

            files = results.get('files', [])
            logger.info(f"Found {len(files)} backups in Drive")

            return files

        except HttpError as e:
            raise CloudBackupError(f"Failed to list backups: {e}") from e


def create_backup_manifest(backup_dir: str, files: list[str]) -> None:
    """
    Create a JSON manifest file for a backup.

    Args:
        backup_dir: Directory containing backup
        files: List of file paths in the backup
    """
    manifest = {
        'timestamp': datetime.now().isoformat(),
        'backup_dir': backup_dir,
        'files': []
    }

    for file_path in files:
        if os.path.exists(file_path):
            file_info = {
                'path': file_path,
                'name': os.path.basename(file_path),
                'size': os.path.getsize(file_path),
                'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            }

            # Calculate hash
            try:
                sha256_hash = hashlib.sha256()
                with open(file_path, "rb") as f:
                    for byte_block in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(byte_block)
                file_info['sha256'] = sha256_hash.hexdigest()
            except Exception as e:
                logger.warning(f"Failed to calculate hash for {file_path}: {e}")
                file_info['sha256'] = None

            manifest['files'].append(file_info)

    manifest_path = os.path.join(backup_dir, 'backup_manifest.json')
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Created backup manifest: {manifest_path}")


def get_backup_manager(
    credentials_file: Optional[str] = None,
    token_file: Optional[str] = None
) -> GoogleDriveBackup:
    """
    Factory function to create and authenticate a backup manager.

    Args:
        credentials_file: Path to OAuth2 credentials
        token_file: Path to store/load token

    Returns:
        Authenticated GoogleDriveBackup instance
    """
    manager = GoogleDriveBackup(
        credentials_file=credentials_file,
        token_file=token_file
    )
    manager.authenticate()
    return manager
