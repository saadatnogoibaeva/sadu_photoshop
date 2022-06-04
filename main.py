from tkinter import *
from tkinter import filedialog as fd
from tkinter import messagebox as mb
from tkinter.ttk import Notebook
from PIL import Image, ImageTk, ImageOps, ImageFilter, ImageEnhance
import os
import shutil
import pyperclip
import json
import numpy as np

CONFIG_FILE = "config.json"


class SaadatPhotoEditor:
    def __init__(self):
        self.root = Tk()
        self.image_tabs = Notebook(self.root)
        self.opened_images = []
        self.last_viewed_images = []

        self.open_recent_menu = None

    def init(self):
        self.root.title("Easy photoshop")
        self.root.iconphoto(True, PhotoImage(file="icon/alatoo.jpg"))
        self.image_tabs.enable_traversal()

        self.root.bind("<Escape>", self._close)
        self.root.protocol("WM_DELETE_WINDOW", self._close)

        if not os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'w') as f:
                json.dump({"opened_images": [], "last_viewed_images": []}, f)
        else:
            self.load_images_from_config()

    def run(self):
        self.draw_menu()
        self.draw_widgets()

        self.root.mainloop()

    def draw_menu(self):
        menu_bar = Menu(self.root)

        file_menu = Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_new_images)


        file_menu.add_separator()
        file_menu.add_command(label="Save", command=self.save_current_image)
        file_menu.add_separator()

        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._close)
        menu_bar.add_cascade(label="File", menu=file_menu)

        edit_menu = Menu(menu_bar, tearoff=0)
        transform_menu = Menu(edit_menu, tearoff=0)


        filter_menu = Menu(edit_menu, tearoff=0)
        filter_menu.add_command(label="Blur", command=lambda: self.apply_filter_to_current_image(ImageFilter.BLUR))
        filter_menu.add_command(label="Sharpen",
                                command=lambda: self.apply_filter_to_current_image(ImageFilter.SHARPEN))
        filter_menu.add_command(label="Contour",
                                command=lambda: self.apply_filter_to_current_image(ImageFilter.CONTOUR))
        filter_menu.add_command(label="Detail", command=lambda: self.apply_filter_to_current_image(ImageFilter.DETAIL))
        filter_menu.add_command(label="Smooth", command=lambda: self.apply_filter_to_current_image(ImageFilter.SMOOTH))



        enhance_menu = Menu(edit_menu, tearoff=0)
        enhance_menu.add_command(label="Color", command=lambda: self.enhance_current_image("Color", ImageEnhance.Color))
        enhance_menu.add_command(label="Contrast",
                                 command=lambda: self.enhance_current_image("Contrast", ImageEnhance.Contrast))
        enhance_menu.add_command(label="Brightness",
                                 command=lambda: self.enhance_current_image("Brightness", ImageEnhance.Brightness))
        enhance_menu.add_command(label="Sharpness",
                                 command=lambda: self.enhance_current_image("Sharpness", ImageEnhance.Sharpness))

        edit_menu.add_cascade(label="Filter", menu=filter_menu)
        edit_menu.add_cascade(label="Enhance", menu=enhance_menu)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)

        self.root.configure(menu=menu_bar)

    def update_open_recent_menu(self):
        if self.open_recent_menu is None:
            return

        self.open_recent_menu.delete(0, "end")
        for path in self.last_viewed_images:
            self.open_recent_menu.add_command(label=path, command=lambda x=path: self.add_new_image(x))

    def draw_widgets(self):
        self.image_tabs.pack(fill="both", expand=1)

    def load_images_from_config(self):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)

        self.last_viewed_images = config["last_viewed_images"]
        paths = config["opened_images"]
        for path in paths:
            self.add_new_image(path)

    def open_new_images(self):
        image_paths = fd.askopenfilenames(filetypes=(("Images", "*.jpeg;*.jpg;*.png"),))
        for image_path in image_paths:
            self.add_new_image(image_path)

            if image_path not in self.last_viewed_images:
                self.last_viewed_images.append(image_path)
            else:
                self.last_viewed_images.remove(image_path)
                self.last_viewed_images.append(image_path)

            if len(self.last_viewed_images) > 5:
                del self.last_viewed_images[0]

        self.update_open_recent_menu()

    def add_new_image(self, image_path):
        opened_images = [info.path for info in self.opened_images]
        if image_path in opened_images:
            index = opened_images.index(image_path)
            self.image_tabs.select(index)
            return

        image = Image.open(image_path)
        image_tab = Frame(self.image_tabs)

        image_panel = Canvas(image_tab, width=image.width, height=image.height, bd=0, highlightthickness=0)
        self.image_tabs.select(image_tab)

    def current_image(self):
        current_tab = self.image_tabs.select()
        if not current_tab:
            return None
        tab_number = self.image_tabs.index(current_tab)
        return self.opened_images[tab_number]

    def save_current_image(self):
        image = self.current_image()
        if not image:
            return
        if not image.unsaved:
            return

        image.save()
        self.image_tabs.add(image.tab, text=image.filename())

    def save_image_as(self):
        image = self.current_image()
        if not image:
            return

        try:
            image.save_as()
            self.update_image_inside_app(image)
        except ValueError as e:
            mb.showerror("Save as error", str(e))

    def save_all_changes(self):
        for image_info in self.opened_images:
            if not image_info.unsaved:
                continue
            image_info.save()
            self.image_tabs.tab(image_info.tab, text=image_info.filename())

    def close_current_image(self):
        image = self.current_image()
        if not image:
            return

        if image.unsaved:
            if not mb.askyesno("Unsaved changes", "Close without saving changes?"):
                return

        image.close()
        self.image_tabs.forget(image.tab)
        self.opened_images.remove(image)

    def delete_current_image(self):
        image = self.current_image()
        if not image:
            return

        if not mb.askokcancel("Delete image",
                              "Are you sure you want to delete image?\nThis operation is unrecoverable!"):
            return

        image.delete()
        self.image_tabs.forget(image.tab)
        self.opened_images.remove(image)

    def move_current_image(self):
        image = self.current_image()
        if not image:
            return

        image.move()
        self.update_image_inside_app(image)

    def update_image_inside_app(self, image_info):
        image_info.update_image_on_canvas()
        self.image_tabs.tab(image_info.tab, text=image_info.filename())

    def rotate_current_image(self, degrees):
        image = self.current_image()
        if not image:
            return

        image.rotate(degrees)
        image.unsaved = True
        self.update_image_inside_app(image)

    def flip_current_image(self, mode):
        image = self.current_image()
        if not image:
            return

        image.flip(mode)
        image.unsaved = True
        self.update_image_inside_app(image)

    def resize_current_image(self, percents):
        image = self.current_image()
        if not image:
            return

        image.resize(percents)
        image.unsaved = True
        self.update_image_inside_app(image)

    def apply_filter_to_current_image(self, filter_type):
        image = self.current_image()
        if not image:
            return

        image.filter(filter_type)
        image.unsaved = True
        self.update_image_inside_app(image)

    def start_crop_selection_of_current_image(self):
        image = self.current_image()
        if not image:
            return

        image.start_crop_selection()

    def crop_selection_of_current_image(self):
        image = self.current_image()
        if not image:
            return

        try:
            image.crop_selected_area()
            image.unsaved = True
            self.update_image_inside_app(image)
        except ValueError as e:
            mb.showerror("Crop error", str(e))

    def convert_current_image(self, mode):
        image = self.current_image()
        if not image:
            return

        try:
            image.convert(mode)
            image.unsaved = True
            self.update_image_inside_app(image)
        except ValueError as e:
            mb.showerror("Convert error", str(e))

    def enhance_current_image(self, name, enhance):
        current_tab, path, image = self.current_image()
        if not current_tab:
            return


    def save_to_clipboard(self, mode):
        image = self.current_image()
        if not image:
            return

        if mode == "name":
            pyperclip.copy(image.filename(no_star=True))
        elif mode == "dir":
            pyperclip.copy(image.directory(no_star=True))
        elif mode == "path":
            pyperclip.copy(image.full_path(no_star=True))

    def save_images_to_config(self):
        paths = [info.full_path(no_star=True) for info in self.opened_images]
        images = {"opened_images": paths, "last_viewed_images": self.last_viewed_images}
        with open(CONFIG_FILE, 'w') as f:
            json.dump(images, f, indent=4)

    def unsaved_images(self):
        for info in self.opened_images:
            if info.unsaved:
                return True
        return False

    def _close(self, event=None):
        if self.unsaved_images():
            if not mb.askyesno("Unsaved changes", "Got unsaved changes! Exit anyway?"):
                return

        self.save_images_to_config()
        self.root.quit()


if __name__ == "__main__":
    SaadatPhotoEditor().run()
