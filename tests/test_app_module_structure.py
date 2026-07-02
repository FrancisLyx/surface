from pathlib import Path


def test_business_modules_use_documented_module_layout():
    root = Path("app/modules")
    expected = {
        "agent": {
            "router.py",
            "schemas.py",
            "dtos.py",
            "service.py",
            "repository.py",
            "models.py",
            "runtime.py",
            "events.py",
            "uow.py",
        },
        "ai": {
            "router.py",
            "schemas.py",
            "dtos.py",
            "service.py",
            "report_service.py",
            "report_repository.py",
            "models.py",
            "uow.py",
        },
        "fund": {
            "router.py",
            "schemas.py",
            "dtos.py",
            "service.py",
            "public.py",
            "favorite_service.py",
            "favorite_repository.py",
            "models.py",
            "uow.py",
        },
        "health": {"router.py"},
        "settings": {
            "router.py",
            "schemas.py",
            "dtos.py",
            "service.py",
            "public.py",
            "repository.py",
            "models.py",
            "uow.py",
        },
        "user": {
            "router.py",
            "schemas.py",
            "dtos.py",
            "service.py",
            "repository.py",
            "models.py",
            "uow.py",
        },
    }

    for module, files in expected.items():
        module_dir = root / module
        assert module_dir.is_dir(), f"missing module directory: {module_dir}"
        for filename in files:
            assert (module_dir / filename).is_file(), (
                f"missing module file: {module_dir / filename}"
            )

    assert (root / "agent" / "graphs" / "__init__.py").is_file()
    assert (root / "agent" / "graphs" / "fund_analysis.py").is_file()
    assert (root / "agent" / "tools" / "__init__.py").is_file()
    assert (root / "agent" / "tools" / "fund.py").is_file()


def test_legacy_layer_directories_are_removed_after_module_migration():
    assert (Path("app/api") / "router.py").is_file()
    assert (Path("app/api") / "error_handlers.py").is_file()
    assert (Path("app/infrastructure") / "database" / "base.py").is_file()
    assert (Path("app/infrastructure") / "database" / "session.py").is_file()
    assert (Path("app/infrastructure") / "database" / "unit_of_work.py").is_file()
    assert (Path("app/infrastructure") / "clients" / "akshare_client.py").is_file()
    assert (Path("app/infrastructure") / "clients" / "langchain_client.py").is_file()
    assert (Path("app/infrastructure") / "messaging" / "event_bus.py").is_file()
    assert (Path("app/infrastructure") / "outbox" / "models.py").is_file()
    assert (Path("app/infrastructure") / "outbox" / "repository.py").is_file()
    assert (Path("app/infrastructure") / "outbox" / "worker.py").is_file()
    assert (Path("app/infrastructure") / "inbox" / "models.py").is_file()
    assert (Path("app/infrastructure") / "inbox" / "repository.py").is_file()
    assert Path("alembic.ini").is_file()
    assert (Path("alembic") / "env.py").is_file()
    assert any((Path("alembic") / "versions").glob("*.py"))
    assert Path(".pre-commit-config.yaml").is_file()
    assert Path("compose.yml").is_file()
    assert (Path("scripts") / "start.sh").is_file()
    assert (Path("scripts") / "test.sh").is_file()
    assert (Path("scripts") / "migrate.sh").is_file()
    assert (Path(".github") / "workflows" / "backend.yml").is_file()
    assert (Path("tests") / "unit").is_dir()
    assert (Path("tests") / "integration").is_dir()
    assert (Path("tests") / "api").is_dir()
    assert (Path("tests") / "e2e").is_dir()

    assert not Path("app/services").exists()
    assert not Path("app/repositories").exists()
    assert not Path("app/api/routes").exists()
    assert not Path("app/db").exists()
    assert not Path("app/clients").exists()
    assert not Path("app/agents").exists()
    assert not Path("app/tools").exists()
    assert not Path("app/sql").exists()


def test_core_uow_is_transaction_only_not_global_repository_container():
    source = Path("app/infrastructure/database/unit_of_work.py").read_text()

    assert "app.modules." not in source
    assert "UserRepository" not in source
    assert "SystemSettingRepository" not in source
    assert "FundFavoriteRepository" not in source
    assert "AiFundReportRepository" not in source
    assert "AgentRepository" not in source
    assert "async def __aenter__" in source
    assert "async def __aexit__" in source


def test_no_sync_sqlalchemy_session_or_startup_schema_creation_in_app_code():
    offenders: list[str] = []
    for path in Path("app").rglob("*.py"):
        source = path.read_text()
        if (
            "sqlalchemy.orm import Session" in source
            or "Base.metadata.create_all" in source
        ):
            offenders.append(str(path))

    assert offenders == []


def test_cross_module_access_uses_public_facades():
    offenders: list[str] = []
    for path in Path("app").rglob("*.py"):
        if "modules" not in path.parts:
            continue
        source = path.read_text()
        module_index = path.parts.index("modules")
        own_module = path.parts[module_index + 1]
        for imported_module in ("agent", "ai", "fund", "settings", "user"):
            if imported_module == own_module:
                continue
            direct_service_imports = (
                f"app.modules.{imported_module} import service",
                f"app.modules.{imported_module}.service",
            )
            if any(pattern in source for pattern in direct_service_imports):
                offenders.append(str(path))

    assert offenders == []
