
'''
Created on 24.04.2015

@author: marscher
'''

from __future__ import absolute_import

import sys
import warnings

from functools import wraps

from . import ProgressBar


__all__ = ('is_interactive_session', 'show_progressbar')


def _simple_memorize(f):
    # cache function f result (takes no arguments)
    @wraps(f)
    def wrapper():
        if not hasattr(f, 'res'):
            f.res = f()
        return f.res
    return wrapper


@_simple_memorize
def __ipy_widget_version():
    try:
        import ipywidgets
    except ImportError:
        import warnings
        try:
            # hide future warning of ipython and show custom message
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                from IPython.html.widgets import Box
            warnings.warn("Consider upgrading to Jupyter (new IPython version) and ipywidgets.",
                          DeprecationWarning)
        except ImportError:
            ver = 0
        else:
            ver = 3
    else:
        ver = 4
    return ver


@_simple_memorize
def __attached_to_ipy_notebook():
    # check if we have an ipython kernel
    try:
        from IPython import get_ipython
        ip = get_ipython()
        if ip is None:
            return False
        if not getattr(ip, 'kernel', None):
            return False
        # No further checks are feasible
        return True
    except ImportError:
        return False


def __is_interactive():
    # started by main function or interactive from python shell?
    import __main__ as main
    return not hasattr(main, '__file__')


def __is_tty_or_interactive_session():
    is_tty = sys.stdout.isatty()
    is_interactive = __is_interactive()
    result = is_tty or is_interactive
    return result

ipython_notebook_session = None
""" are we running an interactive IPython notebook session """

is_interactive_session = __is_tty_or_interactive_session()
""" do we have a tty or an interactive session? """


def hide_widget(widget):
    widget.close()


def hide_progressbar(bar):

    if ipython_notebook_session and hasattr(bar, 'widget'):
        # TODO: close the widget in browser (eg. via Javascript)
        from threading import Timer
        timeout = 2
        Timer(timeout, hide_widget, args=(bar.widget, )).start()


def _create_widget():
    __widget_version = __ipy_widget_version()
    if __widget_version >= 4:
        from ipywidgets import Box, Text, IntProgress
    elif __widget_version == 3:
        from IPython.html.widgets import Box, Text, IntProgress
    else:
        #warnings.warn("no widgets possible")
        return None

    box = Box()
    text = Text()
    progress_widget = IntProgress()

    box.children = [text, progress_widget]

    # # make it visible once
    # display(box)

    # update css for a more compact view
    progress_widget._css = [
        ("div", "margin-top", "0px")
    ]
    progress_widget.height = "8px"
    return box


def show_progressbar(bar, show_eta=True, description=''):
    """ shows given bar either using an ipython widget, if in
    interactive session or simply use the string format of it and print it
    to stdout.

    Parameters
    ----------
    bar : instance of progress_reporter.bar.ProgressBar
    show_eta : bool (optional)

    show_eta: bool

    description: str

    """
    global ipython_notebook_session
    if ipython_notebook_session is None:
        # note: this check ensures we have IPython.display and so on.
        ipython_notebook_session = __attached_to_ipy_notebook()

    if ipython_notebook_session and isinstance(bar, ProgressBar):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', DeprecationWarning)
            # create widget on first call
            if not hasattr(bar, 'widget'):
                from IPython.display import display
                widget = _create_widget()
                if widget is None:
                    ipython_notebook_session = False
                    sys.stdout.write("\r{}".format(bar))
                    sys.stdout.flush()
                    return
                bar.widget = widget
                # # make it visible once
                display(widget)
            else:
                widget = bar.widget

            # update widgets slider value and description text
            desc = description
            if show_eta:
                desc += ':\tETA:' + bar._generate_eta(bar._eta.eta_seconds)
            widget.children[0].placeholder = desc
            widget.children[1].value = bar.percent
    else:
        sys.stdout.write("\r{}".format(bar))
        sys.stdout.flush()
