"""
Console script used to start Labtronyx in Server mode
"""
import os


def main(search_dirs=None):
    # Interactive Mode
    import labtronyx
    labtronyx.logConsole()

    # Add OS-specific application data folders to search for plugins
    if search_dirs is None:
        search_dirs = []

    try:
        import appdirs
        dirs = appdirs.AppDirs("Labtronyx", roaming=True)
        if not os.path.exists(dirs.site_data_dir):
            os.makedirs(dirs.site_data_dir)
        search_dirs.append(dirs.site_data_dir)

        if not os.path.exists(dirs.user_data_dir):
            os.makedirs(dirs.user_data_dir)
        search_dirs.append(dirs.user_data_dir)
    except:
        pass

    # Instantiate an InstrumentManager
    man = labtronyx.InstrumentManager(plugin_dirs=search_dirs)

    # Start the server in the current thread
    try:
        man.server_start(new_thread=False)
    except KeyboardInterrupt:
        man.server_stop()

if __name__ == "__main__":
    main()

