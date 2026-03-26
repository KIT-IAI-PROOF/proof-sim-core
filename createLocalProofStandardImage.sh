#!/bin/bash

# Parse command line arguments
BUILD_JAVA=false
BUILD_PYTHON=false

for arg in "$@"; do
    case $arg in
        --java|-j)
            BUILD_JAVA=true
            ;;
        --python|-p)
            BUILD_PYTHON=true
            ;;
        *)
            echo "Unknown option: $arg"
            echo -e "Usage: $0 [--java|-j] [--python|-p]\nExpecting proof-worker:local to exist, else build it with --java|-j flag."
            exit 1
            ;;
    esac
done

# Check if --java or -j flag is provided
if [ "$BUILD_JAVA" = true ]; then
    echo -e "\n===== Building proof-worker image...\n"
    
    # Check if proof-worker directory exists
    if [ ! -d "../proof-worker" ]; then
        echo "ERROR: proof-worker directory not found at ../proof-worker"
        echo "Expected location: $(cd .. && pwd)/proof-worker"
        exit 2
    fi
    
    cd ../proof-worker
    mvn clean compile jib:dockerBuild -Dimage=proof-worker:local -f pom-local.xml
    
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to build proof-worker image with error code '$?'"
        exit 3
    fi
    
    cd ../proof-sim-core
fi

# Check if --python or -p flag is provided
if [ "$BUILD_PYTHON" = true ]; then
    echo -e "\n===== Building Python package...\n"
    python3 -m build
    
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to build Python package with error code '$?'"
        exit 1
    fi
fi

# Always execute docker build commands
echo -e "\n===== Building py-build container...\n"
docker build -t python-build-test -f docker/proof-standard/Dockerfile-local-python-dev --target python-build-test .
echo -e "\n===== Building proof-standard image...\n"
docker build -t proof-standard:local -f docker/proof-standard/Dockerfile-local-python-dev --target final .