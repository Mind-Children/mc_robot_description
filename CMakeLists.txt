cmake_minimum_required(VERSION 3.5)
project(mc_robot_description)
find_package(ament_cmake REQUIRED)

# Install launch files.
install(DIRECTORY
  launch meshes rviz urdfs
  DESTINATION share/${PROJECT_NAME}/
)

ament_package()