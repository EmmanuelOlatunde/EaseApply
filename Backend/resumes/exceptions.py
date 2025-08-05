class ResumeError(Exception):
    """Base exception for resume-related errors"""
    pass

class FileProcessingError(ResumeError):
    """Exception raised when file processing fails"""
    pass

class ParseError(ResumeError):
    """Exception raised when resume parsing fails"""
    pass

class ValidationError(ResumeError):
    """Exception raised when resume validation fails"""
    pass