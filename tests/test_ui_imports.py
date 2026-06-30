def test_mobile_and_desktop_modules_import() -> None:
    from dosimetry_app.desktop import app as desktop_app
    from dosimetry_app.mobile import app as mobile_app

    assert callable(desktop_app.run)
    assert callable(mobile_app.run)


def test_mobile_dialog_uses_supported_page_api() -> None:
    from pathlib import Path

    source = Path("src/dosimetry_app/mobile/components.py").read_text(encoding="utf-8")
    assert ".show_dialog(" in source
    assert ".pop_dialog(" in source
    assert ".open(" not in source
    assert ".close(" not in source
