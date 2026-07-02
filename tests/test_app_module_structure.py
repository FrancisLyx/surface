from pathlib import Path


def test_business_modules_use_documented_module_layout():
    root = Path("app/modules")
    expected = {
        "agent": {"api.py", "schema.py", "service.py", "repository.py", "model.py", "runtime.py", "event.py"},
        "ai": {"api.py", "schema.py", "service.py", "report_service.py", "report_repository.py", "report_model.py"},
        "fund": {"api.py", "schema.py", "service.py", "favorite_service.py", "favorite_repository.py", "favorite_model.py"},
        "health": {"api.py"},
        "settings": {"api.py", "schema.py", "service.py", "repository.py", "model.py"},
        "user": {"api.py", "schema.py", "service.py", "repository.py", "model.py"},
    }

    for module, files in expected.items():
        module_dir = root / module
        assert module_dir.is_dir(), f"missing module directory: {module_dir}"
        for filename in files:
            assert (module_dir / filename).is_file(), f"missing module file: {module_dir / filename}"


def test_legacy_layer_directories_are_removed_after_module_migration():
    assert not Path("app/services").exists()
    assert not Path("app/repositories").exists()
    assert not Path("app/api/routes").exists()
    assert not Path("app/db/models").exists()
