ADD_EXECUTABLE(
	convenience_headers
	convenience_headers.cpp
)

TARGET_LINK_LIBRARIES(
	convenience_headers
	${Fcppt_core_LIBRARIES}
	${Fcppt_filesystem_LIBRARIES}
)

INSTALL(
	TARGETS convenience_headers
	DESTINATION ${INSTALL_BINARY_DIR}
)
