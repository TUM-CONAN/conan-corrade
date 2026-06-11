from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd, cross_building
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import collect_libs, copy, rmdir
from conan.tools.microsoft import check_min_vs, is_msvc
from conan.tools.scm import Git

import os


required_conan_version = ">=2.0"


class CorradeConan(ConanFile):
    name = "corrade"
    version = "2026.dev"
    description = (
        "Corrade is a multiplatform utility library used as a base for the "
        "Magnum graphics engine."
    )
    topics = ("corrade", "magnum", "filesystem", "console", "utility", "plugin")
    url = "https://github.com/TUM-CONAN/conan-corrade"
    homepage = "https://magnum.graphics/corrade"
    license = "MIT"
    package_type = "library"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_interconnect": [True, False],
        "with_main": [True, False],
        "with_pluginmanager": [True, False],
        "with_rc": [True, False],
        "with_testsuite": [True, False],
        "with_utility": [True, False],
        "build_deprecated": [True, False],
        "build_multithreaded": [True, False],
        "build_static_pic": [True, False],
        "build_static_unique_globals": [True, False],
        "build_static_unique_globals_dll_name": [None, "ANY"],
        "build_tests": [True, False],
        "build_cpu_runtime_dispatch": [True, False],
        "build_tests_force_cpu_pointer_dispatch": [True, False],
        "build_tests_force_wasm_simd128": [True, False],
        "cpu_use_ifunc": [True, False],
        "msvc_compatibility": [True, False],
        "msvc2017_compatibility": [True, False],
        "msvc2015_compatibility": [True, False],
        "testsuite_target_xctest": [True, False],
        "utility_use_ansi_colors": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_interconnect": True,
        "with_main": True,
        "with_pluginmanager": True,
        "with_rc": True,
        "with_testsuite": True,
        "with_utility": True,
        "build_deprecated": True,
        "build_multithreaded": True,
        "build_static_pic": True,
        "build_static_unique_globals": True,
        "build_static_unique_globals_dll_name": None,
        "build_tests": False,
        "build_cpu_runtime_dispatch": False,
        "build_tests_force_cpu_pointer_dispatch": False,
        "build_tests_force_wasm_simd128": False,
        "cpu_use_ifunc": False,
        "msvc_compatibility": False,
        "msvc2017_compatibility": False,
        "msvc2015_compatibility": False,
        "testsuite_target_xctest": False,
        "utility_use_ansi_colors": False,
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, "11")
        if is_msvc(self):
            check_min_vs(self, 190)
        if self.settings.os == "Windows" and self.options.shared and self.options.with_main:
            self.output.info("Corrade::Main is always a static component on Windows.")
        if self.options.with_interconnect and not self.options.with_utility:
            raise ConanInvalidConfiguration("with_interconnect requires with_utility")
        if self.options.with_pluginmanager and not self.options.with_utility:
            raise ConanInvalidConfiguration("with_pluginmanager requires with_utility")
        if self.options.with_testsuite and not self.options.with_utility:
            raise ConanInvalidConfiguration("with_testsuite requires with_utility")
        if self.options.with_utility and not self.options.with_rc and not cross_building(self):
            raise ConanInvalidConfiguration("with_utility requires with_rc for native builds")
        if not self.options.build_tests and (
            self.options.build_tests_force_cpu_pointer_dispatch or self.options.build_tests_force_wasm_simd128
        ):
            raise ConanInvalidConfiguration("test-only dispatch options require build_tests=True")
        if self.options.cpu_use_ifunc and self.settings.os in ("Windows", "Macos", "iOS", "watchOS", "tvOS"):
            raise ConanInvalidConfiguration("cpu_use_ifunc is supported only on suitable ELF platforms")
        if self.options.utility_use_ansi_colors and self.settings.os != "Windows":
            raise ConanInvalidConfiguration("utility_use_ansi_colors is a Windows-only option")
        if self.options.testsuite_target_xctest and self.settings.os != "Macos":
            raise ConanInvalidConfiguration("testsuite_target_xctest is a macOS-only option")
        if (
            self.options.build_static_unique_globals_dll_name
            and (self.settings.os != "Windows" or self.options.shared)
        ):
            raise ConanInvalidConfiguration(
                "build_static_unique_globals_dll_name is only meaningful for static Windows builds"
            )
        if not is_msvc(self) and (
            self.options.msvc_compatibility
            or self.options.msvc2017_compatibility
            or self.options.msvc2015_compatibility
        ):
            raise ConanInvalidConfiguration("MSVC compatibility options require an MSVC compiler")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        source = self.conan_data["sources"][str(self.version)]
        git = Git(self)
        git.clone(url=source["url"], target=".")
        git.checkout(commit=source["commit"])

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["LIB_SUFFIX"] = ""
        tc.variables["CORRADE_BUILD_STATIC"] = not self.options.shared
        tc.variables["CORRADE_BUILD_STATIC_PIC"] = (
            False
            if self.options.shared
            else (
                self.options.get_safe("fPIC", self.options.build_static_pic)
                and self.options.build_static_pic
            )
        )
        tc.variables["CORRADE_BUILD_STATIC_UNIQUE_GLOBALS"] = (
            False if self.options.shared else self.options.build_static_unique_globals
        )

        for option in (
            "with_interconnect",
            "with_main",
            "with_pluginmanager",
            "with_rc",
            "with_testsuite",
            "with_utility",
            "build_deprecated",
            "build_multithreaded",
            "build_tests",
            "build_cpu_runtime_dispatch",
            "build_tests_force_cpu_pointer_dispatch",
            "build_tests_force_wasm_simd128",
            "cpu_use_ifunc",
            "msvc_compatibility",
            "msvc2017_compatibility",
            "msvc2015_compatibility",
            "testsuite_target_xctest",
            "utility_use_ansi_colors",
        ):
            tc.variables[f"CORRADE_{option.upper()}"] = getattr(self.options, option)

        if self.options.build_static_unique_globals_dll_name:
            tc.variables["CORRADE_BUILD_STATIC_UNIQUE_GLOBALS_DLL_NAME"] = (
                self.options.build_static_unique_globals_dll_name
            )

        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "none")
        self.cpp_info.set_property("cmake_file_name", "Corrade")
        self.cpp_info.builddirs = [os.path.join("share", "cmake", "Corrade")]
        self.cpp_info.includedirs = ["include"]
        self.cpp_info.libs = collect_libs(self)

        bindir = os.path.join(self.package_folder, "bin")
        self.buildenv_info.prepend_path("PATH", bindir)
        self.runenv_info.prepend_path("PATH", bindir)
