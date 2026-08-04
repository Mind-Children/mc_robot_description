cmake_minimum_required(VERSION 3.5)
project(mc_robot_description)
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

# Model + visualization assets.
install(DIRECTORY
  urdf meshes launch rviz
  DESTINATION share/${PROJECT_NAME}/
)

# Python helper (get_urdf_path / export_resolved_urdf) — the only sanctioned
# way for consumers to locate the model.
ament_python_install_package(${PROJECT_NAME})

ament_package()
