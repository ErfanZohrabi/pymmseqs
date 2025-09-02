# pymmseqs/application.py

"""
Base command-line application framework for MMseqs2 commands.

This module provides a Biopython Bio.Application-inspired framework for wrapping
MMseqs2 command-line tools with a consistent, object-oriented interface.
"""

import os
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple, Type
from dataclasses import dataclass, field
import shlex

from .utils import get_mmseqs_binary


@dataclass
class MmseqsParameter:
    """
    Represents a single MMseqs2 command-line parameter.
    
    This class encapsulates all information needed to properly format
    and validate a command-line parameter for MMseqs2.
    
    Attributes:
        name: The parameter name as it appears in MMseqs2 documentation
        flag: The command-line flag (e.g., '--min-seq-id', '-v')
        description: Human-readable description of the parameter
        param_type: Type of parameter ('flag', 'option', 'input_file', 'output_file')
        value_type: Expected Python type for the value
        default: Default value for the parameter
        choices: List of valid choices (None if any value is allowed)
        required: Whether this parameter is required
        multiple: Whether parameter can accept multiple values
        validation_func: Optional custom validation function
    """
    name: str
    flag: str
    description: str
    param_type: str  # 'flag', 'option', 'input_file', 'output_file'
    value_type: Type = str
    default: Any = None
    choices: Optional[List[Any]] = None
    required: bool = False
    multiple: bool = False
    validation_func: Optional[callable] = None

    def __post_init__(self):
        """Validate parameter configuration after initialization."""
        valid_types = ['flag', 'option', 'input_file', 'output_file']
        if self.param_type not in valid_types:
            raise ValueError(f"param_type must be one of {valid_types}")
    
    def validate_value(self, value: Any) -> Any:
        """
        Validate and convert a parameter value.
        
        Args:
            value: The value to validate
            
        Returns:
            The validated/converted value
            
        Raises:
            ValueError: If the value is invalid
        """
        if value is None:
            if self.required:
                raise ValueError(f"Parameter {self.name} is required")
            return self.default
        
        # Type conversion (skip for multiple parameters with lists)
        if not isinstance(value, self.value_type) and value is not None and not (self.multiple and isinstance(value, (list, tuple))):
            try:
                value = self.value_type(value)
            except (ValueError, TypeError):
                raise ValueError(
                    f"Parameter {self.name} expected {self.value_type.__name__}, "
                    f"got {type(value).__name__}"
                )
        
        # Choice validation
        if self.choices is not None and value not in self.choices:
            raise ValueError(
                f"Parameter {self.name} must be one of {self.choices}, got {value}"
            )
        
        # File existence validation
        if self.param_type == 'input_file' and value:
            if self.multiple and isinstance(value, (list, tuple)):
                # Validate each file in the list
                for file_path in value:
                    path = Path(file_path)
                    if not path.exists():
                        raise FileNotFoundError(f"Input file not found: {file_path}")
            else:
                # Validate single file
                path = Path(value)
                if not path.exists():
                    raise FileNotFoundError(f"Input file not found: {value}")
        
        # Custom validation
        if self.validation_func and value is not None:
            try:
                value = self.validation_func(value)
            except Exception as e:
                raise ValueError(f"Validation failed for {self.name}: {e}")
        
        return value

    def format_for_command_line(self, value: Any) -> List[str]:
        """
        Format the parameter and its value for command-line usage.
        
        Args:
            value: The parameter value
            
        Returns:
            List of command-line strings
        """
        if value is None or (self.param_type == 'flag' and not value):
            return []
        
        if self.param_type == 'flag':
            # Boolean flag parameter
            return [self.flag] if value else []
        elif self.multiple and isinstance(value, (list, tuple)):
            # Multiple values
            result = []
            for v in value:
                result.extend([self.flag, str(v)])
            return result
        else:
            # Single value parameter
            return [self.flag, str(value)]


@dataclass
class MmseqsCommandResult:
    """
    Encapsulates the result of a MMseqs2 command execution.
    
    Attributes:
        returncode: The subprocess return code
        stdout: Standard output from the command
        stderr: Standard error from the command
        command_line: The full command line that was executed
        success: Whether the command completed successfully
        execution_time: Time taken for command execution (if measured)
    """
    returncode: int
    stdout: str
    stderr: str
    command_line: List[str]
    success: bool = field(init=False)
    execution_time: Optional[float] = None
    
    def __post_init__(self):
        """Set success based on return code."""
        self.success = self.returncode == 0

    @property
    def command_string(self) -> str:
        """Get the command as a shell-escaped string."""
        return ' '.join(shlex.quote(arg) for arg in self.command_line)


class BaseMmseqsCommandline(ABC):
    """
    Abstract base class for MMseqs2 command-line wrappers.
    
    This class provides a framework for creating Python wrappers around MMseqs2
    command-line tools, inspired by Biopython's Bio.Application module.
    
    Key features:
    - Parameter validation and type checking
    - Automatic command-line string construction
    - Subprocess execution with proper error handling
    - Consistent interface across all MMseqs2 commands
    - Extensible parameter system
    """
    
    def __init__(self, **kwargs):
        """
        Initialize the command-line wrapper.
        
        Args:
            **kwargs: Parameter values to set
        """
        self._parameters: Dict[str, MmseqsParameter] = {}
        self._parameter_values: Dict[str, Any] = {}
        
        # Initialize parameters from subclass definition
        self._init_parameters()
        
        # Set any provided parameter values
        for name, value in kwargs.items():
            self.set_parameter(name, value)
    
    @property
    @abstractmethod
    def command_name(self) -> str:
        """Return the MMseqs2 command name (e.g., 'createdb', 'easy-cluster')."""
        pass
    
    @abstractmethod
    def _init_parameters(self) -> None:
        """
        Initialize the parameters for this command.
        
        Subclasses must implement this method to define their specific parameters
        using the add_parameter method.
        """
        pass
    
    def add_parameter(self, parameter: MmseqsParameter) -> None:
        """
        Add a parameter definition to this command.
        
        Args:
            parameter: The parameter definition to add
        """
        self._parameters[parameter.name] = parameter
        # Set default value if not already set
        if parameter.name not in self._parameter_values:
            self._parameter_values[parameter.name] = parameter.default
    
    def set_parameter(self, name: str, value: Any) -> None:
        """
        Set the value of a parameter.
        
        Args:
            name: Parameter name
            value: Parameter value
            
        Raises:
            ValueError: If parameter doesn't exist or value is invalid
        """
        if name not in self._parameters:
            raise ValueError(f"Unknown parameter: {name}")
        
        param = self._parameters[name]
        validated_value = param.validate_value(value)
        self._parameter_values[name] = validated_value
    
    def get_parameter(self, name: str) -> Any:
        """
        Get the current value of a parameter.
        
        Args:
            name: Parameter name
            
        Returns:
            The parameter value
            
        Raises:
            ValueError: If parameter doesn't exist
        """
        if name not in self._parameters:
            raise ValueError(f"Unknown parameter: {name}")
        return self._parameter_values.get(name, self._parameters[name].default)
    
    def list_parameters(self) -> List[str]:
        """
        Get a list of all available parameter names.
        
        Returns:
            List of parameter names
        """
        return list(self._parameters.keys())
    
    def validate_parameters(self) -> None:
        """
        Validate all current parameter values.
        
        Raises:
            ValueError: If any parameter is invalid
            FileNotFoundError: If any required input file doesn't exist
        """
        for name, param in self._parameters.items():
            value = self._parameter_values.get(name)
            param.validate_value(value)  # This will raise if invalid
    
    def build_command_line(self) -> List[str]:
        """
        Build the complete command line for execution.
        
        Returns:
            List of command-line arguments
            
        Raises:
            ValueError: If parameters are invalid
        """
        # Validate all parameters first
        self.validate_parameters()
        
        # Start with the command name
        cmd_line = [self.command_name]
        
        # Add positional arguments first (input/output files)
        positional_params = []
        option_params = []
        
        for name, param in self._parameters.items():
            value = self._parameter_values.get(name)
            if value is not None:
                if param.param_type in ['input_file', 'output_file']:
                    positional_params.append((param, value))
                else:
                    option_params.append((param, value))
        
        # Sort positional parameters by their order of definition
        # (This assumes parameters are added in the correct order)
        for param, value in positional_params:
            if param.multiple and isinstance(value, (list, tuple)):
                cmd_line.extend(str(v) for v in value)
            else:
                cmd_line.append(str(value))
        
        # Add option parameters
        for param, value in option_params:
            cmd_line.extend(param.format_for_command_line(value))
        
        return cmd_line
    
    def __call__(self, 
                 cwd: Optional[Union[str, Path]] = None,
                 capture_output: bool = True,
                 check: bool = True,
                 timeout: Optional[float] = None,
                 env: Optional[Dict[str, str]] = None) -> MmseqsCommandResult:
        """
        Execute the MMseqs2 command.
        
        Args:
            cwd: Working directory for command execution
            capture_output: Whether to capture stdout/stderr
            check: Whether to raise exception on non-zero return code
            timeout: Command timeout in seconds
            env: Environment variables for the subprocess
            
        Returns:
            MmseqsCommandResult with execution details
            
        Raises:
            subprocess.CalledProcessError: If check=True and command fails
            FileNotFoundError: If MMseqs2 binary not found
            subprocess.TimeoutExpired: If command times out
        """
        return self.run(cwd=cwd, capture_output=capture_output, 
                       check=check, timeout=timeout, env=env)
    
    def run(self,
            cwd: Optional[Union[str, Path]] = None,
            capture_output: bool = True,
            check: bool = True,
            timeout: Optional[float] = None,
            env: Optional[Dict[str, str]] = None) -> MmseqsCommandResult:
        """
        Execute the MMseqs2 command.
        
        Args:
            cwd: Working directory for command execution
            capture_output: Whether to capture stdout/stderr
            check: Whether to raise exception on non-zero return code
            timeout: Command timeout in seconds
            env: Environment variables for the subprocess
            
        Returns:
            MmseqsCommandResult with execution details
            
        Raises:
            subprocess.CalledProcessError: If check=True and command fails
            FileNotFoundError: If MMseqs2 binary not found
            subprocess.TimeoutExpired: If command times out
        """
        import time
        
        # Get MMseqs2 binary path
        binary = get_mmseqs_binary()
        
        # Build command line
        cmd_args = self.build_command_line()
        full_command = [binary] + cmd_args
        
        # Prepare environment
        if env is None:
            env = os.environ.copy()
        
        # Execute command
        start_time = time.time()
        
        try:
            result = subprocess.run(
                full_command,
                cwd=cwd,
                capture_output=capture_output,
                text=True,
                check=False,  # We'll handle checking manually
                timeout=timeout,
                env=env
            )
            
            execution_time = time.time() - start_time
            
            # Create result object
            mmseqs_result = MmseqsCommandResult(
                returncode=result.returncode,
                stdout=result.stdout or "",
                stderr=result.stderr or "",
                command_line=full_command,
                execution_time=execution_time
            )
            
            # Handle errors if requested
            if check and not mmseqs_result.success:
                error_msg = f"Command '{self.command_name}' failed with return code {result.returncode}"
                if mmseqs_result.stderr:
                    error_msg += f"\nStderr: {mmseqs_result.stderr}"
                raise subprocess.CalledProcessError(
                    result.returncode, full_command, 
                    result.stdout, result.stderr
                )
            
            return mmseqs_result
            
        except subprocess.TimeoutExpired as e:
            execution_time = time.time() - start_time
            # Re-raise with additional context
            raise subprocess.TimeoutExpired(
                full_command, timeout, 
                output=getattr(e, 'output', None),
                stderr=getattr(e, 'stderr', None)
            ) from e
    
    def __str__(self) -> str:
        """Return string representation showing current command line."""
        try:
            cmd_line = self.build_command_line()
            binary = get_mmseqs_binary()
            full_cmd = [binary] + cmd_line
            return ' '.join(shlex.quote(arg) for arg in full_cmd)
        except Exception as e:
            return f"<{self.__class__.__name__} (invalid parameters: {e})>"
    
    def __repr__(self) -> str:
        """Return detailed string representation."""
        params = {name: self.get_parameter(name) 
                 for name in self._parameters.keys() 
                 if self.get_parameter(name) is not None}
        return f"{self.__class__.__name__}({', '.join(f'{k}={repr(v)}' for k, v in params.items())})"


# Utility functions for common parameter types

def create_input_file_parameter(
    name: str, 
    flag: str = None, 
    description: str = "", 
    required: bool = True,
    multiple: bool = False
) -> MmseqsParameter:
    """Create a parameter for input files."""
    if flag is None:
        flag = f"--{name.replace('_', '-')}"
    
    return MmseqsParameter(
        name=name,
        flag=flag,
        description=description,
        param_type='input_file',
        value_type=str,
        required=required,
        multiple=multiple
    )


def create_output_file_parameter(
    name: str, 
    flag: str = None, 
    description: str = "", 
    required: bool = True
) -> MmseqsParameter:
    """Create a parameter for output files."""
    if flag is None:
        flag = f"--{name.replace('_', '-')}"
    
    return MmseqsParameter(
        name=name,
        flag=flag,
        description=description,
        param_type='output_file',
        value_type=str,
        required=required
    )


def create_option_parameter(
    name: str,
    flag: str = None,
    description: str = "",
    value_type: Type = str,
    default: Any = None,
    choices: Optional[List[Any]] = None,
    required: bool = False
) -> MmseqsParameter:
    """Create a standard option parameter."""
    if flag is None:
        if len(name) == 1:
            flag = f"-{name}"
        else:
            flag = f"--{name.replace('_', '-')}"
    
    return MmseqsParameter(
        name=name,
        flag=flag,
        description=description,
        param_type='option',
        value_type=value_type,
        default=default,
        choices=choices,
        required=required
    )


def create_flag_parameter(
    name: str,
    flag: str = None,
    description: str = "",
    default: bool = False
) -> MmseqsParameter:
    """Create a boolean flag parameter."""
    if flag is None:
        if len(name) == 1:
            flag = f"-{name}"
        else:
            flag = f"--{name.replace('_', '-')}"
    
    return MmseqsParameter(
        name=name,
        flag=flag,
        description=description,
        param_type='flag',
        value_type=bool,
        default=default,
        required=False
    )
