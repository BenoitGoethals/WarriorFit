class Formatter:

    @staticmethod
    def format_time(seconds):
        if seconds is None:
            return "-"
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"