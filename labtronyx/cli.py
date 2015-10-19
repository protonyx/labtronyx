"""
Console script used to start Labtronyx in Server mode
"""
import time

def main():
    # Interactive Mode
    import labtronyx
    labtronyx.logConsole()

    # Instantiate an InstrumentManager
    man = labtronyx.InstrumentManager()

    # Force a refresh
    man.refresh()

    # Start the server in the current thread
    try:
        man.server_start(new_thread=False)
    except KeyboardInterrupt:
        man.server_stop()

if __name__ == "__main__":
    main()

