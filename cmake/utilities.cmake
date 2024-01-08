function(dependants output_variables)
    set(ENV{PYTHONPATH} ${CMAKE_BINARY_DIR})
    execute_process(
            COMMAND_ERROR_IS_FATAL ANY
            COMMAND ${Python3_EXECUTABLE} bin/find_dependants.py ${ARGN}
            OUTPUT_VARIABLE _FILES
    )
    separate_arguments(_FILES_LIST UNIX_COMMAND PROGRAM SEPARATE_ARGS ${_FILES})
    set(${output_variables} ${_FILES_LIST} PARENT_SCOPE)
endfunction()
