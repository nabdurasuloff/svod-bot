"""LibreOffice orqali formulalarni qayta hisoblash (kesh qiymatlari uchun)."""
import os, re, subprocess, tempfile, shutil
from pathlib import Path

MACRO = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE script:module PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "module.dtd">
<script:module xmlns:script="http://openoffice.org/2000/script" script:name="Module1" script:language="StarBasic">
    Sub RecalculateAndSave()
      ThisComponent.calculateAll()
      ThisComponent.store()
      ThisComponent.close(True)
    End Sub
</script:module>"""


def recalc(path, timeout=900):
    """Faylni joyida qayta hisoblaydi (xatolik bo'lsa RuntimeError)."""
    path = str(Path(path).absolute())
    env = dict(os.environ, SAL_USE_VCLPLUGIN="svp")
    prof = tempfile.mkdtemp(prefix="lo_prof_")
    try:
        url = Path(prof).as_uri()
        subprocess.run(["soffice", "--headless", "--terminate_after_init", f"-env:UserInstallation={url}"],
                       capture_output=True, timeout=120, env=env)
        mdir = Path(prof) / "user" / "basic" / "Standard"
        if not mdir.exists():
            raise RuntimeError("LibreOffice profili yaratilmadi")
        (mdir / "Module1.xba").write_text(MACRO)
        before = os.stat(path).st_mtime_ns
        r = subprocess.run(
            ["soffice", "--headless", "--norestore", f"-env:UserInstallation={url}",
             "vnd.sun.star.script:Standard.Module1.RecalculateAndSave?language=Basic&location=application", path],
            capture_output=True, text=True, timeout=timeout, env=env)
        if r.returncode != 0:
            raise RuntimeError("LibreOffice xatosi: " + (r.stderr or "")[:300])
        if os.stat(path).st_mtime_ns == before:
            raise RuntimeError("LibreOffice faylni qayta yozmadi")
    finally:
        shutil.rmtree(prof, ignore_errors=True)
