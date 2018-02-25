from pawt.exceptions import TooLong


def chunk(func):
    """Retry a function's sending if it sends something that is too long.

    This decorator assumes that only one message will be attempted to be sent, or at least that the potentially too
    long message will be the last.
    """

    def chunk_wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except TooLong as tl:
            tl.send_chunked()

    return chunk_wrapper
