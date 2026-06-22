"""Git-based oracle versioning for tracking oracle structure changes.

Per design doc section 21.2: oracle versioning with Git.
"""
import json
import os
import subprocess
import hashlib
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class GitVersionControl:
    """Git-based version control for oracle structures."""

    def __init__(self, repo_dir: str = None):
        self.repo_dir = repo_dir or os.path.join(os.getcwd(), "oracle_versions")
        self.available = False

        if not os.path.exists(self.repo_dir):
            os.makedirs(self.repo_dir, exist_ok=True)

        self._init_repo()

    def _init_repo(self):
        """Initialize git repository if not exists."""
        git_dir = os.path.join(self.repo_dir, ".git")
        if not os.path.exists(git_dir):
            try:
                subprocess.run(
                    ["git", "init"],
                    cwd=self.repo_dir,
                    capture_output=True,
                    timeout=10,
                )
                subprocess.run(
                    ["git", "config", "user.email", "oracle@system.local"],
                    cwd=self.repo_dir,
                    capture_output=True,
                    timeout=10,
                )
                subprocess.run(
                    ["git", "config", "user.name", "Oracle System"],
                    cwd=self.repo_dir,
                    capture_output=True,
                    timeout=10,
                )
                self.available = True
                logger.info("Git repo initialized at %s", self.repo_dir)
            except Exception as e:
                logger.warning("Git init failed: %s", e)
        else:
            self.available = True

    def _run_git(self, *args) -> tuple[bool, str]:
        """Run a git command."""
        try:
            result = subprocess.run(
                ["git"] + list(args),
                cwd=self.repo_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)

    def save_oracle_version(
        self,
        oracle_id: str,
        chromosome_data: dict,
        generation: int,
        fitness: float,
        commit_message: str = None,
    ) -> Optional[str]:
        """Save an oracle version as a git commit."""
        if not self.available:
            return None

        version_hash = hashlib.sha256(
            json.dumps(chromosome_data, sort_keys=True).encode()
        ).hexdigest()[:12]

        filename = f"{oracle_id}_v{generation}_{version_hash}.json"
        filepath = os.path.join(self.repo_dir, filename)

        version_data = {
            "oracle_id": oracle_id,
            "version_hash": version_hash,
            "generation": generation,
            "fitness": fitness,
            "chromosome_data": chromosome_data,
            "timestamp": time.time(),
        }

        with open(filepath, "w") as f:
            json.dump(version_data, f, indent=2, default=str)

        self._run_git("add", filename)

        if not commit_message:
            commit_message = (
                f"Oracle {oracle_id} v{generation} "
                f"(fitness={fitness:.4f}, hash={version_hash})"
            )

        success, output = self._run_git("commit", "-m", commit_message)
        if not success:
            logger.warning("Git commit failed: %s", output)
            return None

        success, commit_hash = self._run_git("rev-parse", "HEAD")
        if success:
            commit_hash = commit_hash.strip()
            logger.info("Saved oracle version: %s (commit: %s)", version_hash, commit_hash[:8])
            return commit_hash

        return None

    def get_oracle_versions(self, oracle_id: str) -> list[dict]:
        """Get all versions of an oracle."""
        if not self.available:
            return []

        success, output = self._run_git(
            "log", "--all", "--oneline", "--", f"{oracle_id}_*.json"
        )
        if not success:
            return []

        versions = []
        for line in output.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split(" ", 1)
            if len(parts) == 2:
                commit_hash, message = parts
                versions.append({
                    "commit_hash": commit_hash.strip(),
                    "message": message.strip(),
                })

        return versions

    def get_version_diff(self, commit1: str, commit2: str) -> Optional[str]:
        """Get diff between two versions."""
        if not self.available:
            return None

        success, output = self._run_git("diff", commit1, commit2)
        return output if success else None

    def checkout_version(self, commit_hash: str) -> bool:
        """Checkout a specific version."""
        if not self.available:
            return False

        success, _ = self._run_git("checkout", commit_hash)
        return success

    def get_current_hash(self) -> Optional[str]:
        """Get current HEAD commit hash."""
        if not self.available:
            return None

        success, output = self._run_git("rev-parse", "HEAD")
        return output.strip() if success else None

    def get_stats(self) -> dict:
        """Get version control stats."""
        if not self.available:
            return {"available": False}

        success, output = self._run_git("rev-list", "--count", "HEAD")
        commit_count = int(output.strip()) if success and output.strip().isdigit() else 0

        return {
            "available": True,
            "repo_dir": self.repo_dir,
            "total_commits": commit_count,
        }
