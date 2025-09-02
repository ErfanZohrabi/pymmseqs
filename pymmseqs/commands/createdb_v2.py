# pymmseqs/commands/createdb_v2.py

"""
New BaseMmseqsCommandline-based implementation of the createdb command.

This module demonstrates the new architecture by implementing the createdb 
command using the BaseMmseqsCommandline framework.
"""

from pathlib import Path
from typing import List, Union

from ..application import (
    BaseMmseqsCommandline,
    create_input_file_parameter,
    create_output_file_parameter,
    create_option_parameter,
    create_flag_parameter
)


class CreateDBCommand(BaseMmseqsCommandline):
    """
    Create a MMseqs2 database from FASTA file(s) using the new architecture.
    
    This command creates a MMseqs2 database from one or more FASTA files,
    providing extensive control over database creation parameters.
    
    Example usage:
        # Basic usage
        cmd = CreateDBCommand(
            input_files="sequences.fasta",
            output_db="mydb"
        )
        result = cmd.run()
        
        # Advanced usage with options
        cmd = CreateDBCommand(
            input_files=["seq1.fasta", "seq2.fasta"], 
            output_db="mydb",
            dbtype=1,  # Amino acid sequences
            shuffle=False,
            compressed=True
        )
        result = cmd.run()
        
        # Check result
        if result.success:
            print("Database created successfully!")
        else:
            print(f"Failed: {result.stderr}")
    """
    
    @property
    def command_name(self) -> str:
        return "createdb"
    
    def _init_parameters(self) -> None:
        """Initialize all parameters for the createdb command."""
        
        # Input FASTA file(s) - positional argument
        self.add_parameter(create_input_file_parameter(
            name="input_files",
            flag="",  # Positional - no flag
            description="Input FASTA file(s)",
            required=True,
            multiple=True
        ))
        
        # Output database - positional argument
        self.add_parameter(create_output_file_parameter(
            name="output_db", 
            flag="",  # Positional - no flag
            description="Output database path prefix",
            required=True
        ))
        
        # Database type option
        self.add_parameter(create_option_parameter(
            name="dbtype",
            flag="--dbtype",
            description="Database type (0=auto-detect, 1=amino acid, 2=nucleotide)",
            value_type=int,
            default=0,
            choices=[0, 1, 2]
        ))
        
        # Shuffle sequences
        self.add_parameter(create_flag_parameter(
            name="shuffle",
            flag="--shuffle",
            description="Shuffle input database entries",
            default=True
        ))
        
        # Database creation mode
        self.add_parameter(create_option_parameter(
            name="createdb_mode",
            flag="--createdb-mode",
            description="Database creation mode (0=copy data, 1=soft-link)",
            value_type=int,
            default=0,
            choices=[0, 1]
        ))
        
        # ID offset
        self.add_parameter(create_option_parameter(
            name="id_offset",
            flag="--id-offset", 
            description="Numeric ID offset in index file",
            value_type=int,
            default=0
        ))
        
        # Compression
        self.add_parameter(create_flag_parameter(
            name="compressed",
            flag="--compressed",
            description="Compress output files",
            default=False
        ))
        
        # Verbosity
        self.add_parameter(create_option_parameter(
            name="v",
            flag="-v",
            description="Verbosity level (0=quiet, 1=+errors, 2=+warnings, 3=+info)",
            value_type=int,
            default=3,
            choices=[0, 1, 2, 3]
        ))
        
        # Write lookup file
        self.add_parameter(create_flag_parameter(
            name="write_lookup",
            flag="--write-lookup",
            description="Create .lookup file mapping IDs to FASTA headers",
            default=True
        ))
    
    def __init__(self, 
                 input_files: Union[str, Path, List[Union[str, Path]]],
                 output_db: Union[str, Path],
                 **kwargs):
        """
        Initialize the CreateDB command.
        
        Args:
            input_files: Input FASTA file(s)
            output_db: Output database path prefix
            **kwargs: Additional parameters (dbtype, shuffle, etc.)
        """
        # Initialize the base class first
        super().__init__()
        
        # Set required parameters
        if isinstance(input_files, (str, Path)):
            input_files = [str(input_files)]
        else:
            input_files = [str(f) for f in input_files]
            
        self.set_parameter("input_files", input_files)
        self.set_parameter("output_db", str(output_db))
        
        # Set any additional parameters
        for key, value in kwargs.items():
            if key in self._parameters:
                self.set_parameter(key, value)
            else:
                raise ValueError(f"Unknown parameter: {key}")
    
    def build_command_line(self) -> List[str]:
        """
        Build command line with proper parameter ordering for createdb.
        
        MMseqs2 createdb expects: createdb input1 [input2 ...] output_db [OPTIONS]
        """
        # Validate parameters first
        self.validate_parameters()
        
        cmd_line = [self.command_name]
        
        # Add input files (positional)
        input_files = self.get_parameter("input_files")
        if isinstance(input_files, list):
            cmd_line.extend(input_files)
        else:
            cmd_line.append(str(input_files))
        
        # Add output database (positional)
        cmd_line.append(str(self.get_parameter("output_db")))
        
        # Add option parameters (non-positional)
        for name, param in self._parameters.items():
            if name not in ["input_files", "output_db"]:  # Skip positional args
                value = self.get_parameter(name)
                if value is not None and value != param.default:
                    cmd_line.extend(param.format_for_command_line(value))
        
        return cmd_line


def createdb_v2(input_files: Union[str, Path, List[Union[str, Path]]],
                output_db: Union[str, Path],
                **kwargs):
    """
    Create a MMseqs2 database using the new architecture.
    
    This is a convenience function that creates and runs a CreateDBCommand
    with the specified parameters.
    
    Args:
        input_files: Input FASTA file(s)
        output_db: Output database path prefix  
        **kwargs: Additional parameters (dbtype, shuffle, etc.)
        
    Returns:
        MmseqsCommandResult: Result of the command execution
        
    Example:
        result = createdb_v2("sequences.fasta", "mydb", dbtype=1, shuffle=False)
        if result.success:
            print("Database created successfully!")
    """
    cmd = CreateDBCommand(input_files, output_db, **kwargs)
    return cmd.run()


if __name__ == "__main__":
    # Example usage
    import tempfile
    import os
    
    # Create a temporary FASTA file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">seq1\nMETHKAQVALSQEELEKI\n")
        f.write(">seq2\nMSTQVGIQPLIAEKGQYEF\n")
        temp_fasta = f.name
    
    try:
        # Test the new createdb implementation
        with tempfile.TemporaryDirectory() as temp_dir:
            output_db = os.path.join(temp_dir, "test_db")
            
            # Create command
            cmd = CreateDBCommand(
                input_files=temp_fasta,
                output_db=output_db,
                dbtype=1,  # Amino acid
                shuffle=False,
                v=3  # Verbose
            )
            
            print("Command line:", str(cmd))
            
            # Run command  
            result = cmd.run()
            
            if result.success:
                print("✓ Database creation successful!")
                print(f"Execution time: {result.execution_time:.2f}s")
                
                # List created files
                db_files = [f for f in os.listdir(temp_dir) if f.startswith("test_db")]
                print(f"Created files: {db_files}")
            else:
                print("✗ Database creation failed!")
                print(f"Error: {result.stderr}")
                
    finally:
        # Cleanup
        os.unlink(temp_fasta)
