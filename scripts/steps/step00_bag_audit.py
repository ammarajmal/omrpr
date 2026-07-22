from omrpr_analysis.bag_audit import audit_tree
from omrpr_analysis.paths import ProjectPaths

if __name__ == "__main__":
    paths = ProjectPaths.discover()
    print(audit_tree(paths.raw / "camera/rosbag", paths.interim / "bag-audit/topic_audit.csv"))
