"""A function that displays a progress bar in the console as a long-running task completes.

Author: Alan Weide
Copyright 2022
"""

import shutil

def progressbar(itr, *,
        prefix="",
        suffix="",
        completion="Done.",
        indicator='█',
        fill=' ',
        total_width=None,
        len_estimate=None):
# pylint: disable-msg=too-many-locals
    """Modified from https://stackoverflow.com/questions/3160699/python-progress-bar/3162864.

    Progressbar is a generator function for the iterable `itr` that displays a progress bar as
    iteration progresses. The statement
        for x in progressbar(itr):
            ...
    is a drop-in replacement for the statement
        for x in itr:
            ...
    at least as far as the behavior is concerned (obviously, output will differ). It is important
    that there is no stdout printing being done in the loop body or in `itr`; the progress bar will
    not be displayed properly if there is.

    `itr` must have a length that is computable a priori via the `len` function; if it does not,
        the keyword parameter `len_estimate` must be supplied. `itr` is the only required
        parameter.

    `prefix`, `suffix`, and `completion` are the messages that should be displayed on the left side
        of the progress bar, the right side of the progress bar, and in the console when the task
        is complete.

    `indicator` and `fill` must each be single-character strings. For "pretty" output, they should
        also print one character wide (the `len` function does not guarantee this fact).

    `total_width`, if not supplied, will be computed as the width of the terminal window in which
        this program is being run, defaulting to 80 if the terminal width cannot be ascertained.

    NOTE: This function has been tested on MacOS and the Zoo. I make no promises that it works on
        other systems.
    """

    assert len(indicator) == 1, "Indicator must be exactly one character long."
    assert len(fill) == 1, "Fill must be exactly one character long."

    total_width = total_width or shutil.get_terminal_size().columns

    if suffix:
        suffix = ' ' + suffix

    if prefix:
        prefix = prefix + ' '

    try:
        total_items = len(itr)
        est_mark = ''
    except TypeError as ex:
        if len_estimate is None:
            raise ex
        total_items = len_estimate
        est_mark = '(estimated)'

    format_string = "{prefix}[{progress}{fill}] {cdone:>{0}}/{total}{emark}{suffix}"
    empty_bar = format_string.format(len(str(total_items)),
        prefix=prefix,
        progress="",
        fill="",
        cdone=total_items,
        total=total_items,
        emark=est_mark,
        suffix=suffix)

    bar_width = total_width - len(empty_bar)

    def show_bar_at_count(n_complete):
        curr_width = min(int(bar_width * n_complete / total_items), bar_width)
        progress = indicator * curr_width
        remaining = fill * (bar_width - curr_width)
        print(
            format_string.format(len(str(total_items)),
                prefix=prefix,
                progress=progress,
                fill=remaining,
                cdone=n_complete,
                total=total_items,
                emark=est_mark,
                suffix=suffix),
            end='\r\r', flush=True)

    show_bar_at_count(0)
    for i, item in enumerate(itr):
        yield item
        show_bar_at_count(i+1)

    if completion:
        print(f"\n{completion}")
    else:
        print()
