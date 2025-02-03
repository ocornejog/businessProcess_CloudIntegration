import json
import logging
from datetime import datetime
import os
from pathlib import Path
from typing import Dict, Any
from decimal import Decimal

class ProcessLogger:
    def __init__(self, base_dir: str = "logs"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different log types
        self.detailed_logs_dir = self.base_dir / "detailed_logs"
        self.json_logs_dir = self.base_dir / "json_logs"
        self.detailed_logs_dir.mkdir(exist_ok=True)
        self.json_logs_dir.mkdir(exist_ok=True)
        
        # Initialize log handlers
        self._setup_logging()
        
        self.process_data = {
            'start_time': datetime.now().isoformat(),
            'steps': [],
            'completion_status': None,
            'process_duration': None
        }

    def _setup_logging(self):
        """Set up logging configuration"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create a formatter for detailed logs
        detailed_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s]\n'
            'Step: %(message)s\n'
            '%(separator)s\n'
        )
        
        # Set up file handler for detailed logs
        detailed_log_file = self.detailed_logs_dir / f"loan_process_{timestamp}.log"
        file_handler = logging.FileHandler(detailed_log_file, encoding='utf-8')
        file_handler.setFormatter(detailed_formatter)
        
        # Configure logger
        self.logger = logging.getLogger(f"loan_process_{timestamp}")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        
        # Store the JSON log file path
        self.json_log_file = self.json_logs_dir / f"loan_process_{timestamp}.json"

    def log_step(self, step: str, details: Dict[str, Any] = None):
        """Log a process step with details"""
        # Ensure details is a dictionary and handle None
        details = details or {}
        
        # Convert any Decimal values to strings
        details = self._convert_decimals(details)
        
        # Format details for readable logging
        details_str = json.dumps(details, indent=2) if details else ""
        separator = "="*80
        
        # Log to detailed log file
        self.logger.info(
            step,
            extra={
                'separator': f"{separator}\n{details_str}\n{separator}"
            }
        )
        
        # Store step data for JSON logging
        step_data = {
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'details': details
        }
        self.process_data['steps'].append(step_data)
        
        # Update JSON file after each step
        self._save_json_log()

    def _convert_decimals(self, data: Any) -> Any:
        """Recursively convert Decimal objects to strings in dictionaries and lists"""
        if isinstance(data, dict):
            return {k: self._convert_decimals(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_decimals(item) for item in data]
        elif isinstance(data, Decimal):
            return str(data)
        return data

    def finalize_process(self, final_status: str, summary: Dict[str, Any] = None):
        """Finalize the process log with summary information"""
        self.process_data['completion_status'] = final_status
        self.process_data['end_time'] = datetime.now().isoformat()
        self.process_data['process_duration'] = (
            datetime.fromisoformat(self.process_data['end_time']) -
            datetime.fromisoformat(self.process_data['start_time'])
        ).total_seconds()
        
        if summary:
            self.process_data['summary'] = summary
        
        # Log final summary
        self.log_step(
            "Process Completed",
            {
                'final_status': final_status,
                'duration_seconds': self.process_data['process_duration'],
                'summary': summary
            }
        )
        
        # Final JSON save
        self._save_json_log()

    def _save_json_log(self):
        """Save the current process data to JSON file"""
        # Convert any Decimal values before saving
        process_data = self._convert_decimals(self.process_data)
        with open(self.json_log_file, 'w', encoding='utf-8') as f:
            json.dump(process_data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def load_process_log(json_file_path: str) -> Dict[str, Any]:
        """Load and return a previously saved process log"""
        with open(json_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)