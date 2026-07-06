#!/usr/bin/env python3
"""Tests for the common-git safety scripts.

Covers git_utils.py (shared module) and the CLI scripts git_safe_push.py,
git_status_report.py, git_cleanup_branches.py. Uses temporary git repos.

Moved from buy-nature-ai (2026-07-06): the suite lives with its owner.
Project-specific scripts (bn_safe_commit.py, github_auth.py) are tested in
the buy-nature-ai repo.
"""
import json
import os
import shutil
import stat
import sys
import tempfile
import unittest


def _force_remove_readonly(func, path, exc_info):
    """Handle Windows read-only files during rmtree (e.g., .git/objects)."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

# Add git scripts to path
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
MOMO_DIR = os.path.dirname(TESTS_DIR)
GIT_SCRIPTS = os.path.join(MOMO_DIR, "development", "common-git", "scripts")

sys.path.insert(0, GIT_SCRIPTS)


class TestIsProtectedBranch(unittest.TestCase):
    """Test is_protected_branch() in git_utils.py."""

    def test_develop_is_protected(self):
        from git_utils import is_protected_branch
        self.assertTrue(is_protected_branch("develop"))

    def test_main_is_protected(self):
        from git_utils import is_protected_branch
        self.assertTrue(is_protected_branch("main"))

    def test_master_is_protected(self):
        from git_utils import is_protected_branch
        self.assertTrue(is_protected_branch("master"))

    def test_release_branch_is_protected(self):
        from git_utils import is_protected_branch
        self.assertTrue(is_protected_branch("release/v1.0.0"))

    def test_custom_base_branch_is_protected(self):
        from git_utils import is_protected_branch
        self.assertTrue(is_protected_branch("integration", base_branch="integration"))

    def test_feature_branch_not_protected(self):
        from git_utils import is_protected_branch
        self.assertFalse(is_protected_branch("feature/TICKET-123-add-cart"))

    def test_bugfix_branch_not_protected(self):
        from git_utils import is_protected_branch
        self.assertFalse(is_protected_branch("bugfix/TICKET-456-fix-total"))


class TestValidateBranchName(unittest.TestCase):
    """Test validate_branch_name() in git_utils.py.

    The Jira prefix comes from the JIRA_PREFIX env var (default: TICKET).
    """

    def setUp(self):
        # Make each test independent of the ambient environment.
        self._saved_prefix = os.environ.pop("JIRA_PREFIX", None)

    def tearDown(self):
        if self._saved_prefix is not None:
            os.environ["JIRA_PREFIX"] = self._saved_prefix
        else:
            os.environ.pop("JIRA_PREFIX", None)

    def test_valid_feature_branch(self):
        from git_utils import validate_branch_name
        valid, error = validate_branch_name("feature/TICKET-123-add-checkout")
        self.assertTrue(valid)
        self.assertEqual(error, "")

    def test_valid_bugfix_branch(self):
        from git_utils import validate_branch_name
        valid, error = validate_branch_name("bugfix/TICKET-456-fix-total")
        self.assertTrue(valid)
        self.assertEqual(error, "")

    def test_valid_hotfix_branch(self):
        from git_utils import validate_branch_name
        valid, error = validate_branch_name("hotfix/TICKET-789-critical-fix")
        self.assertTrue(valid)
        self.assertEqual(error, "")

    def test_valid_release_branch(self):
        from git_utils import validate_branch_name
        valid, error = validate_branch_name("release/v1.2.3")
        self.assertTrue(valid)
        self.assertEqual(error, "")

    def test_valid_branch_without_description(self):
        from git_utils import validate_branch_name
        valid, error = validate_branch_name("feature/TICKET-123")
        self.assertTrue(valid)
        self.assertEqual(error, "")

    def test_env_prefix_override(self):
        from git_utils import validate_branch_name
        os.environ["JIRA_PREFIX"] = "BNAT"
        valid, error = validate_branch_name("feature/BNAT-123-add-checkout")
        self.assertTrue(valid)
        # The default prefix no longer matches once overridden.
        valid, error = validate_branch_name("feature/TICKET-123-add-checkout")
        self.assertFalse(valid)

    def test_env_prefix_comma_separated(self):
        from git_utils import validate_branch_name
        os.environ["JIRA_PREFIX"] = "PROJ,TICKET"
        self.assertTrue(validate_branch_name("feature/PROJ-1-x")[0])
        self.assertTrue(validate_branch_name("feature/TICKET-2-y")[0])

    def test_invalid_no_prefix(self):
        from git_utils import validate_branch_name
        valid, error = validate_branch_name("TICKET-123-add-cart")
        self.assertFalse(valid)
        self.assertIn("Invalid branch name", error)

    def test_invalid_wrong_prefix(self):
        from git_utils import validate_branch_name
        valid, error = validate_branch_name("fix/TICKET-123-bug")
        self.assertFalse(valid)

    def test_invalid_no_ticket(self):
        from git_utils import validate_branch_name
        valid, error = validate_branch_name("feature/add-cart")
        self.assertFalse(valid)

    def test_invalid_uppercase_description(self):
        from git_utils import validate_branch_name
        valid, error = validate_branch_name("feature/TICKET-123-AddCart")
        self.assertFalse(valid)


class TestScanForPatterns(unittest.TestCase):
    """Test scan_for_patterns() in git_utils.py."""

    def test_detect_console_log(self):
        from git_utils import scan_for_patterns, DEBUG_PATTERNS
        content = "const x = 1;\nconsole.log('debug');\nreturn x;"
        hits = scan_for_patterns(content, DEBUG_PATTERNS)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0][0], 2)  # line 2
        self.assertIn("console.log", hits[0][2])

    def test_detect_system_out(self):
        from git_utils import scan_for_patterns, DEBUG_PATTERNS
        content = "System.out.println(\"test\");"
        hits = scan_for_patterns(content, DEBUG_PATTERNS)
        self.assertTrue(any("System.out" in h[2] for h in hits))

    def test_detect_debugger(self):
        from git_utils import scan_for_patterns, DEBUG_PATTERNS
        content = "function test() {\n  debugger\n  return 1;\n}"
        hits = scan_for_patterns(content, DEBUG_PATTERNS)
        self.assertTrue(any("debugger" in h[2] for h in hits))

    def test_detect_hardcoded_secret(self):
        from git_utils import scan_for_patterns, SECRET_PATTERNS
        content = 'password = "my-secret-password"'
        hits = scan_for_patterns(content, SECRET_PATTERNS)
        self.assertTrue(any("secret" in h[2].lower() for h in hits))

    def test_detect_private_key(self):
        from git_utils import scan_for_patterns, SECRET_PATTERNS
        content = "-----BEGIN RSA PRIVATE KEY-----"
        hits = scan_for_patterns(content, SECRET_PATTERNS)
        self.assertTrue(any("Private key" in h[2] for h in hits))

    def test_detect_github_token(self):
        from git_utils import scan_for_patterns, SECRET_PATTERNS
        content = 'token = ghp_1234567890abcdef1234567890abcdef12'
        hits = scan_for_patterns(content, SECRET_PATTERNS)
        self.assertTrue(any("GitHub" in h[2] for h in hits))

    def test_clean_code_no_matches(self):
        from git_utils import scan_for_patterns, DEBUG_PATTERNS, SECRET_PATTERNS
        content = "const total = price * quantity;\nreturn total;"
        debug_hits = scan_for_patterns(content, DEBUG_PATTERNS)
        secret_hits = scan_for_patterns(content, SECRET_PATTERNS)
        self.assertEqual(len(debug_hits), 0)
        self.assertEqual(len(secret_hits), 0)

    def test_multiple_patterns_same_line(self):
        from git_utils import scan_for_patterns, SECRET_PATTERNS
        content = 'password = "test"; token = ghp_abc123def456'
        hits = scan_for_patterns(content, SECRET_PATTERNS)
        self.assertGreaterEqual(len(hits), 2)


class TestFindRepos(unittest.TestCase):
    """Test find_repos() in git_utils.py."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_find_repos_with_git_dirs(self):
        from git_utils import find_repos
        # Create fake git repos
        for name in ["repo-a", "repo-b", "not-a-repo"]:
            os.makedirs(os.path.join(self.tmpdir, name))
        os.makedirs(os.path.join(self.tmpdir, "repo-a", ".git"))
        os.makedirs(os.path.join(self.tmpdir, "repo-b", ".git"))

        repos = find_repos(self.tmpdir)
        self.assertEqual(len(repos), 2)
        repo_names = [os.path.basename(r) for r in repos]
        self.assertIn("repo-a", repo_names)
        self.assertIn("repo-b", repo_names)

    def test_find_repos_empty_dir(self):
        from git_utils import find_repos
        repos = find_repos(self.tmpdir)
        self.assertEqual(len(repos), 0)

    def test_find_repos_nonexistent_dir(self):
        from git_utils import find_repos
        repos = find_repos(os.path.join(self.tmpdir, "nonexistent"))
        self.assertEqual(len(repos), 0)

    def test_find_repos_sorted(self):
        from git_utils import find_repos
        for name in ["zebra", "alpha", "middle"]:
            os.makedirs(os.path.join(self.tmpdir, name, ".git"))
        repos = find_repos(self.tmpdir)
        names = [os.path.basename(r) for r in repos]
        self.assertEqual(names, ["alpha", "middle", "zebra"])


class TestRunGit(unittest.TestCase):
    """Test run_git() with real git commands in temp repo."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Init a real git repo
        import subprocess
        subprocess.run(["git", "init", self.tmpdir], capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"],
                        cwd=self.tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"],
                        cwd=self.tmpdir, capture_output=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, onexc=_force_remove_readonly)

    def test_run_git_success(self):
        from git_utils import run_git
        code, output = run_git("status", cwd=self.tmpdir)
        self.assertEqual(code, 0)

    def test_run_git_failure(self):
        from git_utils import run_git
        code, output = run_git("log", cwd=self.tmpdir)  # empty repo has no log
        self.assertNotEqual(code, 0)

    def test_get_current_branch(self):
        from git_utils import get_current_branch, run_git
        # Create initial commit to have a branch
        test_file = os.path.join(self.tmpdir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")
        run_git("add", ".", cwd=self.tmpdir)
        run_git("commit", "-m", "initial", cwd=self.tmpdir)

        branch = get_current_branch(self.tmpdir)
        self.assertIn(branch, ["main", "master"])  # depends on git config


class TestOutputJson(unittest.TestCase):
    """Test output_json() produces valid JSON."""

    def test_output_is_valid_json(self):
        from git_utils import output_json
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            output_json({"status": "success", "count": 42})

        parsed = json.loads(buf.getvalue())
        self.assertEqual(parsed["status"], "success")
        self.assertEqual(parsed["count"], 42)


class TestGetRepoStatus(unittest.TestCase):
    """Test get_repo_status() in git_status_report.py."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        import subprocess
        subprocess.run(["git", "init", self.tmpdir], capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"],
                        cwd=self.tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"],
                        cwd=self.tmpdir, capture_output=True)
        # Create initial commit on develop
        test_file = os.path.join(self.tmpdir, "README.md")
        with open(test_file, "w") as f:
            f.write("# Test\n")
        subprocess.run(["git", "add", "."], cwd=self.tmpdir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=self.tmpdir, capture_output=True)
        # Create develop branch
        subprocess.run(["git", "checkout", "-b", "develop"], cwd=self.tmpdir, capture_output=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, onexc=_force_remove_readonly)

    def test_clean_repo(self):
        from git_status_report import get_repo_status
        report = get_repo_status(self.tmpdir, "develop")
        self.assertEqual(report["branch"], "develop")
        self.assertEqual(report["status"], "clean")
        self.assertEqual(report["changes"]["staged"], 0)
        self.assertEqual(report["changes"]["unstaged"], 0)
        self.assertEqual(report["changes"]["untracked"], 0)

    def test_dirty_repo(self):
        from git_status_report import get_repo_status
        # Create untracked file
        with open(os.path.join(self.tmpdir, "new_file.txt"), "w") as f:
            f.write("untracked")
        report = get_repo_status(self.tmpdir, "develop")
        self.assertEqual(report["status"], "dirty")
        self.assertGreater(report["changes"]["untracked"], 0)

    def test_not_a_repo(self):
        from git_status_report import get_repo_status
        tmpdir2 = tempfile.mkdtemp()
        try:
            report = get_repo_status(tmpdir2, "develop")
            self.assertEqual(report["status"], "error")
        finally:
            shutil.rmtree(tmpdir2)


class TestGetMergedBranches(unittest.TestCase):
    """Test get_merged_branches() in git_cleanup_branches.py."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        import subprocess
        subprocess.run(["git", "init", self.tmpdir], capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"],
                        cwd=self.tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"],
                        cwd=self.tmpdir, capture_output=True)
        # Initial commit
        with open(os.path.join(self.tmpdir, "README.md"), "w") as f:
            f.write("# Test\n")
        subprocess.run(["git", "add", "."], cwd=self.tmpdir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=self.tmpdir, capture_output=True)
        # Create develop
        subprocess.run(["git", "checkout", "-b", "develop"], cwd=self.tmpdir, capture_output=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, onexc=_force_remove_readonly)

    def test_no_merged_branches(self):
        from git_cleanup_branches import get_merged_branches
        branches = get_merged_branches(self.tmpdir, "develop")
        self.assertEqual(len(branches), 0)

    def test_finds_merged_feature_branch(self):
        import subprocess
        from git_cleanup_branches import get_merged_branches
        # Create a feature branch and merge it
        subprocess.run(["git", "checkout", "-b", "feature/TICKET-1-test"],
                        cwd=self.tmpdir, capture_output=True)
        with open(os.path.join(self.tmpdir, "feature.txt"), "w") as f:
            f.write("feature")
        subprocess.run(["git", "add", "."], cwd=self.tmpdir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "feature"], cwd=self.tmpdir, capture_output=True)
        subprocess.run(["git", "checkout", "develop"], cwd=self.tmpdir, capture_output=True)
        subprocess.run(["git", "merge", "feature/TICKET-1-test"],
                        cwd=self.tmpdir, capture_output=True)

        branches = get_merged_branches(self.tmpdir, "develop")
        self.assertIn("feature/TICKET-1-test", branches)

    def test_excludes_protected_branches(self):
        from git_cleanup_branches import get_merged_branches
        # develop/main/master should never appear even if merged
        branches = get_merged_branches(self.tmpdir, "develop")
        for b in branches:
            self.assertNotIn(b, ["develop", "main", "master"])


class TestGitSafePushArgParsing(unittest.TestCase):
    """Test git_safe_push.py argument handling."""

    def test_push_outside_repo_fails(self):
        import subprocess
        tmpdir = tempfile.mkdtemp()
        try:
            result = subprocess.run(
                [sys.executable, os.path.join(GIT_SCRIPTS, "git_safe_push.py"),
                 "--repo", tmpdir],
                capture_output=True, text=True,
            )
            data = json.loads(result.stdout)
            self.assertEqual(data["status"], "error")
        finally:
            shutil.rmtree(tmpdir)


if __name__ == "__main__":
    unittest.main()
