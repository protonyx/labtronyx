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

    # Keep the main thread alive
    while(1):
        time.sleep(1.0)

if __name__ == "__main__":
    main()

