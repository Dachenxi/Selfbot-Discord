import json
import os
import logging

logger = logging.getLogger(__name__)

class Settings:
    def __init__(self, database=None):
        self.path = "database/settings.json"
        self.settings = None
        self.database = database
        self.user_id = None  # Will be set when bot starts
        self.load_settings()

    def load_settings(self):
        """Load settings from JSON file as fallback"""
        try:
            # Ensure database directory exists
            os.makedirs("database", exist_ok=True)

            with open(self.path, "r") as f:
                self.settings = json.load(f)
                logger.info("Settings loaded from JSON file")

        except FileNotFoundError:
            # Create default settings
            default_settings = {"prefix": "!"}
            try:
                with open(self.path, "w") as f:
                    json.dump(default_settings, f, indent=4)
                self.settings = default_settings
                logger.info("Created new settings file with defaults")
            except PermissionError:
                logger.warning("Cannot write to settings file, using memory-only settings")
                self.settings = default_settings

        except (json.JSONDecodeError, PermissionError) as e:
            logger.warning(f"Error loading settings file: {e}, using defaults")
            self.settings = {"prefix": "!"}

    async def get_async(self, key: str, default=None):
        """Get setting from database if available, otherwise from JSON"""
        if self.database and self.database.pool and self.user_id:
            try:
                if key == "prefix":
                    return await self.database.get_user_prefix(self.user_id)
            except Exception as e:
                logger.warning(f"Database error getting {key}: {e}, falling back to JSON")

        return self.settings.get(key, default)

    def get(self, key: str, default=None):
        """Synchronous get for backward compatibility"""
        return self.settings.get(key, default)

    async def set(self, key, value):
        """Set setting in database if available, and update JSON as backup"""
        if self.database and self.database.pool and self.user_id:
            try:
                if key == "prefix":
                    await self.database.set_user_prefix(self.user_id, value)
                    logger.info(f"Updated {key} in database")
            except Exception as e:
                logger.warning(f"Database error setting {key}: {e}")

        # Always update local settings as backup
        self.settings[key] = value
        self.save_settings()

    def set_user_id(self, user_id: int):
        """Set the user ID for database operations"""
        self.user_id = user_id
        logger.info(f"Settings configured for user ID: {user_id}")

    def save_settings(self):
        """Save settings to JSON file"""
        try:
            with open(self.path, "w") as f:
                json.dump(self.settings, f, indent=4)
        except PermissionError:
            logger.warning("Cannot write to settings file - permission denied")
        except Exception as e:
            logger.warning(f"Error saving settings: {e}")
