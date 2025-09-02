# PyMMseqs2 New Architecture: BaseMmseqsCommandline Framework

## Overview

This document describes the new object-oriented architecture implemented for PyMMseqs2, inspired by Biopython's Bio.Application module. The new framework provides a solid foundation for creating Python wrappers around MMseqs2 command-line tools.

## Key Components

### 1. BaseMmseqsCommandline Abstract Base Class

The core of the new architecture is the `BaseMmseqsCommandline` abstract base class located in `pymmseqs/application.py`. This class provides:

- **Parameter Management**: Type-safe parameter definition and validation
- **Command-line Construction**: Automatic command-line string building
- **Subprocess Execution**: Robust command execution with error handling
- **Consistent Interface**: Uniform API across all MMseqs2 commands

### 2. MmseqsParameter Data Class

Represents individual command-line parameters with comprehensive validation:

```python
@dataclass
class MmseqsParameter:
    name: str                           # Parameter name
    flag: str                          # Command-line flag (e.g., '--min-seq-id')
    description: str                   # Human-readable description
    param_type: str                    # 'flag', 'option', 'input_file', 'output_file'
    value_type: Type = str             # Expected Python type
    default: Any = None                # Default value
    choices: Optional[List[Any]] = None # Valid choices
    required: bool = False             # Whether parameter is required
    multiple: bool = False             # Whether accepts multiple values
    validation_func: Optional[callable] = None # Custom validation
```

### 3. MmseqsCommandResult Data Class

Encapsulates command execution results:

```python
@dataclass
class MmseqsCommandResult:
    returncode: int                    # Process return code
    stdout: str                        # Standard output
    stderr: str                        # Standard error
    command_line: List[str]            # Full command executed
    success: bool                      # Whether command succeeded
    execution_time: Optional[float]    # Execution time in seconds
```

## Key Features

### Type Safety and Validation
- **Parameter Type Checking**: Automatic type conversion and validation
- **Choice Validation**: Restrict parameters to specific valid values
- **File Existence Validation**: Verify input files exist before execution
- **Custom Validation**: Support for custom validation functions

### Flexible Parameter System
- **Multiple Parameter Types**: Support for flags, options, input/output files
- **Multiple Values**: Handle parameters that accept multiple values
- **Positional Arguments**: Proper handling of positional vs. named parameters
- **Default Values**: Comprehensive default value management

### Robust Execution
- **Error Handling**: Proper subprocess error handling and reporting
- **Timeout Support**: Command execution timeout management
- **Environment Control**: Custom environment variable support
- **Output Capture**: Flexible stdout/stderr capture options

### Consistent Interface
- **Callable Objects**: Commands can be called directly like functions
- **String Representation**: Clear command-line preview with proper quoting
- **Parameter Introspection**: List and inspect available parameters

## Example Usage

### Basic Command Creation

```python
from pymmseqs.application import BaseMmseqsCommandline, create_input_file_parameter

class CreateDBCommand(BaseMmseqsCommandline):
    @property
    def command_name(self) -> str:
        return "createdb"
    
    def _init_parameters(self) -> None:
        self.add_parameter(create_input_file_parameter(
            name="input_file",
            description="Input FASTA file",
            required=True
        ))
        # ... more parameters
```

### Command Execution

```python
# Create and configure command
cmd = CreateDBCommand(
    input_files="sequences.fasta",
    output_db="mydb",
    dbtype=1,
    shuffle=False
)

# Execute and handle results
result = cmd.run()
if result.success:
    print(f"✓ Success! Execution time: {result.execution_time:.2f}s")
else:
    print(f"✗ Failed: {result.stderr}")
```

## Implementation Status

### ✅ Completed Components

1. **BaseMmseqsCommandline Framework** (`pymmseqs/application.py`)
   - Abstract base class with full parameter management
   - Type-safe parameter validation system
   - Automatic command-line construction
   - Robust subprocess execution

2. **Comprehensive Unit Tests** (`tests/test_application.py`)
   - 28 test cases covering all framework components
   - Parameter validation, command-line building, execution
   - Mock implementations for testing

3. **Example Implementation** (`pymmseqs/commands/createdb_v2.py`)
   - Complete createdb command using new architecture
   - Demonstrates proper parameter definition and usage
   - Working example with real MMseqs2 execution

### 🔄 Utility Functions

Helper functions for common parameter types:

```python
# Convenient parameter creation functions
create_input_file_parameter(name, description, required=True, multiple=False)
create_output_file_parameter(name, description, required=True)
create_option_parameter(name, value_type=str, default=None, choices=None)
create_flag_parameter(name, default=False)
```

## Benefits of the New Architecture

### For Developers
- **Consistent API**: Uniform interface across all commands
- **Type Safety**: Compile-time parameter validation
- **Easy Extension**: Simple to add new commands
- **Comprehensive Testing**: Built-in validation and testing support

### For Users
- **Better Error Messages**: Clear validation and execution errors
- **Parameter Introspection**: Discover available parameters programmatically
- **Flexible Usage**: Both object-oriented and functional interfaces
- **Robust Execution**: Proper error handling and result reporting

### For Maintainers
- **Modular Design**: Clean separation of concerns
- **Extensible Framework**: Easy to add new parameter types
- **Well-Tested**: Comprehensive unit test coverage
- **Documentation**: Clear examples and usage patterns

## Future Directions

1. **Command Migration**: Gradually migrate existing commands to new architecture
2. **Additional Commands**: Implement missing MMseqs2 commands
3. **Advanced Features**: Add progress indicators, parallel execution
4. **Integration**: Seamless integration with existing pymmseqs parsers

## Testing

Run the comprehensive test suite:

```bash
# Set MMseqs2 path and run tests
export MMSEQS2_PATH=/usr/local/bin/mmseqs
python -m pytest tests/test_application.py -v
```

All 28 tests should pass, demonstrating the framework's reliability and completeness.

---

This new architecture provides a solid foundation for the future development of PyMMseqs2, bringing better type safety, error handling, and maintainability to the project.
