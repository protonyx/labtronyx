"""
Console script used to start Labtronyx in Server mode
"""
import time

def main():
    # Interactive Mode
    import labtronyx
    labtronyx.logConsole()

    # Instantiate an InstrumentManager
    man = labtronyx.InstrumentManager(rpc=True)

    # Force a refresh
    man.refresh()

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        man.rpc_stop()

if __name__ == "__main__":
    main()

