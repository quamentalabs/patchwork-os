# SPDX-License-Identifier: MIT
"""Regression contracts for PWOS-PRESERVE-001; exercise real fixture bytes."""

from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from patchwork_os import hub_spoke_gate as gate


def make_source(base: Path, is_dir: bool) -> tuple[Path, Path]:
    src = base / "source"
    if is_dir:
        src.mkdir()
        data = src / "source.bin"
    else:
        data = src
    data.write_bytes(b"source\x00\xff\n")
    return src, data


def symlink_or_skip(dst: Path, target: Path, is_dir: bool) -> None:
    try:
        dst.symlink_to(target, target_is_directory=is_dir)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"native symlink fixture unavailable: {exc}")


def deny_symlink(*args, **kwargs) -> None:
    raise OSError("forced symlink failure")


def forbid_remove(*args, **kwargs) -> None:
    pytest.fail("an existing binding was removed")


@pytest.mark.parametrize("is_dir", [False, True])
def test_default_preserves_existing_bytes(tmp_path, is_dir):
    src, source_data = make_source(tmp_path, is_dir)
    dst = tmp_path / "destination"
    if is_dir:
        dst.mkdir()
        data = dst / "operator-existing.txt"
    else:
        data = dst
    data.write_bytes(b"operator\x00\xfe\n")
    before = data.read_bytes()
    original = source_data.read_bytes()

    result = gate.safe_bind_spoke(src, dst, is_dir=is_dir, allow_junction=False)

    assert data.read_bytes() == before
    assert source_data.read_bytes() == original
    assert result["tier"] == "PRESERVED_EXISTING"
    assert not dst.is_symlink()


@pytest.mark.parametrize("is_dir", [False, True])
def test_same_source_symlink_is_reused_without_removal(tmp_path, monkeypatch, is_dir):
    src, data = make_source(tmp_path, is_dir)
    dst = tmp_path / "destination"
    symlink_or_skip(dst, src, is_dir)
    target = os.readlink(dst)
    before = data.read_bytes()
    monkeypatch.setattr(gate, "_safe_remove_destination", forbid_remove)

    for _ in range(2):
        result = gate.safe_bind_spoke(src, dst, is_dir=is_dir, allow_junction=False)
        assert result["tier"] == "SYMLINK"
        assert os.readlink(dst) == target
        assert data.read_bytes() == before


@pytest.mark.parametrize("is_dir", [False, True])
@pytest.mark.parametrize("replace", [False, True])
def test_foreign_symlink_target_survives(tmp_path, is_dir, replace):
    src, source_data = make_source(tmp_path, is_dir)
    external = tmp_path / "external"
    if is_dir:
        external.mkdir()
        external_data = external / "operator-existing.txt"
    else:
        external_data = external
    external_data.write_bytes(b"external\x00\xfd\n")
    before = external_data.read_bytes()
    dst = tmp_path / "destination"
    symlink_or_skip(dst, external, is_dir)
    options = {"overwrite_existing": True} if replace else {}

    result = gate.safe_bind_spoke(
        src, dst, is_dir=is_dir, allow_junction=False, **options
    )

    assert external_data.read_bytes() == before
    assert source_data.read_bytes() == b"source\x00\xff\n"
    if replace:
        bound_data = dst / "source.bin" if is_dir else dst
        assert bound_data.read_bytes() == source_data.read_bytes()
    else:
        assert result["tier"] == "PRESERVED_EXISTING"
        assert dst.is_symlink()
        assert dst.resolve() == external.resolve()


def test_dangling_symlink_is_preserved(tmp_path):
    src, _ = make_source(tmp_path, False)
    dst = tmp_path / "destination"
    symlink_or_skip(dst, tmp_path / "missing-external", False)
    before = os.readlink(dst)
    result = gate.safe_bind_spoke(src, dst, allow_junction=False)
    assert result["tier"] == "PRESERVED_EXISTING"
    assert dst.is_symlink()
    assert os.readlink(dst) == before


@pytest.mark.parametrize("layout", ["same_file", "same_dir", "source_inside_dst", "dst_inside_source"])
@pytest.mark.parametrize("replace", [False, True])
def test_overlap_is_rejected_before_mutation(tmp_path, layout, replace):
    if layout == "same_file":
        src = dst = tmp_path / "same"
        src.write_bytes(b"operator\n")
        data = src
        is_dir = False
    elif layout == "same_dir":
        src = dst = tmp_path / "same"
        src.mkdir()
        data = src / "keep.bin"
        data.write_bytes(b"operator\n")
        is_dir = True
    elif layout == "source_inside_dst":
        dst = tmp_path / "container"
        dst.mkdir()
        src = data = dst / "source.bin"
        data.write_bytes(b"operator\n")
        is_dir = False
    else:
        src = tmp_path / "source"
        src.mkdir()
        data = src / "keep.bin"
        data.write_bytes(b"operator\n")
        dst = src / "new-parent" / "destination"
        is_dir = True
    before = data.read_bytes()
    options = {"overwrite_existing": True} if replace else {}

    with pytest.raises(ValueError, match="BIND_SOURCE_DESTINATION_OVERLAP"):
        gate.safe_bind_spoke(src, dst, is_dir=is_dir, allow_junction=False, **options)

    assert data.read_bytes() == before
    if layout == "dst_inside_source":
        assert not dst.parent.exists()


def test_missing_source_does_not_remove_destination(tmp_path):
    dst = tmp_path / "destination"
    dst.write_bytes(b"keep\n")
    with pytest.raises(FileNotFoundError):
        gate.safe_bind_spoke(tmp_path / "missing", dst, allow_junction=False)
    assert dst.read_bytes() == b"keep\n"


@pytest.mark.parametrize("replace", [False, True])
def test_parent_component_destination_is_rejected_before_removal(tmp_path, monkeypatch, replace):
    child = tmp_path / "container" / "child"
    child.mkdir(parents=True)
    src = child / "source.bin"
    src.write_bytes(b"source\n")
    sentinel = child.parent / "operator-existing.txt"
    sentinel.write_bytes(b"operator\n")
    monkeypatch.setattr(gate, "_safe_remove_destination", forbid_remove)

    with pytest.raises(ValueError, match="BIND_DESTINATION_PARENT_COMPONENT"):
        gate.safe_bind_spoke(
            src, child / "..", allow_junction=False, overwrite_existing=replace
        )

    assert src.read_bytes() == b"source\n"
    assert sentinel.read_bytes() == b"operator\n"


def test_wrong_source_kind_does_not_remove_destination(tmp_path):
    src, _ = make_source(tmp_path, False)
    dst = tmp_path / "destination"
    dst.mkdir()
    data = dst / "keep.bin"
    data.write_bytes(b"keep\n")
    with pytest.raises(ValueError, match="BIND_SOURCE_KIND_MISMATCH"):
        gate.safe_bind_spoke(src, dst, is_dir=True, allow_junction=False)
    assert data.read_bytes() == b"keep\n"


@pytest.mark.parametrize("is_dir", [False, True])
def test_copy_fallback_is_created_then_preserved(tmp_path, monkeypatch, is_dir):
    src, source_data = make_source(tmp_path, is_dir)
    dst = tmp_path / "destination"
    monkeypatch.setattr(Path, "symlink_to", deny_symlink)
    first = gate.safe_bind_spoke(src, dst, is_dir=is_dir, allow_junction=False)
    copied = dst / "source.bin" if is_dir else dst
    before = copied.read_bytes()
    assert first["tier"] == "ATOMIC_COPY_FALLBACK"
    assert before == source_data.read_bytes()
    source_data.write_bytes(b"changed-source\n")
    if is_dir:
        extra = dst / "operator-existing.txt"
        extra.write_bytes(b"operator\n")

    second = gate.safe_bind_spoke(src, dst, is_dir=is_dir, allow_junction=False)

    assert copied.read_bytes() == before
    assert source_data.read_bytes() == b"changed-source\n"
    assert second["tier"] == "PRESERVED_EXISTING"
    if is_dir:
        assert extra.read_bytes() == b"operator\n"


def test_hardlink_fallback_can_be_reused_without_removal(tmp_path, monkeypatch):
    src, data = make_source(tmp_path, False)
    probe = tmp_path / "hardlink-probe"
    try:
        os.link(src, probe)
    except OSError as exc:
        pytest.skip(f"native hardlink fixture unavailable: {exc}")
    probe.unlink()
    monkeypatch.setattr(Path, "symlink_to", deny_symlink)
    monkeypatch.setattr(gate.platform, "system", lambda: "Windows")
    dst = tmp_path / "destination"
    first = gate.safe_bind_spoke(src, dst)
    assert first["tier"] == "HARDLINK"
    assert dst.samefile(src)
    monkeypatch.setattr(gate, "_safe_remove_destination", forbid_remove)
    second = gate.safe_bind_spoke(src, dst)
    assert second["tier"] == "HARDLINK"
    assert dst.samefile(src)
    assert data.read_bytes() == b"source\x00\xff\n"


@pytest.mark.skipif(os.name != "nt", reason="requires native Windows junctions")
@pytest.mark.parametrize("mode", ["same", "foreign_preserve", "foreign_replace"])
def test_native_junction_target_preservation(tmp_path, monkeypatch, mode):
    import _winapi

    create = getattr(_winapi, "CreateJunction", None)
    if create is None or not callable(getattr(Path, "is_junction", None)):
        pytest.skip("native junction creation/detection API unavailable")
    src, source_data = make_source(tmp_path, True)
    external = tmp_path / "external"
    external.mkdir()
    keep = external / "operator-existing.txt"
    keep.write_bytes(b"external\n")
    dst = tmp_path / "destination"
    target = src if mode == "same" else external
    try:
        create(str(target), str(dst))
    except OSError as exc:
        pytest.skip(f"native junction fixture unavailable: {exc}")
    assert dst.is_junction()
    if mode != "foreign_replace":
        monkeypatch.setattr(gate, "_safe_remove_destination", forbid_remove)
    options = {"overwrite_existing": True} if mode == "foreign_replace" else {}

    result = gate.safe_bind_spoke(src, dst, is_dir=True, allow_junction=False, **options)

    assert keep.read_bytes() == b"external\n"
    assert source_data.read_bytes() == b"source\x00\xff\n"
    if mode == "same":
        assert result["tier"] == "NTFS_JUNCTION"
        assert dst.is_junction() and dst.resolve() == src.resolve()
    elif mode == "foreign_preserve":
        assert result["tier"] == "PRESERVED_EXISTING"
        assert dst.is_junction() and dst.resolve() == external.resolve()
    else:
        assert (dst / "source.bin").read_bytes() == source_data.read_bytes()


@pytest.mark.parametrize("spoke_is_dir", [False, True])
@pytest.mark.parametrize("overwrite_docs", [False, True])
def test_bootstrap_preserves_spokes_and_scopes_explicit_doc_overwrite(
    tmp_path, monkeypatch, spoke_is_dir, overwrite_docs
):
    data_paths = []
    for rel in (".kiro/steering", ".muse/vault-graft"):
        spoke = tmp_path / rel
        spoke.parent.mkdir(parents=True, exist_ok=True)
        if spoke_is_dir:
            spoke.mkdir()
            data = spoke / "operator-existing.txt"
        else:
            data = spoke
        data.write_bytes(b"operator-spoke\n")
        data_paths.append(data)
    for name in ("CLAUDE.md", "AGENTS.md"):
        (tmp_path / name).write_bytes(b"operator-rules\n")
    monkeypatch.setattr(Path, "symlink_to", deny_symlink)
    monkeypatch.setattr(gate.platform, "system", lambda: "Linux")

    for _ in range(2):
        manifest = gate.bootstrap_agnostic_hub(
            tmp_path, overwrite_existing_root_docs=overwrite_docs
        )
        assert all(data.read_bytes() == b"operator-spoke\n" for data in data_paths)
        for name in ("kiro_steering", "muse_graft"):
            assert manifest["spokes"][name]["tier"] == "PRESERVED_EXISTING"
        for name in ("CLAUDE.md", "AGENTS.md"):
            if overwrite_docs:
                rules = tmp_path / ".agent-hub/steering/core_rules.md"
                assert (tmp_path / name).read_bytes() == rules.read_bytes()
                assert manifest["spokes"][name]["tier"] == "ATOMIC_COPY_FALLBACK"
            else:
                assert (tmp_path / name).read_bytes() == b"operator-rules\n"
                assert manifest["spokes"][name]["tier"] == "PRESERVED_EXISTING"
