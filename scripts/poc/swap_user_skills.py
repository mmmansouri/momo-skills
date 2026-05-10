"""Rename ~/.claude/skills symlink to backup and create empty real dir."""
import os
from pathlib import Path

USER_SKILLS = Path(r"C:\Users\PC\.claude\skills")
BACKUP      = Path(r"C:\Users\PC\.claude\skills-momo-backup")


def main() -> None:
    assert USER_SKILLS.exists(), f"{USER_SKILLS} introuvable"
    assert not BACKUP.exists(),  f"{BACKUP} existe deja - rollback necessaire"
    os.rename(USER_SKILLS, BACKUP)
    USER_SKILLS.mkdir()
    print(f"OK - symlink renomme vers {BACKUP.name}, repertoire vide cree")


if __name__ == "__main__":
    main()
