FROM git.equinor.com:4567/sdp/sdpsoft/centos:6
LABEL version="1.2.5" \
      maintainer="snis@equinor.com" \
      description="This is the Docker image for building, and testing nrlib." \
      "com.statoil.vendor"="Statoil ASA"

# Versions
ENV GCC_VERSION=4.9.4 \
    PYTHON_VERSION=3.6.1 \
    ROXAR_VERSION=10.1.3

# Prefixes
ENV MKL_ROOT="/prog/Intel/studioxe2016/mkl" \
    GCC_PREFIX=$INSTALL_DIR/gcc-$GCC_VERSION \
    ROXAR_RMS_ROOT="/prog/roxar/rms/versions/$ROXAR_VERSION/linux-amd64-gcc_4_4-release" \
    PYTHON_PREFIX="$INSTALL_DIR/python$PYTHON_VERSION" \
    PROG_DIR="prog"

ENV ROXAR_PYTHON="$ROXAR_RMS_ROOT/bin/python" \
    ROXENV="$ROXAR_RMS_ROOT/bin/roxenv" \
    SDPSOFT_PYTHON="$PYTHON_PREFIX/bin/python3" \
    PATH="$GCC_PREFIX/bin:$PATH" \
    LD_LIBRARY_PATH="\
/lib64\
:$GCC_PREFIX/lib\
:$GCC_PREFIX/lib64\
:$GCC_PREFIX/lib/gcc/x86_64-unknown-linux-gnu/4.9.4\
:$GCC_PREFIX/lib/gcc/x86_64-unknown-linux-gnu/lib64\
:$ROXAR_RMS_ROOT/lib\
"
COPY ./$PROG_DIR /$PROG_DIR

RUN ln -s /lib64/libgcc_s.so.1 /lib64/libgcc_s.so \
 && yum update -y \
 && yum install -y \
        mesa-libGL \
        glibc-devel \
        glibc-headers \
        libicu-devel \
        mpich-devel \
        openmp-devel \
        blas-devel \
        lapack-devel \
        zlib-devel \
        bzip2-devel \
        python-devel \
 && yum clean all
