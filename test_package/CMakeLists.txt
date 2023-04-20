cmake_minimum_required(VERSION 3.15)
cmake_policy(SET CMP0074 NEW)

project(test_package CXX)
set(CMAKE_VERBOSE_MAKEFILE TRUE)

set(CMAKE_MODULE_PATH "${Corrade_ROOT}/share/cmake/Corrade" ${CMAKE_MODULE_PATH})

find_package(Corrade REQUIRED Utility)
set_directory_properties(PROPERTIES CORRADE_USE_PEDANTIC_FLAGS ON)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} PRIVATE Corrade::Utility)

set_target_properties(${PROJECT_NAME} 
    PROPERTIES 
    	CXX_STANDARD 11
    	CXX_STANDARD_REQUIRED ON
    	CXX_EXTENSIONS OFF
)