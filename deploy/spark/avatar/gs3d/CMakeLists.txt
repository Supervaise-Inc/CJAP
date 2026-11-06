# Replaces grid-sample3d-trt-plugin's CMakeLists.txt (SeanWangJS @ f964750) for the
# DGX Spark: GB10 = sm_121, TensorRT from NVIDIA's apt packages, no test target.
# Same changes the Spark port blog made (mikihands, 2026-03-03).
cmake_minimum_required(VERSION 3.18)
project(grid_sample_3d_plugin LANGUAGES CXX CUDA)
set(CMAKE_CXX_STANDARD 17)
find_package(CUDAToolkit REQUIRED)

set(TensorRT_INCLUDE_DIR "/usr/include/aarch64-linux-gnu" CACHE PATH "TensorRT headers")
set(TensorRT_LIB_DIR "/usr/lib/aarch64-linux-gnu" CACHE PATH "TensorRT libraries")

file(GLOB SOURCES "./src/*.cpp")
file(GLOB CU_SOURCE "./src/*.cu")
add_library(${PROJECT_NAME} SHARED ${SOURCES} ${CU_SOURCE})
target_include_directories(${PROJECT_NAME} PRIVATE "./src" ${CUDAToolkit_INCLUDE_DIRS}
                           ${TensorRT_INCLUDE_DIR})
target_link_directories(${PROJECT_NAME} PRIVATE ${TensorRT_LIB_DIR})
target_link_libraries(${PROJECT_NAME} PRIVATE nvinfer CUDA::cudart)
set_target_properties(${PROJECT_NAME} PROPERTIES CUDA_ARCHITECTURES "121")
