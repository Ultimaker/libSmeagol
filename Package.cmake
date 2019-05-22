set(CPACK_PACKAGE_VENDOR "Ultimaker")
set(CPACK_PACKAGE_CONTACT "Ultimaker <info@ultimaker.com>")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "Stores precious data")
set(CPACK_PACKAGE_VERSION_MAJOR 1)
set(CPACK_PACKAGE_VERSION_MINOR 0)
set(CPACK_PACKAGE_VERSION_PATCH 0)
set(CPACK_GENERATOR "DEB")

set(CPACK_DEBIAN_PACKAGE_ARCHITECTURE all)

set(DEB_DEPENDS
    "python3 (>= 3.4.2)"
)
string(REPLACE ";" "," DEB_DEPENDS "${DEB_DEPENDS}")
set(CPACK_DEBIAN_PACKAGE_DEPENDS ${DEB_DEPENDS})

include(CPack)
