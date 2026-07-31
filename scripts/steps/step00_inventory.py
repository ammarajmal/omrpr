from omrpr_analysis.inventory import build_inventory
from omrpr_analysis.paths import ProjectPaths

if __name__ == "__main__":
    print(build_inventory(ProjectPaths.discover()))
