"""Create POC app with 2 Windows junctions to target momo-skills."""
import subprocess
from pathlib import Path

POC    = Path(r"D:\Work\poc-skills-cloisonnement")
SKILLS = POC / ".claude" / "skills"
MOMO   = Path(r"D:\Work\projects\momo-skills")

JUNCTIONS = {
    "common-java-developer":     MOMO / "development" / "backend" / "java"   / "common-java-developer",
    "common-spring-boot-config": MOMO / "development" / "backend" / "spring" / "common-spring-boot-config",
}

CLAUDE_MD = (
    "# POC App - Cloisonnement skills\n\n"
    "Application de test.\n"
    "Skills attendus visibles : common-java-developer, common-spring-boot-config.\n"
)


def main() -> None:
    SKILLS.mkdir(parents=True, exist_ok=True)
    for name, target in JUNCTIONS.items():
        link = SKILLS / name
        assert target.exists(), f"Cible inexistante : {target}"
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            check=True,
        )
        print(f"junction {link.name} -> {target}")
    (POC / "CLAUDE.md").write_text(CLAUDE_MD, encoding="utf-8")
    print(f"OK - POC cree a {POC}")


if __name__ == "__main__":
    main()
