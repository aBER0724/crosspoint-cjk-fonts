#!/usr/bin/env python3

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_release_notes.py"


def family(name: str, *, description: str = "Description") -> dict:
    return {
        "name": name,
        "description": description,
        "files": [
            {
                "name": f"{name}_{size}.cpfont",
                "size": size * 100,
                "sha256": f"{size:064x}",
            }
            for size in (8, 10, 12, 14, 16, 18, 22)
        ],
    }


class ReleaseNotesTest(unittest.TestCase):
    def run_generator(self, previous: dict | None, current: dict, plan: dict) -> str:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            current_path = root / "current.json"
            plan_path = root / "plan.json"
            output_path = root / "RELEASE_NOTES.md"
            current_path.write_text(json.dumps(current), encoding="utf-8")
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            command = [
                "python",
                str(SCRIPT),
                "--current-manifest",
                str(current_path),
                "--plan",
                str(plan_path),
                "--output",
                str(output_path),
                "--tag",
                "sd-fonts-m2-b4",
            ]
            if previous is not None:
                previous_path = root / "previous.json"
                previous_path.write_text(json.dumps(previous), encoding="utf-8")
                command.extend(["--previous-manifest", str(previous_path)])
            subprocess.run(command, cwd=ROOT, check=True)
            return output_path.read_text(encoding="utf-8")

    def test_added_family_release_uses_stable_template_and_counts(self):
        previous = {"version": 2, "families": [family("Existing")]}
        current = {"version": 2, "families": [family("Existing"), family("ZenMaruGothicJP", description="Japanese rounded sans-serif")]}
        plan = {
            "new": ["ZenMaruGothicJP"],
            "changedExisting": [],
            "remove": [],
        }

        notes = self.run_generator(previous, current, plan)

        self.assertIn("## Catalog update", notes)
        self.assertIn("2 font families", notes)
        self.assertIn("14 `.cpfont` files", notes)
        self.assertIn("### Added", notes)
        self.assertIn("**ZenMaruGothicJP** — Japanese rounded sans-serif", notes)
        self.assertIn("### Installation", notes)
        self.assertIn("### Verification and licensing", notes)
        self.assertNotIn("### Updated", notes)
        self.assertNotIn("### Removed", notes)

    def test_updated_and_removed_families_are_listed(self):
        previous = {"version": 2, "families": [family("Existing"), family("Removed")]}
        current = {"version": 2, "families": [family("Existing", description="Updated description")]}
        plan = {
            "new": [],
            "changedExisting": ["Existing"],
            "remove": ["Removed"],
        }

        notes = self.run_generator(previous, current, plan)

        self.assertIn("### Updated", notes)
        self.assertIn("**Existing** — Updated description", notes)
        self.assertIn("### Removed", notes)
        self.assertIn("**Removed**", notes)


if __name__ == "__main__":
    unittest.main()
