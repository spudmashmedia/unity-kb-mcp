#!/usr/bin/env bash
set -o pipefail

# Configuration
TARGET_URL="https://cloudmedia-docs.unity3d.com/docscloudstorage/en/6000.0/UnityDocumentation.zip"
BUILD_DIR_NAME="${BUILD_DIR_NAME:-kb}"  # Default to 'kb'
DEST_DIR="${PWD}/${BUILD_DIR_NAME}/docs"  # Direct path: ./kb/docs/
TEMP_ZIP="${BUILD_DIR_NAME}/tmp/blender_docs_temp.zip"
CLEAN_MODE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --clean|-c)
            CLEAN_MODE=true
            shift
            ;;
        --build-dir|-b)
            BUILD_DIR_NAME="$2"
            DEST_DIR="${PWD}/${BUILD_DIR_NAME}/docs"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--clean|-c] [--build-dir|-b <path>]"
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

echo "Starting Docs Download..."
echo "Destination: $DEST_DIR"

# Step 1: Clean destination directory if requested
if [ "$CLEAN_MODE" = true ]; then
    echo "Cleaning destination folder: $DEST_DIR"
    rm -rf "$DEST_DIR"
fi

# Step 2: Create directories (destination + temp)
echo "Creating directories..."
mkdir -p "${BUILD_DIR_NAME}/tmp"
mkdir -p "$DEST_DIR"

# Step 3: Download the zip file
echo "Downloading from: $TARGET_URL"
if ! curl -fL -o "$TEMP_ZIP" "$TARGET_URL"; then
    echo "Error: Failed to download the zip file." >&2
    exit 1
fi

# Step 4: Extract the contents into the destination folder
echo "Extracting files..."
if ! unzip -q -o "$TEMP_ZIP" -d "$DEST_DIR"; then
    echo "Error: Failed to extract the zip file." >&2
    rm -f "$TEMP_ZIP"
    exit 1
fi

# Step 5: Cleanup temporary directory and file
rm -rf "${BUILD_DIR_NAME}/tmp"

echo "Done! Files extracted to $DEST_DIR"
