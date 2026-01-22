docker build -f Dockerfile -t mindchildren/mc_robot_description:v0.1 \
  --build-arg BASE_IMAGE=ros:jazzy-ros-base-noble \
  --progress=plain --network=host .