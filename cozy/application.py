import logging
import os
import platform
import sys
import threading
from pathlib import Path
from traceback import format_exception

import distro
from gi.repository import Adw, GLib

from cozy.app_controller import AppController
from cozy.control.db import init_db
from cozy.control.mpris import MPRIS
from cozy.db.settings import Settings
from cozy.db.storage import Storage
from cozy.report import reporter
from cozy.ui.main_view import CozyUI
from cozy.ui.widgets.filter_list_box import FilterListBox
from cozy.version import __version__

log = logging.getLogger("application")


class Application(Adw.Application):
    ui: CozyUI
    app_controller: AppController

    def __init__(self, pkgdatadir: str):
        self.pkgdatadir = pkgdatadir

        super().__init__(application_id='com.github.geigi.cozy')
        self.init_custom_widgets()

        GLib.setenv("PULSE_PROP_media.role", "music", True)
        GLib.set_application_name("Cozy")

        threading.excepthook = self.handle_exception

    def do_startup(self):
        log.info(distro.linux_distribution(full_distribution_name=False))
        log.info(f"Starting up cozy {__version__}")
        log.info(f"libadwaita version: {Adw._version}")

        self.ui = CozyUI(self.pkgdatadir, self, __version__)
        Adw.Application.do_startup(self)
        init_db()
        self.ui.startup()

    def do_activate(self):
        main_window_builder = self.ui.get_builder()
        self.app_controller = AppController(self, main_window_builder, self.ui)

        self.ui.activate(self.app_controller.library_view)

        if Settings.get().first_start:
            Settings.update(first_start=False).execute()

            path = os.path.join(Path.home(), _("Audiobooks"))
            Storage.create(path=path, default=True)

            os.makedirs(path, exist_ok=True)

        self.add_window(self.ui.window)

        if platform.system().lower() == "linux":
            mpris = MPRIS(self)
            mpris._on_current_changed()

    def handle_exception(self, _):
        print("handle exception")

        exc_type, exc_value, exc_traceback = sys.exc_info()

        if exc_type is SystemExit:
            return

        try:
            reporter.exception("uncaught", exc_value, "\n".join(format_exception(exc_type, exc_value, exc_traceback)))
        finally:
            sys.excepthook(exc_type, exc_value, exc_traceback)

    def quit(self):
        self.app_controller.quit()
        super(Application, self).quit()

    @staticmethod
    def init_custom_widgets():
        FilterListBox()
