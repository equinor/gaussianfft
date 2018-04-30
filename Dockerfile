FROM git.statoil.no:4567/sdp/sdpsoft/centos:6
LABEL version="1.2.1" \
      maintainer="snis@statoil.com" \
      description="This is the Docker image for building, and testing nrlib." \
      "com.statoil.vendor"="Statoil ASA"

ENV GCC_VERSION="4.9.4"
ENV GCC_PREFIX=$INSTALL_DIR/gcc-$GCC_VERSION


ENV MKL_ROOT="/prog/Intel/studioxe2016/mkl"

ENV ROXAR_VERSION=10.1.3
ENV ROXAR_RMS_ROOT="/prog/roxar/rms/versions/$ROXAR_VERSION/linux-amd64-gcc_4_4-release"
ENV ROXAR_PYTHON="$ROXAR_RMS_ROOT/bin/python"
ENV ROXENV="$ROXAR_RMS_ROOT/bin/roxenv"

ENV PYTHON_VERSION=3.6.1
ENV PYTHON_PREFIX="$INSTALL_DIR/python$PYTHON_VERSION"
ENV SDPSOFT_PYTHON="$PYTHON_PREFIX/bin/python3"

COPY ./$PROG_DIR $PROG_DIR

ENV PATH="$GCC_PREFIX/bin:$PATH"
ENV LD_LIBRARY_PATH="\
/lib64\
:$GCC_PREFIX/lib\
:$GCC_PREFIX/lib64\
:$GCC_PREFIX/lib/gcc/x86_64-unknown-linux-gnu/4.9.4\
:$GCC_PREFIX/lib/gcc/x86_64-unknown-linux-gnu/lib64\
:$ROXAR_RMS_ROOT/lib\
"

RUN ln -s /lib64/libgcc_s.so.1 /lib64/libgcc_s.so \
 && yum update -y \
 && yum install -y \
        mesa-libGL \
        glibc-devel \
        glibc-headers \
        libicu-devel \
        mpich-devel \
        openmp-devel \
        zlib-devel \
        bzip2-devel \
        python-devel \
 && yum clean all
