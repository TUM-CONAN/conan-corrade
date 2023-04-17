cmake_minimum_required(VERSION 3.15)
project(test_package CXX)

set(CMAKE_VERBOSE_MAKEFILE TRUE)

find_package(corrade CONFIG REQUIRED)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} corrade::corrade)

set_target_properties(${PROJECT_NAME} 
    PROPERTIES 
    	CXX_STANDARD 11
    	CXX_STANDARD_REQUIRED ON
    	CXX_EXTENSIONS OFF
)