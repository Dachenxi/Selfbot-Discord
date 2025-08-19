import aiomysql
import pymysql
import dotenv
import os
import logging
import asyncio

logger = logging.getLogger(__name__)

class Database:
    def __init__(self,
                 host:str = None,
                 port:int = None,
                 user:str = None,
                 password:str = None,
                 database:str = None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db = database
        self.pool = None
        self.max_retries = 3
        self.retry_delay = 1  # seconds

    async def _is_connection_alive(self) -> bool:
        """Check if the database connection pool is alive."""
        if not self.pool:
            return False

        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1")
                    await cursor.fetchone()
            return True
        except (pymysql.err.OperationalError, aiomysql.Error, Exception):
            return False

    async def _reconnect(self):
        """Reconnect to the database."""
        logger.warning("Attempting to reconnect to database...")

        if self.pool:
            try:
                self.pool.close()
                await self.pool.wait_closed()
            except Exception as e:
                logger.error(f"Error closing old pool: {e}")

        await self.connect()

    async def _execute_with_retry(self, operation, *args, **kwargs):
        """Execute database operation with retry logic for connection errors."""
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                if not await self._is_connection_alive():
                    await self._reconnect()

                return await operation(*args, **kwargs)

            except (pymysql.err.OperationalError, aiomysql.Error) as e:
                last_exception = e
                error_code = getattr(e, 'args', [None])[0] if hasattr(e, 'args') and e.args else None

                # Check for connection-related errors
                if error_code in (2006, 2013, 2055):  # MySQL server has gone away, Lost connection, etc.
                    logger.warning(f"Connection error (attempt {attempt + 1}/{self.max_retries}): {e}")

                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                        try:
                            await self._reconnect()
                        except Exception as reconnect_error:
                            logger.error(f"Reconnection failed: {reconnect_error}")
                    continue
                else:
                    # Non-connection related error, don't retry
                    raise e

            except Exception as e:
                logger.error(f"Unexpected error in database operation: {e}")
                raise e

        # If all retries failed
        logger.error(f"All retry attempts failed. Last error: {last_exception}")
        raise last_exception

    async def check_tables(self):
        """Check if the required tables exist in the database."""
        if not self.pool:
            logger.error("Database pool is not initialized. Call connect() first.")
            return

        async def _check_tables_operation():
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SHOW TABLES;")
                    tables = await cursor.fetchall()
                    table_names = [table[0] for table in tables]
                    if (
                            "virtualfisher" not in table_names
                            or "user" not in table_names
                            or "settings" not in table_names
                    ):
                        logger.warning("Some tables does not exist, creating it.")
                        await self.create_tables()
                    else:
                        logger.info("All required tables are present.")

        try:
            await self._execute_with_retry(_check_tables_operation)
        except Exception as e:
            logger.error(f"Error checking tables: {e}")

    async def connect(self):
        """Initialize database connection pool."""
        try:
            self.pool = await aiomysql.create_pool(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                db=self.db,
                autocommit=True,
                # Connection pool settings for better reliability
                minsize=1,
                maxsize=10,
                pool_recycle=3600,  # Recycle connections every hour
                charset='utf8mb4'
            )
            logger.info("Database connection pool created successfully.")
            await self.check_tables()
        except Exception as e:
            logger.error(f"Failed to create database connection pool: {e}")
            raise

    async def close(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("Database connection pool closed.")

    async def execute(self, query: str, args: tuple = None) -> None:
        """Execute a query without returning results."""
        if not self.pool:
            logger.error("Database pool is not initialized. Call connect() first.")
            return

        async def _execute_operation():
            logger.info(f"Executing query: {query} with args: {args}")
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    if args:
                        await cursor.execute(query, args)
                    else:
                        await cursor.execute(query)

        await self._execute_with_retry(_execute_operation)

    async def fetch(self, query: str, args: tuple = None, one: bool = False):
        """Fetch data from database."""
        if not self.pool:
            logger.error("Database pool is not initialized. Call connect() first.")
            return None

        async def _fetch_operation():
            logger.info(f"Fetching data with query: {query} with args: {args}")
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    if args:
                        await cursor.execute(query, args)
                    else:
                        await cursor.execute(query)

                    if one:
                        result = await cursor.fetchone()
                        return result if result else None
                    else:
                        result = await cursor.fetchall()
                        return result

        return await self._execute_with_retry(_fetch_operation)

    async def create_tables(self):
        """Create database tables from SQL file."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sql_file_path = os.path.join(script_dir, "table.sql")

        try:
            with open(sql_file_path, "r") as file:
                sql = file.read()
        except FileNotFoundError:
            logger.error(f"SQL file not found: {sql_file_path}")
            return
        except Exception as e:
            logger.error(f"Error reading SQL file: {e}")
            return

        queries = sql.split(";")
        for query in queries:
            query = query.strip()
            if query:
                try:
                    await self.execute(query)
                except Exception as e:
                    logger.error(f"Error executing query: {query}\nError: {e}")

dotenv.load_dotenv(".env")

try:
    db = Database(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")) if os.getenv("DB_PORT") else 3306,
        user=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
except ValueError as e:
    logger.error(f"Invalid port number in environment variables: {e}")
    db = None
