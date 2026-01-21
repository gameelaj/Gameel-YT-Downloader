import tkinter as tk
from gui.main_window import YTDLPGui

def main():
    root = tk.Tk()
    # Optional: Set icon if you have one
    # try: root.iconbitmap("icon.ico")
    # except: pass
    
    app = YTDLPGui(root)
    root.mainloop()

if __name__ == "__main__":
    main()