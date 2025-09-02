#!/usr/bin/env python3

"""
Unit tests for the BaseMmseqsCommandline framework.

This module tests the base command-line wrapper functionality including
parameter validation, command-line construction, and subprocess execution.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess

# Import our new application framework
from pymmseqs.application import (
    BaseMmseqsCommandline, 
    MmseqsParameter, 
    MmseqsCommandResult,
    create_input_file_parameter,
    create_output_file_parameter, 
    create_option_parameter,
    create_flag_parameter
)


class TestMmseqsParameter(unittest.TestCase):
    """Test the MmseqsParameter class."""
    
    def test_parameter_creation(self):
        """Test basic parameter creation."""
        param = MmseqsParameter(
            name="test_param",
            flag="--test",
            description="A test parameter",
            param_type="option",
            value_type=int,
            default=42
        )
        
        self.assertEqual(param.name, "test_param")
        self.assertEqual(param.flag, "--test")
        self.assertEqual(param.value_type, int)
        self.assertEqual(param.default, 42)
    
    def test_invalid_parameter_type(self):
        """Test that invalid parameter types raise ValueError."""
        with self.assertRaises(ValueError):
            MmseqsParameter(
                name="test",
                flag="--test", 
                description="test",
                param_type="invalid_type"  # This should fail
            )
    
    def test_value_validation_type_conversion(self):
        """Test type conversion in value validation."""
        param = MmseqsParameter(
            name="int_param",
            flag="--int", 
            description="Integer parameter",
            param_type="option",
            value_type=int,
            default=0
        )
        
        # Should convert string to int
        result = param.validate_value("42")
        self.assertEqual(result, 42)
        self.assertIsInstance(result, int)
    
    def test_value_validation_choices(self):
        """Test choice validation."""
        param = MmseqsParameter(
            name="choice_param",
            flag="--choice",
            description="Choice parameter", 
            param_type="option",
            choices=["a", "b", "c"],
            default="a"
        )
        
        # Valid choice should pass
        result = param.validate_value("b")
        self.assertEqual(result, "b")
        
        # Invalid choice should fail
        with self.assertRaises(ValueError):
            param.validate_value("d")
    
    def test_value_validation_required(self):
        """Test required parameter validation."""
        param = MmseqsParameter(
            name="required_param",
            flag="--required",
            description="Required parameter",
            param_type="option", 
            required=True
        )
        
        # None value for required parameter should fail
        with self.assertRaises(ValueError):
            param.validate_value(None)
    
    def test_file_validation(self):
        """Test input file validation."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test content")
            tmp_path = tmp.name
        
        try:
            param = MmseqsParameter(
                name="input_file",
                flag="--input",
                description="Input file",
                param_type="input_file"
            )
            
            # Existing file should pass
            result = param.validate_value(tmp_path)
            self.assertEqual(result, tmp_path)
            
            # Non-existent file should fail
            with self.assertRaises(FileNotFoundError):
                param.validate_value("/non/existent/file.txt")
                
        finally:
            os.unlink(tmp_path)
    
    def test_format_for_command_line_option(self):
        """Test command-line formatting for option parameters."""
        param = MmseqsParameter(
            name="test_option",
            flag="--test",
            description="Test option",
            param_type="option"
        )
        
        result = param.format_for_command_line("value")
        self.assertEqual(result, ["--test", "value"])
    
    def test_format_for_command_line_flag(self):
        """Test command-line formatting for flag parameters.""" 
        param = MmseqsParameter(
            name="test_flag",
            flag="--flag",
            description="Test flag",
            param_type="flag"
        )
        
        # True flag should include the flag
        result = param.format_for_command_line(True)
        self.assertEqual(result, ["--flag"])
        
        # False flag should be empty
        result = param.format_for_command_line(False)
        self.assertEqual(result, [])
    
    def test_format_for_command_line_multiple(self):
        """Test command-line formatting for multiple values."""
        param = MmseqsParameter(
            name="multi_param", 
            flag="--multi",
            description="Multiple values",
            param_type="option",
            multiple=True
        )
        
        result = param.format_for_command_line(["val1", "val2"])
        self.assertEqual(result, ["--multi", "val1", "--multi", "val2"])


class TestMmseqsCommandResult(unittest.TestCase):
    """Test the MmseqsCommandResult class."""
    
    def test_result_creation(self):
        """Test basic result creation."""
        result = MmseqsCommandResult(
            returncode=0,
            stdout="output",
            stderr="",
            command_line=["mmseqs", "createdb", "input", "output"]
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.stdout, "output")
        
    def test_result_failure(self):
        """Test result with failure."""
        result = MmseqsCommandResult(
            returncode=1,
            stdout="", 
            stderr="error",
            command_line=["mmseqs", "createdb"]
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.stderr, "error")
    
    def test_command_string_property(self):
        """Test the command_string property."""
        result = MmseqsCommandResult(
            returncode=0,
            stdout="",
            stderr="",
            command_line=["mmseqs", "createdb", "file with spaces.fasta", "output"]
        )
        
        cmd_str = result.command_string
        self.assertIn("'file with spaces.fasta'", cmd_str)  # Should be quoted


class MockMmseqsCommand(BaseMmseqsCommandline):
    """Mock implementation of BaseMmseqsCommandline for testing."""
    
    @property
    def command_name(self) -> str:
        return "mock-command"
    
    def _init_parameters(self) -> None:
        """Initialize test parameters."""
        self.add_parameter(create_input_file_parameter(
            name="input_file", 
            flag="",  # Positional argument
            description="Input file",
            required=True
        ))
        
        self.add_parameter(create_output_file_parameter(
            name="output_file",
            flag="",  # Positional argument  
            description="Output file",
            required=True
        ))
        
        self.add_parameter(create_option_parameter(
            name="min_seq_id",
            flag="--min-seq-id",
            description="Minimum sequence identity",
            value_type=float,
            default=0.0
        ))
        
        self.add_parameter(create_flag_parameter(
            name="verbose",
            flag="-v",
            description="Verbose output"
        ))


class TestBaseMmseqsCommandline(unittest.TestCase):
    """Test the BaseMmseqsCommandline base class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary test files
        self.temp_dir = tempfile.mkdtemp()
        self.input_file = os.path.join(self.temp_dir, "input.fasta")
        self.output_file = os.path.join(self.temp_dir, "output")
        
        with open(self.input_file, "w") as f:
            f.write(">seq1\nAAAA\n>seq2\nCCCC\n")
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_command_initialization(self):
        """Test basic command initialization."""
        cmd = MockMmseqsCommand()
        
        # Should have the expected parameters
        params = cmd.list_parameters()
        expected_params = ["input_file", "output_file", "min_seq_id", "verbose"]
        for param in expected_params:
            self.assertIn(param, params)
    
    def test_parameter_setting_and_getting(self):
        """Test setting and getting parameter values."""
        cmd = MockMmseqsCommand()
        
        cmd.set_parameter("min_seq_id", 0.5)
        self.assertEqual(cmd.get_parameter("min_seq_id"), 0.5)
        
        cmd.set_parameter("verbose", True)
        self.assertTrue(cmd.get_parameter("verbose"))
    
    def test_invalid_parameter_name(self):
        """Test that setting invalid parameter raises ValueError."""
        cmd = MockMmseqsCommand()
        
        with self.assertRaises(ValueError):
            cmd.set_parameter("non_existent", "value")
        
        with self.assertRaises(ValueError):
            cmd.get_parameter("non_existent")
    
    def test_parameter_validation(self):
        """Test parameter validation."""
        cmd = MockMmseqsCommand()
        
        # Setting invalid type should raise ValueError
        with self.assertRaises(ValueError):
            cmd.set_parameter("min_seq_id", "not_a_number")
    
    def test_build_command_line_basic(self):
        """Test basic command line building."""
        cmd = MockMmseqsCommand()
        cmd.set_parameter("input_file", self.input_file)
        cmd.set_parameter("output_file", self.output_file)
        
        cmd_line = cmd.build_command_line()
        
        # Should start with command name
        self.assertEqual(cmd_line[0], "mock-command")
        
        # Should include input and output files as positional args
        self.assertIn(self.input_file, cmd_line)
        self.assertIn(self.output_file, cmd_line)
    
    def test_build_command_line_with_options(self):
        """Test command line building with options."""
        cmd = MockMmseqsCommand()
        cmd.set_parameter("input_file", self.input_file)
        cmd.set_parameter("output_file", self.output_file)
        cmd.set_parameter("min_seq_id", 0.8)
        cmd.set_parameter("verbose", True)
        
        cmd_line = cmd.build_command_line()
        
        # Should include option parameters
        self.assertIn("--min-seq-id", cmd_line)
        self.assertIn("0.8", cmd_line)
        self.assertIn("-v", cmd_line)
    
    def test_validation_missing_required(self):
        """Test validation fails with missing required parameters."""
        cmd = MockMmseqsCommand()
        # Don't set required parameters
        
        with self.assertRaises(ValueError):
            cmd.validate_parameters()
    
    def test_validation_nonexistent_input_file(self):
        """Test validation fails with non-existent input file."""
        cmd = MockMmseqsCommand()
        
        # Setting non-existent input file should fail immediately
        with self.assertRaises(FileNotFoundError):
            cmd.set_parameter("input_file", "/non/existent/file.fasta")
    
    @patch('pymmseqs.utils.get_mmseqs_binary')
    @patch('subprocess.run')
    def test_run_command_success(self, mock_subprocess_run, mock_get_binary):
        """Test successful command execution."""
        # Setup mocks
        mock_get_binary.return_value = "/usr/local/bin/mmseqs"
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Success output"
        mock_result.stderr = ""
        mock_subprocess_run.return_value = mock_result
        
        # Setup command
        cmd = MockMmseqsCommand()
        cmd.set_parameter("input_file", self.input_file)
        cmd.set_parameter("output_file", self.output_file)
        
        # Run command
        result = cmd.run()
        
        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.stdout, "Success output")
        
        # Verify subprocess was called correctly
        mock_subprocess_run.assert_called_once()
        call_args = mock_subprocess_run.call_args
        self.assertEqual(call_args[0][0][0], "/usr/local/bin/mmseqs")  # Binary path
        self.assertEqual(call_args[0][0][1], "mock-command")     # Command name
    
    @patch('pymmseqs.utils.get_mmseqs_binary')
    @patch('subprocess.run') 
    def test_run_command_failure(self, mock_subprocess_run, mock_get_binary):
        """Test failed command execution."""
        # Setup mocks
        mock_get_binary.return_value = "/usr/bin/mmseqs"
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error occurred"
        mock_subprocess_run.return_value = mock_result
        
        # Setup command
        cmd = MockMmseqsCommand()
        cmd.set_parameter("input_file", self.input_file)
        cmd.set_parameter("output_file", self.output_file)
        
        # Run command with check=True (default) should raise exception
        with self.assertRaises(subprocess.CalledProcessError):
            cmd.run()
        
        # Run command with check=False should return result
        result = cmd.run(check=False)
        self.assertFalse(result.success)
        self.assertEqual(result.stderr, "Error occurred")
    
    def test_string_representation(self):
        """Test string representations of command."""
        cmd = MockMmseqsCommand()
        cmd.set_parameter("input_file", self.input_file)
        cmd.set_parameter("output_file", self.output_file)
        
        # Test __str__
        str_repr = str(cmd)
        self.assertIn("mock-command", str_repr)
        self.assertIn(self.input_file, str_repr)
        
        # Test __repr__
        repr_str = repr(cmd)
        self.assertIn("MockMmseqsCommand", repr_str)
    
    def test_callable_interface(self):
        """Test that command objects are callable."""
        with patch('pymmseqs.utils.get_mmseqs_binary') as mock_get_binary, \
             patch('subprocess.run') as mock_subprocess_run:
            
            mock_get_binary.return_value = "/usr/bin/mmseqs"
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "output"
            mock_result.stderr = ""
            mock_subprocess_run.return_value = mock_result
            
            cmd = MockMmseqsCommand()
            cmd.set_parameter("input_file", self.input_file)
            cmd.set_parameter("output_file", self.output_file)
            
            # Should be able to call the command object directly
            result = cmd()
            self.assertTrue(result.success)


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions for creating parameters."""
    
    def test_create_input_file_parameter(self):
        """Test input file parameter creation."""
        param = create_input_file_parameter(
            name="input_file",
            description="Test input file",
            required=True
        )
        
        self.assertEqual(param.name, "input_file")
        self.assertEqual(param.param_type, "input_file") 
        self.assertTrue(param.required)
    
    def test_create_output_file_parameter(self):
        """Test output file parameter creation."""
        param = create_output_file_parameter(
            name="output_file",
            description="Test output file"
        )
        
        self.assertEqual(param.name, "output_file")
        self.assertEqual(param.param_type, "output_file")
        self.assertTrue(param.required)
    
    def test_create_option_parameter(self):
        """Test option parameter creation."""
        param = create_option_parameter(
            name="min_seq_id",
            description="Minimum sequence identity",
            value_type=float,
            default=0.5,
            choices=[0.0, 0.5, 1.0]
        )
        
        self.assertEqual(param.name, "min_seq_id")
        self.assertEqual(param.param_type, "option")
        self.assertEqual(param.value_type, float)
        self.assertEqual(param.default, 0.5)
        self.assertEqual(param.choices, [0.0, 0.5, 1.0])
    
    def test_create_flag_parameter(self):
        """Test flag parameter creation."""
        param = create_flag_parameter(
            name="verbose",
            description="Enable verbose output",
            default=False
        )
        
        self.assertEqual(param.name, "verbose")
        self.assertEqual(param.param_type, "flag")
        self.assertEqual(param.value_type, bool)
        self.assertFalse(param.default)


if __name__ == "__main__":
    unittest.main()
