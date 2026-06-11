## Conan package recipe for Corrade

Corrade is a multiplatform utility library used as a base for the Magnum
graphics engine.

This recipe packages Corrade `2026.dev`, pinned to upstream `mosra/corrade`
`master` commit `120098ebf53487678e352edaa00993956f4c9f06`.

## Conan 2 usage

```bash
conan create .
conan create . -o 'corrade/*:shared=True'
```

Consumer CMake projects can use Corrade's own installed CMake package files:

```cmake
find_package(Corrade REQUIRED Utility)
target_link_libraries(my_target PRIVATE Corrade::Utility)
```

## Options

| Option | Default |
| --- | --- |
| `shared` | `False` |
| `fPIC` | `True` |
| `with_interconnect` | `True` |
| `with_main` | `True` |
| `with_pluginmanager` | `True` |
| `with_rc` | `True` |
| `with_testsuite` | `True` |
| `with_utility` | `True` |
| `build_deprecated` | `True` |
| `build_multithreaded` | `True` |
| `build_static_pic` | `True` |
| `build_static_unique_globals` | `True` |
| `build_static_unique_globals_dll_name` | `None` |
| `build_tests` | `False` |
| `build_cpu_runtime_dispatch` | `False` |
| `build_tests_force_cpu_pointer_dispatch` | `False` |
| `build_tests_force_wasm_simd128` | `False` |
| `cpu_use_ifunc` | `False` |
| `msvc_compatibility` | `False` |
| `msvc2017_compatibility` | `False` |
| `msvc2015_compatibility` | `False` |
| `testsuite_target_xctest` | `False` |
| `utility_use_ansi_colors` | `False` |

The recipe maps these options to Corrade's current `CORRADE_*` CMake cache
variables and uses Corrade's installed `CorradeConfig.cmake` /
`FindCorrade.cmake` files for CMake consumers.

## License

The recipe is MIT licensed. Corrade itself is MIT licensed; see the packaged
`COPYING` file from upstream.
