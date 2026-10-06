from pathlib import Path

from sqlalchemy.orm import Session

try:
    from backend.app.models.repository import Repository, RepositoryStatus
    from backend.app.services.scanner import (
        is_binary_file,
        is_generated_file,
        is_secret_file,
        scan_repository_files,
    )
except ModuleNotFoundError:
    from app.models.repository import Repository, RepositoryStatus
    from app.services.scanner import (
        is_binary_file,
        is_generated_file,
        is_secret_file,
        scan_repository_files,
    )


def create_test_repository(db_session: Session, name: str = "TestRepo") -> Repository:
    repo = Repository(
        name=name,
        github_url=f"https://github.com/test/{name.lower()}",
        default_branch="main",
        status=RepositoryStatus.READY,
    )
    db_session.add(repo)
    db_session.commit()
    db_session.refresh(repo)
    return repo


class TestScannerIgnoredDirectories:
    """Verify that ignored build and dependency directories are never scanned."""

    def test_ignored_directories(self, db_session: Session, tmp_path: Path):
        repo = create_test_repository(db_session, "IgnoredDirsRepo")

        # Create valid source file
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "index.ts").write_text("console.log('hello');")

        # Create files inside ignored directories
        ignored_dir_names = [
            ".git",
            "node_modules",
            "dist",
            "build",
            "target",
            "venv",
            ".venv",
            "__pycache__",
            "coverage",
            "vendor",
        ]

        for d_name in ignored_dir_names:
            d_path = tmp_path / d_name
            d_path.mkdir(parents=True, exist_ok=True)
            (d_path / f"nested_file_{d_name}.txt").write_text("should be ignored")

        files = scan_repository_files(db_session, repo.id, tmp_path)

        indexed_paths = [f.path for f in files]
        assert "src/index.ts" in indexed_paths
        assert len(files) == 1

        for d_name in ignored_dir_names:
            assert not any(f.path.startswith(d_name) for f in files)


class TestScannerSecretFiles:
    """Verify secrets, keys, and credentials files are never indexed."""

    def test_secret_files_exclusion(self, db_session: Session, tmp_path: Path):
        repo = create_test_repository(db_session, "SecretsRepo")

        # Legitimate file
        (tmp_path / "config.py").write_text("DEBUG = True")

        # Secret files that must be excluded
        secret_filenames = [
            ".env",
            ".env.local",
            ".env.production",
            ".env.test",
            "id_rsa",
            "id_ed25519",
            "server.key",
            "cert.pem",
            "credentials.json",
            "client_secret.json",
            "gcp-service-account.json",
            "app-secret.yaml",
            ".npmrc",
            ".pypirc",
        ]

        for s_name in secret_filenames:
            (tmp_path / s_name).write_text("SUPER_SECRET_TOKEN=xyz")

        files = scan_repository_files(db_session, repo.id, tmp_path)

        indexed_names = [f.filename for f in files]
        assert "config.py" in indexed_names
        assert len(files) == 1

        for s_name in secret_filenames:
            assert s_name not in indexed_names

    def test_is_secret_file_function(self):
        assert is_secret_file(".env") is True
        assert is_secret_file(".env.development") is True
        assert is_secret_file("id_rsa") is True
        assert is_secret_file("private.key") is True
        assert is_secret_file("gcp-credentials.json") is True
        assert is_secret_file("safe_settings.json") is False
        assert is_secret_file("main.py") is False


class TestScannerBinaryFiles:
    """Verify binary detection via extension and null-byte buffer inspection."""

    def test_binary_files_detection(self, db_session: Session, tmp_path: Path):
        repo = create_test_repository(db_session, "BinaryRepo")

        # Binary by extension
        (tmp_path / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\n...")
        (tmp_path / "document.pdf").write_bytes(b"%PDF-1.4...")
        (tmp_path / "archive.zip").write_bytes(b"PK\x03\x04...")

        # Binary by null-byte content (unknown extension)
        (tmp_path / "data.dat").write_bytes(b"some text\x00with null byte")

        # Text file
        (tmp_path / "plain.txt").write_bytes(b"just regular plain text content")

        files = scan_repository_files(db_session, repo.id, tmp_path)
        file_map = {f.filename: f for f in files}

        assert file_map["logo.png"].is_binary is True
        assert file_map["document.pdf"].is_binary is True
        assert file_map["archive.zip"].is_binary is True
        assert file_map["data.dat"].is_binary is True
        assert file_map["plain.txt"].is_binary is False

    def test_is_binary_file_function(self, tmp_path: Path):
        img_file = tmp_path / "icon.ico"
        img_file.write_bytes(b"\x00\x00\x01\x00")
        assert is_binary_file("icon.ico", img_file) is True

        txt_file = tmp_path / "notes.md"
        txt_file.write_text("# Readme")
        assert is_binary_file("notes.md", txt_file) is False


class TestScannerSourceFiles:
    """Verify source code file extensions and language detection."""

    def test_source_files_language_detection(self, db_session: Session, tmp_path: Path):
        repo = create_test_repository(db_session, "SourceRepo")

        source_expectations = {
            "app.py": "Python",
            "main.ts": "TypeScript",
            "component.tsx": "TypeScript",
            "script.js": "JavaScript",
            "server.go": "Go",
            "lib.rs": "Rust",
            "App.java": "Java",
            "index.html": "HTML",
            "styles.css": "CSS",
            "query.sql": "SQL",
            "config.toml": "TOML",
            "deploy.yaml": "YAML",
            "Dockerfile": "Dockerfile",
            "run.sh": "Shell",
        }

        for filename in source_expectations:
            (tmp_path / filename).write_text("content")

        files = scan_repository_files(db_session, repo.id, tmp_path)
        file_map = {f.filename: f for f in files}

        for filename, expected_lang in source_expectations.items():
            assert filename in file_map
            assert file_map[filename].language == expected_lang
            assert file_map[filename].is_binary is False


class TestScannerGeneratedFiles:
    """Verify minified files, lockfiles, and generated code headers."""

    def test_generated_files_detection(self, db_session: Session, tmp_path: Path):
        repo = create_test_repository(db_session, "GeneratedRepo")

        # Minified and maps
        (tmp_path / "bundle.min.js").write_text("var a=1;")
        (tmp_path / "styles.min.css").write_text("body{margin:0}")
        (tmp_path / "bundle.js.map").write_text('{"version":3}')

        # Lockfiles
        (tmp_path / "package-lock.json").write_text('{"name": "test"}')
        (tmp_path / "yarn.lock").write_text("# yarn lockfile v1")
        (tmp_path / "Cargo.lock").write_text("[[package]]")

        # Generated extension
        (tmp_path / "service.pb.go").write_text("package service")

        # Generated code header
        gen_header_file = tmp_path / "autogen.py"
        gen_header_file.write_text("# @generated\n# DO NOT EDIT\ndef foo(): pass\n")

        # Normal file
        normal_file = tmp_path / "normal.py"
        normal_file.write_text("def bar(): return 42\n")

        files = scan_repository_files(db_session, repo.id, tmp_path)
        file_map = {f.filename: f for f in files}

        assert file_map["bundle.min.js"].is_generated is True
        assert file_map["styles.min.css"].is_generated is True
        assert file_map["bundle.js.map"].is_generated is True
        assert file_map["package-lock.json"].is_generated is True
        assert file_map["yarn.lock"].is_generated is True
        assert file_map["Cargo.lock"].is_generated is True
        assert file_map["service.pb.go"].is_generated is True
        assert file_map["autogen.py"].is_generated is True
        assert file_map["normal.py"].is_generated is False

    def test_is_generated_file_function(self, tmp_path: Path):
        gen_file = tmp_path / "bundle.min.js"
        gen_file.write_text("var x=1;")
        assert is_generated_file("bundle.min.js", gen_file) is True

        normal_file = tmp_path / "main.py"
        normal_file.write_text("print('hello')\n")
        assert is_generated_file("main.py", normal_file) is False
