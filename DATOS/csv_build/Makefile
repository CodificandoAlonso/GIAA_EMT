# Compiler and flags
CXX = g++
CXXFLAGS = -std=c++20 -Wall -Wextra -O2
DEBUG_FLAGS = -g -DDEBUG

# Directories
SRC_DIR = src
BUILD_DIR = .
BIN_DIR = bin


# Output executable
TARGET = converter
DEBUG_TARGET = $(TARGET)_debug

# Source files
SOURCES = $(SRC_DIR)/main.cpp
OBJECTS = $(SOURCES:$(SRC_DIR)/%.cpp=$(BUILD_DIR)/%.o)
DEBUG_OBJECTS = $(SOURCES:$(SRC_DIR)/%.cpp=$(BUILD_DIR)/%.debug.o)

# Default target
all: directories $(BIN_DIR)/$(TARGET)

# Debug target
debug: CXXFLAGS += $(DEBUG_FLAGS)
debug: directories $(BIN_DIR)/$(DEBUG_TARGET)

# Create necessary directories
directories:
	@mkdir -p $(BUILD_DIR) $(BIN_DIR)

# Build release version
$(BIN_DIR)/$(TARGET): $(OBJECTS)
	$(CXX) $(CXXFLAGS) $^ -o $@
	@echo "Build complete: $@"

# Build debug version
$(BIN_DIR)/$(DEBUG_TARGET): $(DEBUG_OBJECTS)
	$(CXX) $(CXXFLAGS) $^ -o $@
	@echo "Debug build complete: $@"

# Compile source files (release)
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Compile source files (debug)
$(BUILD_DIR)/%.debug.o: $(SRC_DIR)/%.cpp
	$(CXX) $(CXXFLAGS) $(DEBUG_FLAGS) -c $< -o $@

# Clean build artifacts
clean:
	rm -rf $(BUILD_DIR) $(BIN_DIR)
	@echo "Cleaned build artifacts"

# Phony targets
.PHONY: all debug clean run directories