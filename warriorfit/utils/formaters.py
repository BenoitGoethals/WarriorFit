class Formatter:
    """
    Provides utility functions for formatting time-related values.

    This class offers a static method to format a given time value, provided
    in seconds, into a human-readable string in the format ``HH:MM:SS``.
    It is useful for displaying time in an easily interpretable format.
    """

    @staticmethod
    def format_time(seconds):
        if seconds is None:
            return "-"
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
