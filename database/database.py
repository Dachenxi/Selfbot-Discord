import aiomysql
import dotenv
import os
import logging

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

    async def check_tables(self):
        """Check if the required tables exist in the database."""
        if not self.pool:
            logger.error("Database pool is not initialized. Call connect() first.")
            return

        try:
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
                autocommit=True
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

        logger.info(f"Executing query: {query} with args: {args}")
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                if args:
                    await cursor.execute(query, args)
                else:
                    await cursor.execute(query)

    async def fetch(self, query: str, args: tuple = None, one: bool = False):
        """Fetch data from database."""
        if not self.pool:
            logger.error("Database pool is not initialized. Call connect() first.")
            return None

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
