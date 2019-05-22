project(libSmeagol NONE)
cmake_minimum_required(VERSION 2.8.11)

find_package(PythonInterp 3.4.2 REQUIRED)

set(_debian_default OFF)
if(EXISTS ${CMAKE_SYSROOT}/etc/debian_version)
    set(_debian_default ON)
endif()

option(DEBIAN_PACKAGE "Use Debian installation layout and support building a Debian package" ${_debian_default})

if(DEBIAN_PACKAGE)
    set(_install_path lib${LIB_SUFFIX}/python${PYTHON_VERSION_MAJOR}/dist-packages)
else()
    set(_install_path lib${LIB_SUFFIX}/python${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}/site-packages)
endif()

install(DIRECTORY dbus_interface_lib DESTINATION ${_install_path} PATTERN __pycache__ EXCLUDE)

if(DEBIAN_PACKAGE)
    include(Package.cmake)
endif()
