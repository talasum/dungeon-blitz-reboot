import builtins
import traceback


CONSOLE_OUTPUT_ENABLED = False

_ORIGINAL_PRINT = builtins.print
_ORIGINAL_TRACEBACK_PRINT_EXC = traceback.print_exc


def console_output_enabled() -> bool:
    return CONSOLE_OUTPUT_ENABLED


def set_console_output(enabled: bool) -> None:
    global CONSOLE_OUTPUT_ENABLED
    CONSOLE_OUTPUT_ENABLED = bool(enabled)


def console_print(*args, **kwargs):
    return _ORIGINAL_PRINT(*args, **kwargs)


def install_console_output_override() -> None:
    def guarded_print(*args, **kwargs):
        if CONSOLE_OUTPUT_ENABLED:
            return _ORIGINAL_PRINT(*args, **kwargs)
        return None

    def guarded_print_exc(*args, **kwargs):
        if CONSOLE_OUTPUT_ENABLED:
            return _ORIGINAL_TRACEBACK_PRINT_EXC(*args, **kwargs)
        return None

    builtins.print = guarded_print
    traceback.print_exc = guarded_print_exc
