"""Run database migrations."""
import os
import sys
from pathlib import Path

def run_migrations():
    # Add the project root to the Python path
    project_root = str(Path(__file__).resolve().parent.parent)
    if project_root not in sys.path:
        sys.path.append(project_root)
    
    # Set the database URL in the environment
    from app.config.settings import settings
    os.environ["DATABASE_URL"] = settings.DATABASE_URL
    
    # Import and run Alembic
    from alembic.config import Config
    from alembic import command
    
    # Initialize Alembic config
    alembic_cfg = Config("alembic.ini")
    
    # Create a new migration
    print("Generating new migration...")
    command.revision(
        config=alembic_cfg,
        autogenerate=True,
        message="Initial migration"
    )
    
    # Run the migration
    print("\nRunning migrations...")
    command.upgrade(alembic_cfg, "head")
    
    print("\nDatabase migrations completed successfully!")

if __name__ == "__main__":
    run_migrations()
