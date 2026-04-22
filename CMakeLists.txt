cmake_minimum_required(VERSION 3.5)
project(mc_robot_description)
find_package(ament_cmake REQUIRED)

# Install launch/asset directories.
install(DIRECTORY
  launch meshes rviz urdfs
  DESTINATION share/${PROJECT_NAME}/
)

# Install scripts so `ros2 run mc_robot_description <script>.py` works.
install(PROGRAMS
  scripts/init_joint_states_once.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()