FROM centos:6
LABEL version="1.1.1" \
      maintainer="snis@statoil.com" \
      description="This is the Docker image for building, and testing nrlib." \
      "com.statoil.vendor"="Statoil ASA"

######################################################################
#  ___ ___  _____  ____   __  ___ ___ _____ _____ ___ _  _  ___ ___
# | _ \ _ \/ _ \ \/ /\ \ / / / __| __|_   _|_   _|_ _| \| |/ __/ __|
# |  _/   / (_) >  <  \ V /  \__ \ _|  | |   | |  | || .` | (_ \__ \
# |_| |_|_\\___/_/\_\  |_|   |___/___| |_|   |_| |___|_|\_|\___|___/
#
######################################################################
ENV PROXY_SCHEME=http
ENV PROXY_HOST=www-proxy.statoil.no
ENV PROXY_PORT=80
ENV HTTP_PROXY=$PROXY_SCHEME://$PROXY_HOST:$PROXY_PORT
ENV HTTPS_PROXY=$PROXY_SCHEME://$PROXY_HOST:$PROXY_PORT
ENV FTP_PROXY=$PROXY_SCHEME://$PROXY_HOST:$PROXY_PORT
# Tell yum to use the proxy as well
RUN echo "proxy=$HTTP_PROXY" >> /etc/yum.conf
# Install wget and tell wget to use the proxy too
RUN yum update -y \
 && yum install -y wget
RUN echo "https_proxy = $HTTP_PROXY" >> /etc/wgetrc \
 && echo "http_proxy = $HTTPS_PROXY" >> /etc/wgetrc \
 && echo "ftp_proxy = $HTTP_PROXY" >> /etc/wgetrc \
 && echo "use_proxy = on" >> /etc/wgetrc

# Download, and install Statoil's Certificates
ENV STATOIL_CERT="statoil-ca-certificates.el6.rpm"
RUN wget http://st-linrhn01.st.statoil.no/pub/$STATOIL_CERT \
 && yum install -y $STATOIL_CERT \
 && rm -f $STATOIL_CERT

#################################################
#  __  __ ___ ___  ___     __  ___ _  ___   __
# |  \/  |_ _/ __|/ __|   / / | __| \| \ \ / /
# | |\/| || |\__ \ (__   / /  | _|| .` |\ V /
# |_|  |_|___|___/\___| /_/   |___|_|\_| \_/
#
#################################################
ENV ENCODING="en_US.UTF-8"
ENV LC_ALL=$ENCODING
ENV LANG=$ENCODING

ENV ROOT_DIR=/software
ENV BUILD_DIR=$ROOT_DIR/build
ENV SOURCE_DIR=$ROOT_DIR/source
ENV PROG_DIR=/prog
ENV INSTALL_DIR=$PROG_DIR/sdpsoft

ENV GCC_VERSION="4.9.4"
ENV GCC_PREFIX=$INSTALL_DIR/gcc-$GCC_VERSION


ENV MKL_ROOT="/prog/Intel/studioxe2016/mkl"

ENV ROXAR_VERSION=10.1.1
ENV ROXAR_RMS_ROOT="/prog/roxar/rms/versions/$ROXAR_VERSION/linux-amd64-gcc_4_4-release"
ENV ROXAR_PYTHON="$ROXAR_RMS_ROOT/bin/python"
ENV ROXENV="$ROXAR_RMS_ROOT/bin/roxenv"

ENV PYTHON_VERSION="3.6.1"
ENV PYTHON_PREFIX="$INSTALL_DIR/python$PYTHON_VERSION"
ENV SDPSOFT_PYTHON="$PYTHON_PREFIX/bin/python"

COPY ./$PROG_DIR $PROG_DIR

ENV PATH="$GCC_PREFIX/bin:$PATH"
ENV LD_LIBRARY_PATH="$GCC_PREFIX/lib:$LD_LIBRARY_PATH"
ENV LD_LIBRARY_PATH="$GCC_PREFIX/lib64:$LD_LIBRARY_PATH"
ENV LD_LIBRARY_PATH="$GCC_PREFIX/lib/gcc/x86_64-unknown-linux-gnu/4.9.4:$LD_LIBRARY_PATH"
ENV LD_LIBRARY_PATH="$GCC_PREFIX/lib/gcc/x86_64-unknown-linux-gnu/lib64:$LD_LIBRARY_PATH"

RUN ln -s /lib64/libgcc_s.so.1 /lib64/libgcc_s.so

RUN yum update -y \
 && yum install -y mesa-libGL \
        glibc-devel \
        glibc-headers \
        libicu-devel \
        mpich-devel \
        openmp-devel \
        zlib-devel \
        bzip2-devel \
        python-devel

ENV LD_LIBRARY_PATH=/lib64:$LD_LIBRARY_PATH


ENV SOURCE_DIR="/source"
ENV BUILD_DIR="/build"
ENV INSTALL_DIR="/prog/sdpsoft"
RUN mkdir -p \
        $SOURCE_DIR \
        $BUILD_DIR \
        $INSTALL_DIR
