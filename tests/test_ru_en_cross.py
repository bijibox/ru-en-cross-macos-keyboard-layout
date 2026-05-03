import filecmp
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import ru_en_cross


def assert_trees_identical(testcase: unittest.TestCase, expected: Path, actual: Path) -> None:
    comparison = filecmp.dircmp(expected, actual)
    testcase.assertEqual(comparison.left_only, [], "missing from generated bundle")
    testcase.assertEqual(comparison.right_only, [], "extra files in generated bundle")
    testcase.assertEqual(comparison.funny_files, [], "uncomparable files in generated bundle")

    for name in comparison.common_files:
        expected_file = expected / name
        actual_file = actual / name
        testcase.assertTrue(
            filecmp.cmp(expected_file, actual_file, shallow=False),
            f"file differs: {actual_file.relative_to(actual)}",
        )
        testcase.assertEqual(
            os.stat(expected_file).st_mode & 0o777,
            os.stat(actual_file).st_mode & 0o777,
            f"mode differs: {actual_file.relative_to(actual)}",
        )

    for name in comparison.common_dirs:
        assert_trees_identical(testcase, expected / name, actual / name)


class BuildTests(unittest.TestCase):
    def test_build_bundle_matches_reference(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            bundle = ru_en_cross.build_bundle(output_dir)

            self.assertEqual(bundle, output_dir.resolve() / ru_en_cross.BUNDLE_NAME)
            assert_trees_identical(self, ru_en_cross.ORIGINAL_BUNDLE, bundle)

    def test_cli_build_matches_reference(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            result = subprocess.run(
                [sys.executable, str(ROOT / "ru_en_cross.py"), "build", str(output_dir)],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                Path(result.stdout.strip()),
                output_dir.resolve() / ru_en_cross.BUNDLE_NAME,
            )
            assert_trees_identical(
                self,
                ru_en_cross.ORIGINAL_BUNDLE,
                output_dir / ru_en_cross.BUNDLE_NAME,
            )

    def test_build_refuses_to_overwrite_reference(self):
        with self.assertRaises(ValueError):
            ru_en_cross.build_bundle(ru_en_cross.ORIGINAL_BUNDLE.parent)


if __name__ == "__main__":
    unittest.main()
