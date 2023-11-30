import curses
import time
import threading
from functools import wraps

def progress_bar(step, length):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            stdscr = args[0].stdscr
            def update_progress(progress):
                progress_win.clear()
                # progress_win.border()
                progress_win.addstr(1, 0, f"{progress}%")
                progress_bar_width = width - 10
                filled_width = int(progress / length * progress_bar_width)
                progress_win.addstr(1, 6, ">" * filled_width )
                progress_win.refresh()

            height, width = stdscr.getmaxyx()

            # creat the window of progress bar
            progress_win = curses.newwin(3, width - 4, height // 2 - 1, 2)
            progress_win.border()

            # set the progress bar initial value
            progress_min = 0

            # Simulated progress update
            for index, progress in enumerate(func(*args, **kwargs)):
                progress += (index + 1) * step
                progress = round(progress, 1)
                if progress < length:
                    update_progress(progress)
                else:
                    update_progress(length)

            stdscr.getch()
            curses.endwin()

        return wrapper
    return decorator