#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.scm import Git
from conan.tools.files import load, save, update_conandata, copy, collect_libs
from conan.tools.microsoft.visual import is_msvc, check_min_vs

import os
import textwrap


def sort_libs(correct_order, libs, lib_suffix='', reverse_result=False):
    # Add suffix for correct string matching
    correct_order[:] = [s.__add__(lib_suffix) for s in correct_order]

    result = []
    for expectedLib in correct_order:
        for lib in libs:
            if expectedLib == lib:
                result.append(lib)

    if reverse_result:
        # Linking happens in reversed order
        result.reverse()

    return result


class LibnameConan(ConanFile):
    name = "corrade"
    version = "2020.06"
    description = "Corrade is a multiplatform utility library written \
                    in C++11/C++14. It's used as a base for the Magnum \
                    graphics engine, among other things."
    topics = ("conan", "corrade", "magnum", "filesystem", "console", "environment", "os")
    url = "https://github.com/TUM-CONAN/conan-corrade"
    homepage = "https://magnum.graphics/corrade"
    author = "ulrich eck (forked on github)"
    license = "MIT"
    exports = ["LICENSE.md"]
    exports_sources = ["CMakeLists.txt", "patches/*"]

    # Options may need to change depending on the packaged library.
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False], 
        "fPIC": [True, False],
        "build_deprecated": [True, False],
        "build_multithreaded": [True, False],
        "with_interconnect": [True, False],
        "with_pluginmanager": [True, False],
        "with_rc": [True, False],
        "with_testsuite": [True, False],
        "with_utility": [True, False],
    }

    default_options = {
        "shared": False, 
        "fPIC": True,
        "build_deprecated": True,
        "build_multithreaded": True,
        "with_interconnect": True,
        "with_pluginmanager": True,
        "with_rc": True,
        "with_testsuite": True,
        "with_utility": True,
    }

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def validate(self):
        if self.settings.os == "Windows":
            check_min_vs(self, "141")

    def export(self):
        update_conandata(self, {"sources": {
            "commit": "v{}".format(self.version), 
            "url": "https://github.com/mosra/corrade.git"
            }}
            )

    def source(self):
        git = Git(self)
        sources = self.conan_data["sources"]
        git.clone(url=sources["url"], target=self.source_folder)
        git.checkout(commit=sources["commit"])

    def generate(self):
        tc = CMakeToolchain(self)

        def add_cmake_option(option, value):
            var_name = "{}".format(option).upper()
            value_str = "{}".format(value)
            var_value = "ON" if value_str == 'True' else "OFF" if value_str == 'False' else value_str 
            tc.variables[var_name] = var_value

        for option, value in self.options.items():
            add_cmake_option(option, value)

        # Corrade uses suffix on the resulting 'lib'-folder when running cmake.install()
        # Set it explicitly to empty, else Corrade might set it implicitly (eg. to "64")
        add_cmake_option("LIB_SUFFIX", "")

        add_cmake_option("BUILD_STATIC", not self.options.shared)

        if is_msvc(self):
            if check_min_vs(self, 193, raise_invalid=False):
                tc.variables["MSVC2019_COMPATIBILITY"] = True
            elif check_min_vs(self, 192, raise_invalid=False):
                tc.variables["MSVC2017_COMPATIBILITY"] = True
            elif check_min_vs(self, 191, raise_invalid=False):
                tc.variables["MSVC2015_COMPATIBILITY"] = True
        
        if self.settings.compiler == 'gcc':
            add_cmake_option("GCC47_COMPATIBILITY", float(self.settings.compiler.version.value) < 4.8)

        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def layout(self):
        cmake_layout(self, src_folder="source_subfolder")

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="LICENSE", dst="licenses", src=self.source_folder)
        cmake = CMake(self)
        cmake.install()


    def _register_component(self, component):
        name = component["name"]
        self.cpp_info.components[name].set_property("cmake_target_name", f"Corrade::{name}")
        self.cpp_info.components[name].builddirs.append(self._cmake_folder)
        self.cpp_info.components[name].set_property("pkg_config_name", name)
        self.cpp_info.components[name].libs = [component["lib"]] if component['lib'] is not None else []
        self.cpp_info.components[name].requires = component["requires"]

    @property
    def _cmake_entry_point_file(self):
        return os.path.join("share", "cmake", "Corrade", "conan_corrade_entry_point.cmake")

    @property
    def _cmake_folder(self):
        return os.path.join('share', 'cmake', 'Corrade')

    def package_info(self):

        contents = textwrap.dedent(f"""\
        message(STATUS "Corrade Conan Directory: ${{CMAKE_CURRENT_LIST_DIR}}")
        set(CORRADE_INCLUDE_DIR "${{CMAKE_CURRENT_LIST_DIR}}/../../../include")
        set(CORRADE_MODULE_DIR "${{CMAKE_CURRENT_LIST_DIR}}")

        message(STATUS "Corrade include: ${{CORRADE_INCLUDE_DIR}}")
        message(STATUS "Corrade module: ${{CORRADE_MODULE_DIR}}")

        # Configuration file
        find_file(_CORRADE_CONFIGURE_FILE configure.h
            HINTS ${{CORRADE_INCLUDE_DIR}}/Corrade/)

        # Read flags from configuration
        file(READ ${{_CORRADE_CONFIGURE_FILE}} _corradeConfigure)
        string(REGEX REPLACE ";" "\\\\\\\\;" _corradeConfigure "${{_corradeConfigure}}")
        string(REGEX REPLACE "\\n" ";" _corradeConfigure "${{_corradeConfigure}}")
        set(_corradeFlags
            MSVC2015_COMPATIBILITY
            MSVC2017_COMPATIBILITY
            MSVC_COMPATIBILITY
            BUILD_DEPRECATED
            BUILD_STATIC
            BUILD_STATIC_UNIQUE_GLOBALS
            BUILD_MULTITHREADED
            BUILD_CPU_RUNTIME_DISPATCH
            TARGET_UNIX
            TARGET_APPLE
            TARGET_IOS
            TARGET_IOS_SIMULATOR
            TARGET_WINDOWS
            TARGET_WINDOWS_RT
            TARGET_EMSCRIPTEN
            TARGET_ANDROID
            # TARGET_X86 etc, TARGET_32BIT, TARGET_BIG_ENDIAN and TARGET_LIBCXX etc.
            # are not exposed to CMake as the meaning is unclear on platforms with
            # multi-arch binaries or when mixing different STL implementations.
            # TARGET_GCC etc are figured out via UseCorrade.cmake, as the compiler can
            # be different when compiling the lib & when using it.
            CPU_USE_IFUNC
            PLUGINMANAGER_NO_DYNAMIC_PLUGIN_SUPPORT
            TESTSUITE_TARGET_XCTEST
            UTILITY_USE_ANSI_COLORS)
        foreach(_corradeFlag ${{_corradeFlags}})
            list(FIND _corradeConfigure "#define CORRADE_${{_corradeFlag}}" _corrade_${{_corradeFlag}})
            if(NOT _corrade_${{_corradeFlag}} EQUAL -1)
                set(CORRADE_${{_corradeFlag}} 1)
            endif()
        endforeach()

        set(CORRADE_USE_MODULE ${{_CORRADE_MODULE_DIR}}/UseCorrade.cmake)
        set(CORRADE_LIB_SUFFIX_MODULE ${{_CORRADE_MODULE_DIR}}/CorradeLibSuffix.cmake)

        # find corrade-rc
        if (NOT TARGET Corrade::rc)
          add_executable(Corrade::rc IMPORTED)
        endif()

        find_program(CORRADE_rc_EXECUTABLE corrade-rc HINTS ${{CMAKE_CURRENT_LIST_DIR}}/../../../bin)

        if(CORRADE_rc_EXECUTABLE)
            set_property(TARGET Corrade::rc PROPERTY
                IMPORTED_LOCATION ${{CORRADE_rc_EXECUTABLE}})
        endif()


        #Fixes for Interconnect

        # Disable /OPT:ICF on MSVC, which merges functions with identical
        # contents and thus breaks signal comparison
        if(CORRADE_TARGET_WINDOWS AND CMAKE_CXX_COMPILER_ID STREQUAL "MSVC")
            if(CMAKE_VERSION VERSION_LESS 3.13)
                set_property(TARGET Corrade::Interconnect PROPERTY
                    INTERFACE_LINK_LIBRARIES "-OPT:NOICF,REF")
            else()
                set_property(TARGET Corrade::Interconnect PROPERTY
                    INTERFACE_LINK_OPTIONS "/OPT:NOICF,REF")
            endif()
        endif()

        # Fixes for Utility

        # Top-level include directory
        set_property(TARGET Corrade::Utility APPEND PROPERTY
            INTERFACE_INCLUDE_DIRECTORIES ${{CORRADE_INCLUDE_DIR}})

        # Require (at least) C++11 for users
        set_property(TARGET Corrade::Utility PROPERTY
            INTERFACE_CORRADE_CXX_STANDARD 11)
        set_property(TARGET Corrade::Utility APPEND PROPERTY
            COMPATIBLE_INTERFACE_NUMBER_MAX CORRADE_CXX_STANDARD)

        # Path::libraryLocation() needs this
        if(CORRADE_TARGET_UNIX)
            set_property(TARGET Corrade::Utility APPEND PROPERTY
                INTERFACE_LINK_LIBRARIES ${{CMAKE_DL_LIBS}})
        endif()
        # AndroidLogStreamBuffer class needs to be linked to log library
        if(CORRADE_TARGET_ANDROID)
            set_property(TARGET Corrade::Utility APPEND PROPERTY
                INTERFACE_LINK_LIBRARIES "log")
        endif()
        """)

        corradeentry = os.path.join(self.package_folder, self._cmake_entry_point_file)
        save(self, corradeentry, contents)


        self.cpp_info.set_property("cmake_file_name", "Corrade")
        corrademacros = os.path.join(self._cmake_folder, 'UseCorrade.cmake')
        self.cpp_info.set_property("cmake_build_modules", [corradeentry, corrademacros])

        suffix = '-d' if self.settings.build_type == "Debug" else ''

        components = [
            {"name": "Utility", "lib": "CorradeUtility" + suffix, "requires": []},
            {"name": "Containers", "lib": None, "requires": ["Utility"]},
            {"name": "Interconnect", "lib": "CorradeInterconnect" + suffix, "requires": ["Utility"]},
            {"name": "PluginManager", "lib": "CorradePluginManager" + suffix, "requires": ["Utility"]},
            {"name": "TestSuite", "lib": "CorradeTestSuite" + suffix, "requires": ["Utility"]},
        ]

        for component in components:
            self._register_component(component)


        # # See dependency order here: https://doc.magnum.graphics/magnum/custom-buildsystems.html
        # all_libs = [
        #     #1
        #     "CorradeUtility",
        #     "CorradeContainers",
        #     #2
        #     "CorradeInterconnect",
        #     "CorradePluginManager",
        #     "CorradeTestSuite",
        # ]

        # # Sort all built libs according to above, and reverse result for correct link order
        # suffix = '-d' if self.settings.build_type == "Debug" else ''
        # built_libs = collect_libs(self)
        # self.cpp_info.libs = sort_libs(correct_order=all_libs, libs=built_libs, lib_suffix=suffix, reverse_result=True)
