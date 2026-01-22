#!/bin/bash
set -e

if [ -z "${DISPLAY}" ]; then
    echo "DISPLAY is not set"
    exit 1
fi

XAUTH="${XAUTHORITY:-$HOME/.Xauthority}"
if [ ! -f "$XAUTH" ]; then
    echo "Xauthority file not found: $XAUTH"
    exit 1
fi

# -------------------------
# Args
# -------------------------
USE_JSP="false"
EXTRA_LAUNCH_ARGS=()

print_usage() {
  cat <<EOF
Usage:
  ./run_rviz.sh [--jsp] [--jsp=true|false] [--] [extra ros2 launch args...]

Examples:
  ./run_rviz.sh
  ./run_rviz.sh --jsp
  ./run_rviz.sh --jsp=true
  ./run_rviz.sh --jsp=false
  ./run_rviz.sh -- use_joint_state_publisher_gui:=true
  ./run_rviz.sh --jsp -- rviz_config:=/context/rviz/animation.rviz
EOF
}

parse_bool() {
  case "$1" in
    true|True|TRUE|1|yes|YES|y|Y) echo "true" ;;
    false|False|FALSE|0|no|NO|n|N) echo "false" ;;
    *)
      echo "Invalid boolean: $1" >&2
      exit 2
      ;;
  esac
}

while [ $# -gt 0 ]; do
  case "$1" in
    --jsp)
      USE_JSP="true"
      shift
      ;;
    --jsp=*)
      USE_JSP="$(parse_bool "${1#*=}")"
      shift
      ;;
    -h|--help)
      print_usage
      exit 0
      ;;
    --)
      shift
      EXTRA_LAUNCH_ARGS+=("$@")
      break
      ;;
    *)
      # allow passing ros2 launch args directly
      EXTRA_LAUNCH_ARGS+=("$1")
      shift
      ;;
  esac
done

# Prevent duplicate use_joint_state_publisher_gui args
HAS_JSP_ARG="false"
for a in "${EXTRA_LAUNCH_ARGS[@]}"; do
  if [[ "$a" == use_joint_state_publisher_gui:=* ]]; then
    HAS_JSP_ARG="true"
    break
  fi
done

LAUNCH_ARGS=()
if [ "$HAS_JSP_ARG" != "true" ]; then
  LAUNCH_ARGS+=("use_joint_state_publisher_gui:=${USE_JSP}")
fi
LAUNCH_ARGS+=("${EXTRA_LAUNCH_ARGS[@]}")

docker run --rm -it \
  --network host \
  -v "$(pwd)":/context \
  -e DISPLAY="$DISPLAY" \
  -e XAUTHORITY=/root/.Xauthority \
  -v "$XAUTH":/root/.Xauthority:ro \
  -e QT_X11_NO_MITSHM=1 \
  mindchildren/mc_robot_description:v0.1 \
  ros2 launch mc_robot_description rviz_current.launch.py "${LAUNCH_ARGS[@]}"
