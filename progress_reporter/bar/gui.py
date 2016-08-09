
'''
Created on 24.04.2015

@author: marscher
'''

from __future__ import absolute_import

import sys
import warnings

from . import ProgressBar


__all__ = ('is_interactive_session', 'show_progressbar')


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
            return None
        else:
            return 3
    else:
        return 4


def __attached_to_ipy_notebook():
    # first determine which IPython version we have (eg. ipywidgets or ipy3 deprecated,
    # then try to instanciate a widget to determine if we're interactive (raises, if not).
    if 'IPython' not in sys.modules:
        return
    ipy_widget_version = __ipy_widget_version()

    if ipy_widget_version is None:
        return False

    if ipy_widget_version == 4:
        from ipywidgets import Box
    elif ipy_widget_version == 3:
        from IPython.html.widgets import Box
    # FIXME: this unfortunately does not raise if frontend is QT...
    try:
        Box()
    except:
        return False
    else:
        return True


def __is_interactive():
    # started by main function or interactive from python shell?
    import __main__ as main
    return not hasattr(main, '__file__')


def __is_tty_or_interactive_session():
    is_tty = sys.stdout.isatty()
    is_interactive = __is_interactive()
    result = is_tty or is_interactive
    return result

ipython_notebook_session = __attached_to_ipy_notebook()
""" are we running an interactive IPython notebook session """

is_interactive_session = __is_tty_or_interactive_session()
""" do we have a tty or an interactive session? """


if ipython_notebook_session:
    from IPython.display import display
    __widget_version = __ipy_widget_version()
    __widget_version = __widget_version if __widget_version is not None else 0

    if __widget_version >= 4:
        from ipywidgets import Box, Text, IntProgress
    elif __widget_version == 3:
        from IPython.html.widgets import Box, Text, IntProgress


def hide_widget(widget):
    widget.close()


def hide_progressbar(bar):

    if ipython_notebook_session and hasattr(bar, 'widget'):
        # TODO: close the widget in browser (eg. via Javascript)
        from threading import Timer
        timeout = 2
        Timer(timeout, hide_widget, args=(bar.widget, )).start()
        #import time
        #time.sleep(0.5)
        #bar.widget.close()

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
    # note: this check ensures we have IPython.display and so on.
    if ipython_notebook_session and isinstance(bar, ProgressBar):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', DeprecationWarning)
            # create IPython widgets on first call
            if not hasattr(bar, 'widget'):

                box = Box()
                text = Text()
                progress_widget = IntProgress()

                box.children = [text, progress_widget]
                bar.widget = box
                widget = box

                # make it visible once
                display(box)

                # update css for a more compact view
                progress_widget._css = [
                    ("div", "margin-top", "0px")
                ]
                progress_widget.height = "8px"
            else:
                widget = bar.widget

            # update widgets slider value and description text
            desc = description
            if show_eta:
                desc += ':\tETA:' + bar._generate_eta(bar._eta.eta_seconds)
            assert isinstance(widget.children[0], Text)
            assert isinstance(widget.children[1], IntProgress)
            widget.children[0].placeholder = desc
            widget.children[1].value = bar.percent
    else:
        sys.stdout.write("\r" + str(bar))
        sys.stdout.flush()
