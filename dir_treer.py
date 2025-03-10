#!/usr/bin/env python3
"""
Canvas-based directory tree viewer with:
 - Click folder name/arrow to expand/collapse.
 - Click bracket check [•] to toggle items (recursively for folders).
 - If a child is checked, its parent folder is also auto-checked (recursively upwards).
 - "Include hidden files" toggles Unix dotfiles/Windows hidden attribute.
 - "Re-run" rescans the filesystem.
 - "Copy" copies only checked items. If none are checked, shows "Nothing to copy".
 - "Copied!" message disappears after 5 seconds.
 - Mouse wheel scrolling on Windows/macOS/Linux, bound directly to the Canvas.
 - Folders first (alphabetically), then files (alphabetically).
 - The window title & icon name are "Tree: <folder>", so it appears in the dock/taskbar as that.

Logging controlled by DEBUG_MODE.
"""

import os
import sys
import platform
import logging
import ctypes
from pathlib import Path
import tkinter as tk

DEBUG_MODE = False

if DEBUG_MODE:
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
else:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")


# Adjust this to reduce or increase line spacing
ROW_HEIGHT = 18


def is_hidden(path: Path) -> bool:
    """Return True if 'path' is hidden on Unix (.dotfile) or Windows (hidden attribute)."""
    if platform.system() != "Windows":
        return path.name.startswith(".")
    else:
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
        if attrs == -1:
            return False
        # FILE_ATTRIBUTE_HIDDEN = 2
        return bool(attrs & 2)


class TreeItem:
    """
    Represents one file or folder in the directory tree, with a 'checked' state
    and an 'expanded' state if it's a folder (collapsible).
    """
    def __init__(self, path: Path, parent=None):
        self.path = path
        self.parent = parent
        self.is_dir = path.is_dir()
        self.children = []
        self.checked = True  # default is checked
        # For collapsible folders (False => collapsed, True => expanded, None => not a folder)
        self.expanded = False if self.is_dir else None

    @property
    def name(self) -> str:
        """Return display name, with slash/backslash if directory."""
        if self.is_dir:
            return self.path.name + ("\\" if os.name == "nt" else "/")
        else:
            return self.path.name

    def add_child(self, item: "TreeItem"):
        self.children.append(item)


def build_tree_structure(directory: Path, exclude_hidden: bool) -> TreeItem:
    """
    Recursively build a TreeItem hierarchy from 'directory', placing folders first
    then files, both sorted alphabetically.
    """
    root = TreeItem(directory)
    if directory.is_dir():
        try:
            entries = list(directory.iterdir())
            # separate dirs/files
            dirs = [e for e in entries if e.is_dir()]
            files = [e for e in entries if e.is_file()]

            # sort each group by name
            dirs.sort(key=lambda p: p.name.lower())
            files.sort(key=lambda p: p.name.lower())

            # combine so directories come first
            sorted_entries = dirs + files

        except PermissionError as e:
            logging.warning(f"Permission denied: {directory} ({e})")
            return root

        if exclude_hidden:
            sorted_entries = [e for e in sorted_entries if not is_hidden(e)]

        for entry in sorted_entries:
            child = build_tree_structure(entry, exclude_hidden)
            child.parent = root
            root.add_child(child)

    return root


class DirectoryTreeGUI(tk.Tk):
    def __init__(self, directory: Path):
        super().__init__()

        # Window title & icon name so that it shows up in the dock/Taskbar
        self.title(f"Tree: {directory.name}")
        self.iconname(f"Tree: {directory.name}")  # attempt to change the dock/taskbar name
        self.geometry("900x600")

        self.directory = directory
        self.exclude_hidden = True  # Toggled by "Include hidden files"

        self.root_item = None

        # -- Top Frame: Checkbutton, Re-run, Copy, "Copied!"
        top_frame = tk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.show_hidden_var = tk.BooleanVar(value=False)
        cb_hidden = tk.Checkbutton(
            top_frame,
            text="Include hidden files",
            variable=self.show_hidden_var,
            command=self.on_toggle_hidden
        )
        cb_hidden.pack(side=tk.LEFT, padx=5)

        self.refresh_button = tk.Button(top_frame, text="⟳ Re-run", command=self.refresh_tree)
        self.refresh_button.pack(side=tk.LEFT, padx=5)

        self.copy_button = tk.Button(top_frame, text="📋 Copy", command=self.copy_to_clipboard)
        self.copy_button.pack(side=tk.LEFT, padx=5)

        self.copied_label = tk.Label(top_frame, text="", fg="green")
        self.copied_label.pack(side=tk.RIGHT, padx=5)

        # -- Canvas for the directory tree
        self.canvas = tk.Canvas(self, bg="black", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Ensure the canvas can get focus for mouse-wheel events:
        self.canvas.focus_set()

        # Scrollbars
        self.scrollbar_y = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.scrollbar_x = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas.configure(
            yscrollcommand=self.scrollbar_y.set,
            xscrollcommand=self.scrollbar_x.set
        )

        # Font setup
        self.font_family = ("Courier New", 12)  # or any monospaced font
        self.line_height = ROW_HEIGHT
        self.current_y = 0
        self.max_x = 0

        # Dictionaries for click handling
        self.item_id_to_tree_item_check = {}
        self.item_id_to_tree_item_expand = {}

        # Bind mouse click directly to the canvas
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # Bind mouse wheel to the canvas (rather than bind_all)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel_windows_mac)
        self.canvas.bind("<Button-4>", self.on_mousewheel_linux_up)
        self.canvas.bind("<Button-5>", self.on_mousewheel_linux_down)

        self.refresh_tree()

    def on_toggle_hidden(self):
        """User toggled 'Include hidden files' => invert exclude_hidden and re-run."""
        self.exclude_hidden = not self.show_hidden_var.get()
        self.refresh_tree()

    def refresh_tree(self):
        """Re-scan the directory structure, set root expanded, then re-draw."""
        self.copied_label.config(text="")
        self.canvas.delete("all")
        self.item_id_to_tree_item_check.clear()
        self.item_id_to_tree_item_expand.clear()
        self.current_y = 0
        self.max_x = 0

        logging.debug(f"Building tree for {self.directory}, exclude_hidden={self.exclude_hidden}")
        self.root_item = build_tree_structure(self.directory, self.exclude_hidden)

        # Only top-level folder expanded by default
        if self.root_item.is_dir:
            self.root_item.expanded = True

        self.draw_tree_item(self.root_item, prefix="", is_last=True)
        self.update_scrollregion()

    def update_scrollregion(self):
        """Update canvas scroll region."""
        self.canvas.config(scrollregion=(0, 0, self.max_x, self.current_y))

    def draw_tree_item(self, item: TreeItem, prefix: str, is_last: bool):
        """
        Draw a single 'line' for this item: bracket region + arrow + prefix+connector + item name.
        Then, if the item is a directory and expanded, draw children below it.
        """
        connector = "└──" if is_last else "├──"

        x = 10
        y = self.current_y

        # 1) Bracket region [•]/[ ]:
        bracket_tag = f"check_{id(item)}"

        bracket_open_id = self.canvas.create_text(
            x, y, text="[", anchor="nw", fill="white", font=self.font_family
        )
        self.canvas.itemconfig(bracket_open_id, tags=(bracket_tag,))
        bb = self.canvas.bbox(bracket_open_id)
        x_next = bb[2] + 1

        dot_color = "lightblue" if item.checked else self.canvas.cget("bg")
        dot_id = self.canvas.create_text(
            x_next, y, text="•", anchor="nw", fill=dot_color, font=self.font_family
        )
        self.canvas.itemconfig(dot_id, tags=(bracket_tag,))
        bb_dot = self.canvas.bbox(dot_id)
        x_next = bb_dot[2] + 1

        bracket_close_id = self.canvas.create_text(
            x_next, y, text="]", anchor="nw", fill="white", font=self.font_family
        )
        self.canvas.itemconfig(bracket_close_id, tags=(bracket_tag,))
        bb_close = self.canvas.bbox(bracket_close_id)
        x_next = bb_close[2] + 1

        self.item_id_to_tree_item_check[bracket_tag] = item

        # 2) space
        space_id = self.canvas.create_text(
            x_next, y, text=" ", anchor="nw", fill="white", font=self.font_family
        )
        bb_space = self.canvas.bbox(space_id)
        x_next = bb_space[2]

        # 3) If directory => arrow (► for collapsed, ▼ for expanded). If file => no arrow
        arrow_str = ""
        if item.is_dir:
            arrow_str = "▼" if item.expanded else "►"

        if arrow_str:
            arrow_tag = f"expand_{id(item)}"
            arrow_id = self.canvas.create_text(
                x_next, y, text=arrow_str, anchor="nw", fill="white", font=self.font_family
            )
            self.canvas.itemconfig(arrow_id, tags=(arrow_tag,))
            bb_arrow = self.canvas.bbox(arrow_id)
            x_next = bb_arrow[2] + 1

            arrow_space = self.canvas.create_text(
                x_next, y, text=" ", anchor="nw", fill="white", font=self.font_family
            )
            bb_arrow_space = self.canvas.bbox(arrow_space)
            x_next = bb_arrow_space[2]

            self.item_id_to_tree_item_expand[arrow_tag] = item

        # 4) prefix + connector
        connector_str = prefix + connector
        conn_id = self.canvas.create_text(
            x_next, y, text=connector_str, anchor="nw", fill="white", font=self.font_family
        )
        bb_conn = self.canvas.bbox(conn_id)
        x_next = bb_conn[2] + 1

        space2_id = self.canvas.create_text(
            x_next, y, text=" ", anchor="nw", fill="white", font=self.font_family
        )
        bb_space2 = self.canvas.bbox(space2_id)
        x_next = bb_space2[2]

        # 5) item name => yellow if dir, white if file
        name_color = "yellow" if item.is_dir else "white"
        name_tag = ""
        if item.is_dir:
            name_tag = f"expand_{id(item)}"  # clicking name toggles expand
        name_id = self.canvas.create_text(
            x_next, y, text=item.name, anchor="nw", fill=name_color, font=self.font_family
        )
        if name_tag:
            self.canvas.itemconfig(name_id, tags=(name_tag,))
            self.item_id_to_tree_item_expand[name_tag] = item

        bb_name = self.canvas.bbox(name_id)
        x_next = bb_name[2]

        # track max_x
        if x_next > self.max_x:
            self.max_x = x_next

        self.current_y += self.line_height

        # 6) children if folder is expanded
        if item.is_dir and item.expanded:
            child_count = len(item.children)
            for i, child in enumerate(item.children):
                child_is_last = (i == child_count - 1)
                deeper_prefix = prefix + ("    " if is_last else "│   ")
                self.draw_tree_item(child, deeper_prefix, child_is_last)

    def on_canvas_click(self, event):
        """
        If user clicks bracket => toggle check. If user clicks folder => expand/collapse.
        Checking a child also checks the parent chain.
        """
        closest = self.canvas.find_closest(event.x, event.y)
        if not closest:
            return
        tags = self.canvas.gettags(closest)

        # 1) check toggles
        for t in tags:
            if t.startswith("check_") and t in self.item_id_to_tree_item_check:
                item = self.item_id_to_tree_item_check[t]
                new_state = not item.checked
                item.checked = new_state
                if item.is_dir:
                    self.recursive_check_down(item, new_state)
                else:
                    # if a file or subfolder was just checked, check ancestors
                    if new_state:
                        self.recursive_check_up(item)
                self.redraw_canvas()
                return

        # 2) expand/collapse toggles
        for t in tags:
            if t.startswith("expand_") and t in self.item_id_to_tree_item_expand:
                item = self.item_id_to_tree_item_expand[t]
                if item.is_dir:
                    item.expanded = not item.expanded
                    self.redraw_canvas()
                return

    def recursive_check_down(self, folder_item: TreeItem, new_state: bool):
        """Recursively set the 'checked' state for all children of a folder."""
        for child in folder_item.children:
            child.checked = new_state
            if child.is_dir:
                self.recursive_check_down(child, new_state)

    def recursive_check_up(self, item: TreeItem):
        """If a child is checked, ensure its parent(s) are also checked."""
        parent = item.parent
        if parent and parent.is_dir and not parent.checked:
            parent.checked = True
            self.recursive_check_up(parent)

    def redraw_canvas(self):
        """Re-draw from self.root_item (no re-scan)."""
        self.canvas.delete("all")
        self.item_id_to_tree_item_check.clear()
        self.item_id_to_tree_item_expand.clear()
        self.current_y = 0
        self.max_x = 0
        self.draw_tree_item(self.root_item, prefix="", is_last=True)
        self.update_scrollregion()

    # ------------ Mouse Wheel --------------
    def on_mousewheel_windows_mac(self, event):
        """
        On Windows/macOS, <MouseWheel> is triggered with event.delta = ±120 multiples.
        Negative delta => scroll down, Positive => scroll up.
        """
        # For mac, event.delta can be very large. Typically we do integer division by 120.
        if platform.system() == "Darwin":
            # On mac, each scroll is typically ±1 in event.delta
            self.canvas.yview_scroll(-1 * event.delta, "units")
        else:
            # On Windows, event.delta is typically ±120
            delta = int(-1 * (event.delta // 120))
            self.canvas.yview_scroll(delta, "units")

    def on_mousewheel_linux_up(self, event):
        """Some Linux systems send <Button-4> for wheel up."""
        self.canvas.yview_scroll(-1, "units")

    def on_mousewheel_linux_down(self, event):
        """Some Linux systems send <Button-5> for wheel down."""
        self.canvas.yview_scroll(1, "units")

    # ------------ Copy to Clipboard --------------
    def copy_to_clipboard(self):
        """
        Copy only the checked items in a tree-like text form to the system clipboard.
        If none are checked, show "Nothing to copy". Otherwise "Copied!" for 5s.
        """
        lines = []
        self.build_text_for_checked(self.root_item, lines, prefix="", is_last=True)
        final_text = "\n".join(lines).strip()

        if not final_text:
            self.copied_label.config(text="Nothing to copy")
            self.after(5000, self._hide_copied_label)
            return

        self.clipboard_clear()
        self.clipboard_append(final_text)
        self.copied_label.config(text="Copied!")
        self.after(5000, self._hide_copied_label)

    def _hide_copied_label(self):
        self.copied_label.config(text="")

    def build_text_for_checked(self, item: TreeItem, lines, prefix, is_last):
        """Recursive function to build lines for only checked items."""
        if not item.checked:
            return

        connector = "└──" if is_last else "├──"
        if item.parent is not None:
            lines.append(prefix + connector + " " + item.name)
        else:
            # top-level
            path_line = str(item.path.resolve())
            if item.is_dir:
                path_line += "\\" if os.name == "nt" else "/"
            lines.append(path_line)

        checked_children = [c for c in item.children if c.checked]
        cnt = len(checked_children)
        for i, child in enumerate(checked_children):
            child_is_last = (i == cnt - 1)
            deeper_prefix = prefix + ("    " if is_last else "│   ")
            self.build_text_for_checked(child, lines, deeper_prefix, child_is_last)


def main():
    if len(sys.argv) > 1:
        directory_path = Path(sys.argv[1]).resolve()
    else:
        directory_path = Path.cwd()

    if not directory_path.exists():
        print(f"Error: The path {directory_path} does not exist.")
        sys.exit(1)

    app = DirectoryTreeGUI(directory_path)
    app.mainloop()


if __name__ == "__main__":
    main()