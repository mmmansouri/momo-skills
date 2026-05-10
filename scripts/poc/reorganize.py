"""Reorganize momo-skills into 4 packages via git mv."""
import subprocess
from pathlib import Path

REPO = Path(r"D:\Work\projects\momo-skills")

MOVES = {
    "common-developer":               "development",
    "common-architecture":            "development",
    "common-git":                     "development",
    "common-code-reviewer":           "development",
    "common-java-developer":          "development/backend/java",
    "common-java-jpa":                "development/backend/java",
    "common-java-testing":            "development/backend/java",
    "common-spring-boot-config":      "development/backend/spring",
    "common-rest-api":                "development/backend/spring",
    "common-security":                "development/backend/spring",
    "common-liquibase":               "development/backend/spring",
    "common-typescript":              "development/frontend",
    "common-frontend-angular":        "development/frontend/angular",
    "common-frontend-design":         "development/frontend/angular",
    "common-frontend-testing":        "development/frontend/angular",
    "common-e2e-playwright":          "development/frontend/angular",
    "spec-templates":                 "specification",
    "spec-workflow-feature-planning": "specification",
    "spec-workflow-story-refinement": "specification",
    "skill-creator":                  "ia",
    "initiate-claude":                "ia",
    "pptx":                           "tools",
    "remotion-best-practices":        "tools",
}


def main() -> None:
    for dest in sorted({d for d in MOVES.values()}):
        (REPO / dest).mkdir(parents=True, exist_ok=True)

    for skill, dest in MOVES.items():
        src = REPO / skill
        if not src.exists():
            print(f"SKIP (already moved?): {skill}")
            continue
        subprocess.run(
            ["git", "mv", skill, f"{dest}/{skill}"],
            cwd=REPO, check=True,
        )
        print(f"moved {skill} -> {dest}/{skill}")

    allowed = {"development", "specification", "ia", "tools",
               ".git", ".claude", "scripts"}
    leftover = [p.name for p in REPO.iterdir()
                if p.is_dir() and p.name not in allowed]
    assert not leftover, f"Skills oublies a la racine : {leftover}"
    print(f"OK - {len(MOVES)} skills deplaces, racine propre")


if __name__ == "__main__":
    main()
