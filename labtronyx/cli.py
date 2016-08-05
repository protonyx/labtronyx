"""
Console script used to start Labtronyx in Server mode
"""
import os
import argparse
import appdirs

import labtronyx
import labtronyx.gui
labtronyx.logConsole()


def main(search_dirs=None):
    parse = argparse.ArgumentParser(description="Labtronyx Automation Framework")
    parse.add_argument('-g', dest='gui', action='store_const', const=True)
    parse.add_argument('-d', dest='dirs', nargs='*', help='plugin search directory')
    args = parse.parse_args()

    if args.gui:
        launch_gui()
        return
    
    # Add OS-specific application data folders to search for plugins
    if search_dirs is None:
        search_dirs = []

    dirs = appdirs.AppDirs("Labtronyx", roaming=True)
    if not os.path.exists(dirs.site_data_dir):
        os.makedirs(dirs.site_data_dir)
    search_dirs.append(dirs.site_data_dir)

    if not os.path.exists(dirs.user_data_dir):
        os.makedirs(dirs.user_data_dir)
    search_dirs.append(dirs.user_data_dir)

    if args.dirs is not None:
        search_dirs += args.dirs

    # Instantiate an InstrumentManager
    man = labtronyx.InstrumentManager(plugin_dirs=search_dirs)

    # Start the server in the current thread
    try:
        man.server_start(new_thread=False)
    except KeyboardInterrupt:
        man.server_stop()


def launch_gui():
    controller = labtronyx.gui.controllers.MainApplicationController()
    labtronyx.gui.wx_views.wx_main.main(controller)
    controller._stop()


if __name__ == "__main__":
    main()

