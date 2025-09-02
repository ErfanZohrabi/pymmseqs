# feat: Implement BaseMmseqsCommandline Framework

## 📋 Summary

This PR implements **Issue #1: Implement a Base Command-Line Wrapper Class** by introducing a comprehensive, Biopython Bio.Application-inspired framework for PyMMseqs2. This provides a solid, object-oriented foundation for creating Python wrappers around MMseqs2 command-line tools.

## 🎯 What This PR Addresses

- ✅ Creates a base class that handles common MMseqs2 command-line logic
- ✅ Implements parameter validation and type checking
- ✅ Provides automatic command-line string construction  
- ✅ Adds robust subprocess execution with proper error handling
- ✅ Establishes a consistent interface across all MMseqs2 commands
- ✅ Includes comprehensive documentation and type hints

## 🔧 Core Components

### 1. `BaseMmseqsCommandline` Abstract Base Class
- **Location**: `pymmseqs/application.py`
- **Purpose**: Abstract base for all MMseqs2 command wrappers
- **Features**:
  - Parameter management with validation
  - Automatic command-line construction
  - Subprocess execution with error handling
  - Consistent interface across commands

### 2. `MmseqsParameter` Data Class
- **Purpose**: Type-safe parameter definition
- **Validation**: Type checking, choice validation, file existence
- **Flexibility**: Supports flags, options, input/output files, multiple values

### 3. `MmseqsCommandResult` Data Class  
- **Purpose**: Encapsulates command execution results
- **Information**: Return code, stdout/stderr, execution time, success status

## 📁 Files Added

- `pymmseqs/application.py` - Core framework implementation
- `tests/test_application.py` - Comprehensive unit tests (28 test cases)
- `pymmseqs/commands/createdb_v2.py` - Example implementation using new framework
- `ARCHITECTURE.md` - Complete documentation of the new architecture

## 🧪 Testing

- **Unit Tests**: 28 comprehensive test cases covering all functionality
- **Coverage**: Parameter validation, command-line building, subprocess execution
- **Integration**: Working example with real MMseqs2 execution
- **All tests pass** ✅

```bash
# Run tests
export MMSEQS2_PATH=/usr/local/bin/mmseqs
python -m pytest tests/test_application.py -v
# Result: 28 passed
```

## 📝 Example Usage

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
        # ... additional parameters
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

## 🔍 Key Benefits

### Type Safety & Validation
- Automatic parameter type checking and conversion
- File existence validation for input files
- Choice validation for restricted parameters
- Custom validation function support

### Developer Experience
- Consistent API across all commands
- Clear error messages with proper validation
- Parameter introspection capabilities
- Both object-oriented and functional interfaces

### Maintainability
- Well-structured, modular design
- Comprehensive test coverage
- Complete documentation with examples
- Easy to extend with new commands

## 🚀 Architecture Highlights

### Inspired by Biopython
- Follows proven patterns from Bio.Application module
- Maintains consistency with established bioinformatics tools
- Provides familiar interface for users coming from Biopython

### Modern Python Practices
- Full type hints throughout the codebase
- Dataclass-based architecture for clarity
- Abstract base classes for proper inheritance
- Comprehensive docstrings and documentation

### Production Ready
- Robust error handling and validation
- Proper subprocess management
- Timeout support and environment control
- Extensive test coverage

## 🔄 Migration Path

This framework is designed to coexist with existing code:
- Existing commands continue to work unchanged
- New commands can use the new framework
- Gradual migration path for existing implementations
- No breaking changes to current API

## 📚 Documentation

- **ARCHITECTURE.md**: Complete framework documentation
- **Inline Documentation**: Comprehensive docstrings and type hints
- **Examples**: Working createdb_v2.py implementation
- **Test Cases**: 28 tests demonstrating proper usage

## 🎯 Future Work

This framework enables:
- Easy implementation of additional MMseqs2 commands
- Consistent error handling across the entire package
- Better parameter validation and user experience
- Simplified testing and maintenance

## ✅ Checklist

- [x] Code follows project style guidelines
- [x] All new code is fully tested (28 test cases, 100% pass rate)
- [x] Documentation is complete and clear
- [x] No breaking changes to existing functionality
- [x] Example implementation provided and working
- [x] Type hints added throughout
- [x] Error handling implemented properly

---

This PR establishes a solid foundation for PyMMseqs2's future development, bringing better type safety, error handling, and maintainability to the project while maintaining backward compatibility.
