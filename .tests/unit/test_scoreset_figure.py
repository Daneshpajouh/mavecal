"""
Rule test code for unit testing of rules generated with Snakemake 9.27.0.
"""

import os
import sys
import shutil
import tempfile
from pathlib import Path
from subprocess import check_output

sys.path.insert(0, os.path.dirname(__file__))


def test_scoreset_figure(conda_prefix):

    with tempfile.TemporaryDirectory() as tmpdir:
        workdir = Path(tmpdir) / "workdir"
        config_path = Path(".tests/unit/scoreset_figure/config")
        data_path = Path(".tests/unit/scoreset_figure/data")
        expected_path = Path(".tests/unit/scoreset_figure/expected")

        # Copy config to the temporary workdir.
        shutil.copytree(config_path, workdir)

        # Copy data to the temporary workdir.
        shutil.copytree(data_path, workdir, dirs_exist_ok=True)

        # The test configuration and the fixtures it points to are read at parse time.
        shutil.copytree(".tests/integration/config", workdir / ".tests/integration/config", dirs_exist_ok=True)
        shutil.copytree(
            "tests/data",
            workdir / "tests/data",
            dirs_exist_ok=True,
            copy_function=lambda s, d: d if os.path.exists(d) else shutil.copy2(s, d),
        )

        # Run the test job.
        check_output(
            [
                sys.executable,
                "-m",
                "snakemake",
                ".tests/integration/results/figures/toy_tp53.png",
                ".tests/integration/results/figures/toy_tp53.svg",
                "--snakefile",
                "workflow/Snakefile",
                "-f",
                "--notemp",
                "--show-failed-logs",
                "-j1",
                # macOS: the benchmark sampler can fail on short jobs (see profiles/local).
                "--retries",
                "2",
                "--target-files-omit-workdir-adjustment",
                "--allowed-rules",
                "scoreset_figure",
                "--configfile",
                ".tests/integration/config/config.yaml",
                "--directory",
                workdir,
            ]
            + conda_prefix
        )

        # Check the output byte by byte using cmp/zmp/bzcmp/xzcmp.
        # To modify this behavior, you can inherit from common.OutputChecker in here
        # and overwrite the method `compare_files(generated_file, expected_file),
        # also see common.py.
        import common
        common.OutputChecker(data_path, expected_path, workdir).check()
