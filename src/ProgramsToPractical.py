import docs
import local
from tkinter import filedialog, Tk

root = Tk()
root.withdraw()
path = filedialog.askdirectory(
    mustexist=True,
    initialdir=r"D:\Ankur\Programs\Python\School",
    title="Pick practical folder",
    parent=root
).replace("/", "\\")
practical = local.extract_from_practical(path)
docs.make_requests(practical)