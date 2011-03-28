import wxversion
wxversion.select("2.8")
import wx, wx.html
import sys
import random
import os.path

app_name = "Plate Normalizer"
aboutText = """<p>Plate normalizer v0.1.</p>""" 

class HtmlWindow(wx.html.HtmlWindow):
    def __init__(self, parent, id, size=(600,400)):
        wx.html.HtmlWindow.__init__(self,parent, id, size=size)

    def OnLinkClicked(self, link):
        wx.LaunchDefaultBrowser(link.GetHref())
        
class AboutBox(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(self, None, -1, "About...",
                           style=wx.DEFAULT_DIALOG_STYLE|wx.THICK_FRAME)
        hwin = HtmlWindow(self, -1, size=(400,200))
        hwin.SetPage(aboutText)
        self.SetClientSize(hwin.GetSize())
        self.CentreOnParent(wx.BOTH)
        self.SetFocus()


class TabPanel(wx.Panel):
    #----------------------------------------------------------------------
    def __init__(self, parent, *args):
        """"""
        wx.Panel.__init__(self, parent=parent)
 
        colors = ["red", "blue", "gray", "yellow", "green"]
        self.SetBackgroundColour(random.choice(colors))
 
        btn = wx.Button(self, label="Press Me")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(btn, 0, wx.ALL, 10)
        self.SetSizer(sizer)

ColumnSelector = TabPanel
 
class Normalization(object):
    def __init__(self):
        self.input_file = ''
        self.output_file = ''
        

class DataInputOutput(wx.Panel):
    def __init__(self, parent, normalization):
        wx.Panel.__init__(self, parent=parent)
        self.normalization = normalization

        input_box = wx.StaticBox(self, wx.ID_ANY, 'Input')
        output_box = wx.StaticBox(self, wx.ID_ANY, 'Output')
        
        input_sizer = wx.StaticBoxSizer(input_box, wx.VERTICAL)
        self.input_text = wx.TextCtrl(self, -1, normalization.input_file, style=wx.TE_RIGHT)
        input_browse = wx.Button(self, label="Browse")
        input_sizer.Add(self.input_text, 0, wx.EXPAND)
        input_sizer.Add(input_browse, 0, wx.ALIGN_RIGHT | wx.TOP, 5)

        output_sizer = wx.StaticBoxSizer(output_box, wx.VERTICAL)
        self.output_text = wx.TextCtrl(self, -1, normalization.output_file)
        output_browse = wx.Button(self, label="Browse")
        output_sizer.Add(self.output_text, 0, wx.EXPAND)
        output_sizer.Add(output_browse, 0, wx.ALIGN_RIGHT | wx.TOP, 5)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(input_sizer, 0, wx.ALL | wx.EXPAND, 10)
        sizer.Add(output_sizer, 0, wx.ALL | wx.EXPAND, 10)
        self.SetSizer(sizer)

        input_browse.Bind(wx.EVT_BUTTON, self.browse_input)
        output_browse.Bind(wx.EVT_BUTTON, self.browse_output)
        # TODO - handle text editing

        
    def browse_input(self, evt):
        dlg = wx.FileDialog(self, "Choose an input file (.XLS)", wildcard="*.xls", style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.normalization.input_file = dlg.GetPath()
            self.update_files()
        dlg.Destroy()

    def browse_output(self, evt):
        dlg = wx.FileDialog(self, "Choose an output file (.XLS)", wildcard="*.xls", style=wx.SAVE|wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            self.normalization.output_file = dlg.GetPath()
            self.update_files()
        dlg.Destroy()

    def update_files(self):
        # should check existence, possibly pre-parse
        self.input_text.Value = self.normalization.input_file
        self.output_text.Value = self.normalization.output_file
        self.TopLevelParent.update_title()

class PlateLayout(wx.Panel):
    def __init__(self, parent, normalization):
        wx.Panel.__init__(self, parent=parent)
        self.normalization = normalization

        shape_box = wx.StaticBox(self, wx.ID_ANY, 'Plate shape')
        shape_sizer = wx.StaticBoxSizer(shape_box, wx.HORIZONTAL)
        shapeb1 = wx.RadioButton(self, -1, '96', style=wx.RB_GROUP)
        shapeb2 = wx.RadioButton(self, -1, '384')
        shapeb3 = wx.RadioButton(self, -1, 'Detect')
        shape_sizer.Add((1,1), 2)
        shape_sizer.Add(shapeb1, 0)
        shape_sizer.Add((1,1), 1)
        shape_sizer.Add(shapeb2, 0)
        shape_sizer.Add((1,1), 1)
        shape_sizer.Add(shapeb3, 0)
        shape_sizer.Add((1,1), 2)

        plate_column_box = wx.StaticBox(self, wx.ID_ANY, 'Plate column in spreadsheet')
        plate_column_sizer = wx.StaticBoxSizer(plate_column_box, wx.HORIZONTAL)
        plate_column_selector = ColumnSelector(self, self.set_plate_column, 'plate')
        plate_column_sizer.Add(plate_column_selector)

        well_column_box = wx.StaticBox(self, wx.ID_ANY, 'Well column(s) in spreadsheet')
        self.well_column_sizer = wx.StaticBoxSizer(well_column_box, wx.VERTICAL)
        wells_combined = wx.RadioButton(self, -1, 'Wells in single column', style=wx.RB_GROUP)
        wells_separate = wx.RadioButton(self, -1, 'Rows & columns in separate columns')
        self.well_selector = ColumnSelector(self, self.set_well_column, 'well')
        self.wellrow_selector = ColumnSelector(self, self.set_wellrow_column, 'row')
        self.wellcol_selector = ColumnSelector(self, self.set_wellcol_column, 'col')
        self.well_column_sizer.Add(wells_combined, 0)
        self.well_column_sizer.Add(wells_separate, 0, wx.TOP, 5)
        self.well_column_sizer.Add(self.well_selector, 0, wx.EXPAND | wx.TOP, 5)
        self.well_column_sizer.Add(self.wellrow_selector, 0, wx.EXPAND | wx.TOP, 5)
        self.well_column_sizer.Add(self.wellcol_selector, 0, wx.EXPAND | wx.TOP, 5)

        wells_combined.Value = True
        self.well_column_sizer.Hide(self.wellrow_selector)
        self.well_column_sizer.Hide(self.wellcol_selector)
        
        shapeb1.Bind(wx.EVT_RADIOBUTTON, self.set_shape)
        shapeb2.Bind(wx.EVT_RADIOBUTTON, self.set_shape)
        shapeb3.Bind(wx.EVT_RADIOBUTTON, self.set_shape)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(shape_sizer, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(plate_column_sizer, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(self.well_column_sizer, 0, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(sizer)
    
    def set_plate_column(self, val):
        pass

    def set_well_column(self, val):
        pass
    
    def set_wellrow_column(self, val):
        pass

    def set_wellcol_column(self, val):
        pass

    def set_shape(self, evt):
        self.normalization.shape = evt.EventObject.Label


class Frame(wx.Frame):
    def __init__(self, title, normalization):
        wx.Frame.__init__(self, None, title=title, size=(450,300))
        self.normalization = normalization
        self.appname = title

        menuBar = wx.MenuBar()
        menu = wx.Menu()
        m_exit = menu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Close window and exit program.")
        self.Bind(wx.EVT_MENU, self.on_close, m_exit)
        menuBar.Append(menu, "&File")
        menu = wx.Menu()
        m_about = menu.Append(wx.ID_ABOUT, "&About", "Information about this program")
        self.Bind(wx.EVT_MENU, self.on_about, m_about)
        menuBar.Append(menu, "&Help")
        self.SetMenuBar(menuBar)

        self.statusbar = self.CreateStatusBar()

        panel = wx.Panel(self)
        
        notebook = wx.Notebook(panel)

        notebook.AddPage(DataInputOutput(notebook, self.normalization), "Data Input/Output")
        notebook.AddPage(PlateLayout(notebook, self.normalization), "Plate Layout")

        tabTwo = TabPanel(notebook)
        notebook.AddPage(tabTwo, "Controls")

        tabTwo = TabPanel(notebook)
        notebook.AddPage(tabTwo, "Normalization")

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(notebook, 1, wx.ALL|wx.EXPAND, 5)
        panel.SetSizer(sizer)

        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.on_close)



    def on_close(self, event):
        dlg = wx.MessageDialog(self, 
            "Do you really want to close this application?",
            "Confirm Exit", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            self.Destroy()

    def on_about(self, event):
        dlg = AboutBox()
        dlg.ShowModal()
        dlg.Destroy()  

    def update_title(self):
        title = self.appname
        if self.normalization.input_file != '':
            title += ' - %s'%(os.path.basename(self.normalization.input_file))
            if self.normalization.output_file != '':
                title += ' -> %s'%(os.path.basename(self.normalization.output_file))
        self.Title = title

app = wx.App(redirect=False) 
top = Frame(app_name, Normalization())
top.Show()
app.MainLoop()
