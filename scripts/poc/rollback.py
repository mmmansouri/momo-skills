"""Rollback: remove empty user-level skills dir, restore symlink, clean POC."""
import os
import shutil
from pathlib import Path

USER_SKILLS = Path(r"C:\Users\PC\.claude\skills")
BACKUP      = Path(r"C:\Users\PC\.claude\skills-momo-backup")
POC         = Path(r"D:\Work\poc-skills-cloisonnement")


def main() -> None:
    if USER_SKILLS.exists() and not USER_SKILLS.is_symlink():
        try:
            USER_SKILLS.rmdir()
            print(f"removed empty {USER_SKILLS}")
        except OSError as e:
            print(f"WARNING: {USER_SKILLS} non vide, abandon : {e}")
            return

    if BACKUP.exists():
        os.rename(BACKUP, USER_SKILLS)
        print(f"restored symlink {USER_SKILLS}")

    if POC.exists():
        shutil.rmtree(POC)
        print(f"removed POC {POC}")


if __name__ == "__main__":
    main()
