# Load GUI in interactive mode
if __name__ == "__main__":
    # Load Application GUI
    
    try:
        #sys.path.append("..")
        from application.a_Main import a_Main
        main_gui = a_Main()
        main_gui.mainloop()
         
    except Exception as e:
        print "Unable to load main application"
        raise
        sys.exit()