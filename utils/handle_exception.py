import functools
import traceback
import logging
from discord.ext import commands
import inspect


def handle_exception(logger: "logging.Logger | None" = None):
    def decorator(func):
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if logger:
                        logger.exception(e)
                    else:
                        self = args[0] if len(args) > 0 else None
                        ctx = args[1] if len(args) > 1 else None
                        if (
                            self is not None
                            and hasattr(self, "logger")
                            and type(self.logger) == logging.Logger
                        ):
                            self.logger.exception(e)
                            if ctx is not None and type(ctx) == commands.Context:
                                await ctx.send(
                                    "An error occurred. Please report this to the developer."
                                )
                        else:
                            traceback.print_exc()
                    return None

            return async_wrapper
        else:

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if logger:
                        logger.exception(e)
                    else:
                        self = args[0] if len(args) > 0 else None
                        if (
                            self is not None
                            and hasattr(self, "logger")
                            and type(self.logger) == logging.Logger
                        ):
                            self.logger.exception(e)
                        else:
                            traceback.print_exc()
                    return None

            return wrapper

    return decorator
