#!/bin/bash
# Build script for creating universal maniforge executables

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔨 Building Maniforge Universal Executable${NC}"
echo

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install --upgrade pip > /dev/null 2>&1
pip install pyinstaller pyyaml > /dev/null 2>&1

# Clean previous builds
echo -e "${YELLOW}Cleaning previous builds...${NC}"
rm -rf build/ dist/

# Build the executable
echo -e "${YELLOW}Building executable...${NC}"
pyinstaller --clean maniforge.spec

# Check if build succeeded
if [ -f "dist/maniforge" ]; then
    echo
    echo -e "${GREEN}✅ Build successful!${NC}"
    echo
    echo "Executable location: dist/maniforge"
    echo
    
    # Test the executable
    echo -e "${YELLOW}Testing executable...${NC}"
    ./dist/maniforge --help > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Executable works!${NC}"
    else
        echo -e "${RED}❌ Executable test failed${NC}"
        exit 1
    fi
    
    # Show file info
    echo
    echo -e "${BLUE}File Info:${NC}"
    ls -lh dist/maniforge
    file dist/maniforge
    
    echo
    echo -e "${GREEN}Installation:${NC}"
    echo "  sudo cp dist/maniforge /usr/local/bin/maniforge"
    echo
    echo -e "${GREEN}Or test locally:${NC}"
    echo "  ./dist/maniforge init --cluster my-cluster"
else
    echo -e "${RED}❌ Build failed${NC}"
    deactivate
    exit 1
fi

# Deactivate virtual environment
deactivate
