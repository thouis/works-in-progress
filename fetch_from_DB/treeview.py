import wx
import wx.html
import wx.lib.agw.customtreectrl as CT
import os

class DirTree(CT.CustomTreeCtrl):
    def __init__(self, parent, initial_dir, display_file_test=None):
        self.current_directory = initial_dir
        CT.CustomTreeCtrl.__init__(self, parent, -1, style=wx.TR_DEFAULT_STYLE)
        self.display_file_test = display_file_test or (lambda x: True)

        # folder images
        isz = (16, 16)
        il = wx.ImageList(*isz)
        self.fldridx     = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER,      wx.ART_OTHER, isz))
        self.fldropenidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN,   wx.ART_OTHER, isz))
        self.fileidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz))
        self.SetImageList(il)

        self.set_directory(self.current_directory)
        self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.expand)

    def set_directory(self, dir):
        if not os.path.isdir(dir):
            return
        self.DeleteAllItems()
        root = self.AddRoot(dir, ct_type=1)
        self.SetPyData(root, (dir, False))
        self.SetItemImage(root, self.fldridx, wx.TreeItemIcon_Normal)
        self.SetItemImage(root, self.fldropenidx, wx.TreeItemIcon_Expanded)
        self.AppendItem(root, '...')
        self.Refresh()

    def expand(self, evt):
        self.Freeze()
        item = evt.GetItem()
        (dirname, already_visited) = self.GetPyData(item)
        if not already_visited:
            # put some feedback about directory size here?
            _, subdirs, subfiles = os.walk(dirname).next()
            subdirs.sort()
            subfiles.sort()
            if len(subfiles + subdirs):
                self.DeleteChildren(item)
            if len(subdirs) > 0:
                for sd in subdirs:
                    child = self.AppendItem(item, sd, ct_type=1)
                    self.SetPyData(child, (os.path.join(dirname, sd), False))
                    self.SetItemImage(child, self.fldridx, wx.TreeItemIcon_Normal)
                    self.SetItemImage(child, self.fldropenidx, wx.TreeItemIcon_Expanded)
                    self.AppendItem(child, '...')
            if len(subfiles) > 0:
                for sf in subfiles:
                    child = self.AppendItem(item, sf, ct_type=0)
                    # self.SetItemImage(child, self.fileidx, wx.TreeItemIcon_Normal)
        self.SetPyData(item, (dirname, True))
        self.Thaw()

    def get_selected_dirs(self):
        def find_all_checked_branches(node):
            if node.IsChecked():
                yield self.GetPyData(node)[0]
            for child in node.GetChildren():
                for checked_child in find_all_checked_branches(child):
                    yield checked_child

        return [d for d in find_all_checked_branches(self.GetRootItem())]


if __name__ == '__main__':
    class MyApp(wx.App):
        def OnInit(self):
            frame = wx.Frame(None, title="Select files to load...", style=wx.DEFAULT_FRAME_STYLE)
            d = DirTree(frame, ".")
            frame.Show(True)
            self.SetTopWindow(frame)
            return True

    app = MyApp(0)
    app.MainLoop()
