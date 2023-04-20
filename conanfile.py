#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.scm import Git
from conan.tools.files import load, update_conandata, copy, collect_libs
from conan.tools.microsoft.visual import check_min_vs
import os


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
    description =   "Corrade is a multiplatform utility library written \
                    in C++11/C++14. It's used as a base for the Magnum \
                    graphics engine, among other things."
    topics = ("conan", "corrad", "magnum", "filesystem", "console", "environment", "os")
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
        if self.settings.compiler == 'msvc':
            add_cmake_option("MSVC2015_COMPATIBILITY", int(self.settings.compiler.version.value) == 14)
            add_cmake_option("MSVC2017_COMPATIBILITY", int(self.settings.compiler.version.value) == 17)
        
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
        self.output.info("XXX Corrade_ROOT: {}".format(self.package_folder))

    def package_info(self):
        # See dependency order here: https://doc.magnum.graphics/magnum/custom-buildsystems.html
        all_libs = [
            #1
            "CorradeUtility",
            "CorradeContainers",
            #2
            "CorradeInterconnect",
            "CorradePluginManager",
            "CorradeTestSuite",
        ]

        # Sort all built libs according to above, and reverse result for correct link order
        suffix = '-d' if self.settings.build_type == "Debug" else ''
        built_libs = collect_libs(self)
        self.cpp_info.libs = sort_libs(correct_order=all_libs, libs=built_libs, lib_suffix=suffix, reverse_result=True)
