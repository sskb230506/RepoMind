import os
import tempfile
from pathlib import Path

from alembic.config import Config

from alembic import command


def test_alembic_migration_upgrade_and_downgrade():
    """Verify that Alembic migrations can execute upgrade and downgrade cleanly."""
    backend_dir = Path(__file__).resolve().parent.parent
    alembic_ini_path = str(backend_dir / "alembic.ini")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
        db_path = tmp_file.name

    try:
        # Format sqlite path with forward slashes
        clean_db_path = db_path.replace("\\", "/")
        alembic_cfg = Config(alembic_ini_path)
        alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{clean_db_path}")

        # 1. Upgrade to head
        command.upgrade(alembic_cfg, "head")

        # 2. Downgrade to base
        command.downgrade(alembic_cfg, "base")

        # 3. Upgrade to head again
        command.upgrade(alembic_cfg, "head")
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
