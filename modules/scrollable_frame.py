# Hype ERP - Reusable Scrollable Frame with full Mouse + Keyboard support
# Developer: David | Nexuzy Lab
# Usage: sf = ScrollableFrame(parent); use sf.scrollable_frame as container
import tkinter as tk


class ScrollableFrame(tk.Frame):
    """
    Drop-in scrollable container.
    - Mouse wheel scroll (Windows + Linux)
    - Arrow keys / Page Up / Page Down / Home / End
    - Works inside any Toplevel or Frame
    """
    def __init__(self, parent, bg='#1a1a2e', **kwargs):
        super().__init__(parent, bg=bg, **kwargs)

        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.vbar = tk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.hbar = tk.Scrollbar(self, orient='horizontal', command=self.canvas.xview)

        self.canvas.configure(yscrollcommand=self.vbar.set,
                              xscrollcommand=self.hbar.set)

        self.hbar.pack(side='bottom', fill='x')
        self.vbar.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)

        self.scrollable_frame = tk.Frame(self.canvas, bg=bg)
        self._win_id = self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor='nw'
        )

        self.scrollable_frame.bind('<Configure>', self._on_frame_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)

        # Bind mouse wheel
        self.canvas.bind('<Enter>', self._bind_mousewheel)
        self.canvas.bind('<Leave>', self._unbind_mousewheel)

        # Keyboard scroll (focus canvas to activate)
        self.canvas.bind('<Up>',       lambda e: self.canvas.yview_scroll(-1, 'units'))
        self.canvas.bind('<Down>',     lambda e: self.canvas.yview_scroll(1, 'units'))
        self.canvas.bind('<Left>',     lambda e: self.canvas.xview_scroll(-1, 'units'))
        self.canvas.bind('<Right>',    lambda e: self.canvas.xview_scroll(1, 'units'))
        self.canvas.bind('<Prior>',    lambda e: self.canvas.yview_scroll(-5, 'units'))  # Page Up
        self.canvas.bind('<Next>',     lambda e: self.canvas.yview_scroll(5, 'units'))   # Page Down
        self.canvas.bind('<Home>',     lambda e: self.canvas.yview_moveto(0))
        self.canvas.bind('<End>',      lambda e: self.canvas.yview_moveto(1))
        self.canvas.bind('<Button-1>', lambda e: self.canvas.focus_set())

    def _on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self._win_id, width=event.width)

    def _bind_mousewheel(self, event):
        self.canvas.bind_all('<MouseWheel>',        self._on_mousewheel_win)
        self.canvas.bind_all('<Button-4>',          self._on_mousewheel_up)
        self.canvas.bind_all('<Button-5>',          self._on_mousewheel_down)

    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all('<MouseWheel>')
        self.canvas.unbind_all('<Button-4>')
        self.canvas.unbind_all('<Button-5>')

    def _on_mousewheel_win(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

    def _on_mousewheel_up(self, event):
        self.canvas.yview_scroll(-3, 'units')

    def _on_mousewheel_down(self, event):
        self.canvas.yview_scroll(3, 'units')

    def scroll_to_top(self):
        self.canvas.yview_moveto(0)

    def scroll_to_bottom(self):
        self.canvas.yview_moveto(1)


def add_treeview_scroll(parent, tree):
    """
    Utility: attach both vertical + horizontal scrollbars to any Treeview
    and bind mousewheel on it.
    """
    vsb = tk.Scrollbar(parent, orient='vertical', command=tree.yview)
    hsb = tk.Scrollbar(parent, orient='horizontal', command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.bind('<MouseWheel>',
              lambda e: tree.yview_scroll(int(-1*(e.delta/120)), 'units'))
    tree.bind('<Button-4>',  lambda e: tree.yview_scroll(-3, 'units'))
    tree.bind('<Button-5>',  lambda e: tree.yview_scroll(3, 'units'))

    # Keyboard navigation on treeview
    tree.bind('<Up>',    lambda e: _tree_nav(tree, -1))
    tree.bind('<Down>',  lambda e: _tree_nav(tree, 1))
    tree.bind('<Home>',  lambda e: _tree_select_first(tree))
    tree.bind('<End>',   lambda e: _tree_select_last(tree))

    return vsb, hsb


def _tree_nav(tree, direction):
    sel = tree.selection()
    children = tree.get_children()
    if not children: return
    if not sel:
        tree.selection_set(children[0])
        tree.see(children[0])
        return
    idx = list(children).index(sel[0]) + direction
    idx = max(0, min(idx, len(children)-1))
    tree.selection_set(children[idx])
    tree.see(children[idx])


def _tree_select_first(tree):
    ch = tree.get_children()
    if ch: tree.selection_set(ch[0]); tree.see(ch[0])


def _tree_select_last(tree):
    ch = tree.get_children()
    if ch: tree.selection_set(ch[-1]); tree.see(ch[-1])
