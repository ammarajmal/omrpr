# Environment

`01_bootstrap_or_update.sh` tries Python 3.14.6 first and falls back to 3.13.14
only if the latest scientific dependency set cannot resolve. `uv.lock` is
created on the target workstation. `02_upgrade_dependencies.sh` refreshes all
compatible dependencies. The official AprilTag source is never vendored here;
it is fetched from AprilRobotics and checked out at verified release v3.4.5.
