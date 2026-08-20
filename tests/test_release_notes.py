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
    def run_generator(
        self,
        previous: dict | None,
        current: dict,
        plan: dict,
        *,
        previous_notes: str | None = None,
        date: str | None = None,
        pr: str | None = None,
    ) -> str:
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
            if previous_notes is not None:
                notes_path = root / "previous_notes.md"
                notes_path.write_text(previous_notes, encoding="utf-8")
                command.extend(["--previous-notes", str(notes_path)])
            if date is not None:
                command.extend(["--date", date])
            if pr is not None:
                command.extend(["--pr", str(pr)])
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

        notes = self.run_generator(previous, current, plan, date="2026-08-20")

        self.assertIn("## Catalog update", notes)
        self.assertIn("2 font families", notes)
        self.assertIn("14 `.cpfont` files", notes)
        self.assertIn("## Changelog", notes)
        self.assertIn("Add **ZenMaruGothicJP** — Japanese rounded sans-serif", notes)
        self.assertIn("<summary>2026-08-20</summary>", notes)
        self.assertIn("### Installation", notes)
        self.assertIn("### Verification", notes)
        self.assertNotIn("licens", notes.lower())
        self.assertIn("Source links", notes)
        self.assertNotIn("### Added", notes)
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

        notes = self.run_generator(previous, current, plan, date="2026-08-20")

        self.assertIn("## Changelog", notes)
        self.assertIn("Update **Existing** — Updated description", notes)
        self.assertIn("Remove **Removed**", notes)
        self.assertNotIn("### Added", notes)
        self.assertNotIn("### Updated", notes)
        self.assertNotIn("### Removed", notes)

    def test_changelog_accumulates_oldest_last_and_links_pr(self):
        previous = {"version": 2, "families": [family("Existing")]}
        current = {"version": 2, "families": [family("Existing"), family("ZenMaruGothicJP", description="Japanese rounded sans-serif")]}
        plan = {
            "new": ["ZenMaruGothicJP"],
            "changedExisting": [],
            "remove": [],
        }
        previous_notes = "\n".join(
            [
                "## Catalog update",
                "",
                "This update keeps the stable `sd-fonts-m2-b4` compatibility channel.",
                "",
                "### Added",
                "",
                "- **Existing** — Description",
                "",
                "## Changelog",
                "",
                "<details>",
                "<summary>2026-08-18</summary>",
                "",
                "- Add **Existing** — Description",
                "",
                "</details>",
                "",
                "### Installation",
                "",
                "Install me.",
            ]
        )

        notes = self.run_generator(
            previous,
            current,
            plan,
            previous_notes=previous_notes,
            date="2026-08-20",
            pr="32",
        )

        self.assertIn("## Changelog", notes)
        self.assertIn("<summary>2026-08-20</summary>", notes)
        self.assertIn("<summary>2026-08-18</summary>", notes)
        self.assertIn("Add **ZenMaruGothicJP** — Japanese rounded sans-serif", notes)
        self.assertIn("via [PR #32](https://github.com/aBER0724/crosspoint-cjk-fonts/pull/32)", notes)
        self.assertLess(
            notes.index("<summary>2026-08-20</summary>"),
            notes.index("<summary>2026-08-18</summary>"),
            "newest changelog entry must appear before older ones",
        )

    def test_first_changelog_without_previous_notes_has_only_current_entry(self):
        previous = {"version": 2, "families": [family("Existing")]}
        current = {"version": 2, "families": [family("Existing"), family("ZenMaruGothicJP", description="Japanese rounded sans-serif")]}
        plan = {
            "new": ["ZenMaruGothicJP"],
            "changedExisting": [],
            "remove": [],
        }

        notes = self.run_generator(previous, current, plan, date="2026-08-20")

        self.assertIn("<summary>2026-08-20</summary>", notes)
        self.assertNotIn("<summary>2026-08-18</summary>", notes)
        self.assertNotIn("via [PR", notes)

    def test_changelog_preserved_when_families_unchanged(self):
        previous = {"version": 2, "families": [family("Existing")]}
        current = {"version": 2, "families": [family("Existing")]}
        plan = {
            "new": [],
            "changedExisting": [],
            "remove": [],
        }
        previous_notes = "\n".join(
            [
                "## Catalog update",
                "",
                "This update keeps the stable `sd-fonts-m2-b4` compatibility channel.",
                "",
                "### Changes",
                "",
                "- Release metadata refreshed.",
                "",
                "## Changelog",
                "",
                "<details>",
                "<summary>2026-08-18</summary>",
                "",
                "- Add **Existing** — Description",
                "",
                "</details>",
                "",
                "### Installation",
                "",
                "Install me.",
            ]
        )

        notes = self.run_generator(
            previous,
            current,
            plan,
            previous_notes=previous_notes,
            date="2026-08-20",
        )

        self.assertIn("## Changelog", notes)
        self.assertIn("<summary>2026-08-18</summary>", notes)
        self.assertNotIn("<summary>2026-08-20</summary>", notes)
        self.assertNotIn("via [PR", notes)

    def test_no_changelog_when_nothing_changed_and_no_history(self):
        previous = {"version": 2, "families": [family("Existing")]}
        current = {"version": 2, "families": [family("Existing")]}
        plan = {
            "new": [],
            "changedExisting": [],
            "remove": [],
        }

        notes = self.run_generator(previous, current, plan)

        self.assertNotIn("## Changelog", notes)
        self.assertNotIn("<details>", notes)

    def test_same_day_duplicate_rebuild_does_not_add_entry(self):
        previous = {"version": 2, "families": [family("Existing")]}
        current = {"version": 2, "families": [family("Existing")]}
        plan = {
            "new": [],
            "changedExisting": ["Existing"],
            "remove": [],
        }
        previous_notes = "\n".join(
            [
                "## Catalog update",
                "",
                "This update keeps the stable `sd-fonts-m2-b4` compatibility channel.",
                "",
                "## Changelog",
                "",
                "<details>",
                "<summary>2026-08-20</summary>",
                "",
                "- Update **Existing** — Description (via [PR #35](https://github.com/aBER0724/crosspoint-cjk-fonts/pull/35))",
                "",
                "</details>",
                "",
                "### Installation",
                "",
                "Install me.",
            ]
        )

        notes = self.run_generator(
            previous,
            current,
            plan,
            previous_notes=previous_notes,
            date="2026-08-20",
            pr="36",
        )

        self.assertIn("## Changelog", notes)
        self.assertEqual(notes.count("<summary>2026-08-20</summary>"), 1)
        self.assertEqual(notes.count("via [PR #35"), 1)
        self.assertNotIn("via [PR #36", notes)

    def test_same_day_new_family_merges_into_existing_entry(self):
        previous = {"version": 2, "families": [family("Existing")]}
        current = {
            "version": 2,
            "families": [family("Existing"), family("ZenMaruGothicJP", description="Japanese rounded sans-serif")],
        }
        plan = {
            "new": ["ZenMaruGothicJP"],
            "changedExisting": ["Existing"],
            "remove": [],
        }
        previous_notes = "\n".join(
            [
                "## Catalog update",
                "",
                "This update keeps the stable `sd-fonts-m2-b4` compatibility channel.",
                "",
                "## Changelog",
                "",
                "<details>",
                "<summary>2026-08-20</summary>",
                "",
                "- Update **Existing** — Description (via [PR #35](https://github.com/aBER0724/crosspoint-cjk-fonts/pull/35))",
                "",
                "</details>",
                "",
                "### Installation",
                "",
                "Install me.",
            ]
        )

        notes = self.run_generator(
            previous,
            current,
            plan,
            previous_notes=previous_notes,
            date="2026-08-20",
            pr="36",
        )

        self.assertEqual(notes.count("<summary>2026-08-20</summary>"), 1)
        self.assertIn("Add **ZenMaruGothicJP** — Japanese rounded sans-serif", notes)
        self.assertIn("via [PR #36", notes)
        self.assertLess(notes.index("Add **ZenMaruGothicJP"), notes.index("### Installation"))

    def test_different_day_still_appends_new_entry(self):
        previous = {"version": 2, "families": [family("Existing")]}
        current = {"version": 2, "families": [family("Existing")]}
        plan = {
            "new": [],
            "changedExisting": ["Existing"],
            "remove": [],
        }
        previous_notes = "\n".join(
            [
                "## Catalog update",
                "",
                "This update keeps the stable `sd-fonts-m2-b4` compatibility channel.",
                "",
                "## Changelog",
                "",
                "<details>",
                "<summary>2026-08-19</summary>",
                "",
                "- Update **Existing** — Description",
                "",
                "</details>",
                "",
                "### Installation",
                "",
                "Install me.",
            ]
        )

        notes = self.run_generator(
            previous,
            current,
            plan,
            previous_notes=previous_notes,
            date="2026-08-20",
        )

        self.assertEqual(notes.count("<summary>2026-08-20</summary>"), 1)
        self.assertEqual(notes.count("<summary>2026-08-19</summary>"), 1)
        self.assertLess(notes.index("<summary>2026-08-20</summary>"), notes.index("<summary>2026-08-19</summary>"))


if __name__ == "__main__":
    unittest.main()
