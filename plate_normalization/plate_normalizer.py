import wxversion
wxversion.select("2.8")
import wx, wx.html, wx.lib.scrolledpanel
import sys
import random
import os.path
from normalization import Normalization, DETECT, TRANSFORMATIONS
import wxplotpanel
import traceback
import numpy as np

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
        """ """
        wx.Panel.__init__(self, parent=parent)

        colors = ["red", "blue", "gray", "yellow", "green"]
        self.SetBackgroundColour(random.choice(colors))

        btn = wx.Button(self, label="Press Me")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(btn, 0, wx.ALL, 10)
        self.SetSizer(sizer)

class ColumnSelector(wx.Panel):
    def __init__(self, parent, callback, substring_hint, normalization, callback_args=[]):
        """ """
        wx.Panel.__init__(self, parent=parent)
        self.callback = callback
        self.substring_hint = substring_hint
        self.normalization = normalization
        self.sheet_idx = 0
        self.callback_args = callback_args

        self.sheet_selector = wx.ComboBox(self, -1, choices=[], style=wx.CB_READONLY)
        self.column_selector = wx.ComboBox(self, -1, choices=[], style=wx.CB_READONLY)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.sheet_selector, 1, wx.EXPAND | wx.RIGHT, 5)
        sizer.Add(self.column_selector, 1, wx.EXPAND)
        self.SetSizer(sizer)

        self.sheet_selector.Bind(wx.EVT_COMBOBOX, self.select_sheet)
        self.column_selector.Bind(wx.EVT_COMBOBOX, self.select_column)

        normalization.file_listeners.append(self.input_file_updated)
        if normalization.input_file:
            self.input_file_updated()

    def input_file_updated(self):
        # find sheet and column names
        self.sheet_selector.Clear()
        self.sheet_selector.AppendItems(self.normalization.book.sheet_names())

    def select_sheet(self, evt):
        sheet_idx = evt.GetSelection()
        self.sheet_idx = sheet_idx
        self.column_selector.Clear()
        column_names = [c.value for c in self.normalization.book.sheet_by_index(sheet_idx).row(0)]
        self.column_selector.AppendItems(column_names)
        default = min([idx for idx, name in enumerate(column_names) if self.substring_hint in name.lower()] or [-1])
        if default > -1:
            self.column_selector.Selection = default
            newevt = wx.PyCommandEvent(wx.wxEVT_COMMAND_COMBOBOX_SELECTED)
            newevt.SetInt(default)
            wx.PostEvent(self.column_selector, newevt)

    def set_default_sheet(self, idx):
        # set a default sheet and trigger a select event
        self.sheet_selector.Selection = idx
        newevt = wx.PyCommandEvent(wx.wxEVT_COMMAND_COMBOBOX_SELECTED)
        newevt.SetInt(idx)
        wx.PostEvent(self.sheet_selector, newevt)

    def select_column(self, evt):
        colidx = evt.GetSelection()
        self.callback((self.sheet_idx, colidx,
                       self.normalization.book.sheet_names()[self.sheet_idx],
                       self.normalization.book.sheet_by_index(self.sheet_idx).row(0)[colidx]),
                      *self.callback_args)


class PlateLayout(wx.Panel):
    def __init__(self, parent, normalization):
        wx.Panel.__init__(self, parent=parent)
        self.normalization = normalization

        input_box = wx.StaticBox(self, wx.ID_ANY, 'Input')
        input_sizer = wx.StaticBoxSizer(input_box, wx.VERTICAL)
        self.input_text = wx.TextCtrl(self, -1, normalization.input_file, style=wx.TE_RIGHT)
        input_browse = wx.Button(self, label="Browse")
        input_sizer.Add(self.input_text, 0, wx.EXPAND)
        input_sizer.Add(input_browse, 0, wx.ALIGN_RIGHT | wx.TOP, 5)

        shape_box = wx.StaticBox(self, wx.ID_ANY, 'Plate shape')
        shape_sizer = wx.StaticBoxSizer(shape_box, wx.HORIZONTAL)
        shapeb1 = wx.RadioButton(self, -1, '96', style=wx.RB_GROUP)
        shapeb2 = wx.RadioButton(self, -1, '384')
        shapeb3 = wx.RadioButton(self, -1, DETECT)
        shape_sizer.Add((1,1), 2)
        shape_sizer.Add(shapeb1, 0)
        shape_sizer.Add((1,1), 1)
        shape_sizer.Add(shapeb2, 0)
        shape_sizer.Add((1,1), 1)
        shape_sizer.Add(shapeb3, 0)
        shape_sizer.Add((1,1), 2)
        shapeb3.Value = 1

        plate_column_box = wx.StaticBox(self, wx.ID_ANY, 'Plate column in spreadsheet')
        plate_column_sizer = wx.StaticBoxSizer(plate_column_box, wx.VERTICAL)
        plate_column_selector = ColumnSelector(self, self.set_plate_column, 'plate', self.normalization)
        plate_column_sizer.Add(plate_column_selector, 0, wx.EXPAND)

        well_column_box = wx.StaticBox(self, wx.ID_ANY, 'Well column(s) in spreadsheet')
        self.well_column_sizer = wx.StaticBoxSizer(well_column_box, wx.VERTICAL)
        wells_combined = self.wells_combined = wx.RadioButton(self, -1, 'Wells in single column', style=wx.RB_GROUP)
        wells_separate = wx.RadioButton(self, -1, 'Rows & columns in separate columns')
        self.well_selector = ColumnSelector(self, self.set_well_column, 'well', self.normalization)
        self.wellrow_selector = ColumnSelector(self, self.set_wellrow_column, 'row', self.normalization)
        self.wellcol_selector = ColumnSelector(self, self.set_wellcol_column, 'col', self.normalization)
        self.well_column_sizer.Add(wells_combined, 0)
        self.well_column_sizer.Add(wells_separate, 0, wx.TOP, 5)
        self.well_column_sizer.Add(self.well_selector, 0, wx.EXPAND | wx.TOP, 5)
        self.well_column_sizer.Add(self.wellrow_selector, 0, wx.EXPAND | wx.TOP, 5)
        self.well_column_sizer.Add(self.wellcol_selector, 0, wx.EXPAND | wx.TOP, 5)

        gene_column_box = wx.StaticBox(self, wx.ID_ANY, 'Gene column in spreadsheet')
        gene_column_sizer = wx.StaticBoxSizer(gene_column_box, wx.VERTICAL)
        self.gene_column_selector = ColumnSelector(self, self.set_gene_column, 'gene', self.normalization)
        gene_column_sizer.Add(self.gene_column_selector, 0, wx.EXPAND)

        status_box = wx.StaticBox(self, wx.ID_ANY, 'Status')
        status_sizer = wx.StaticBoxSizer(status_box, wx.VERTICAL)
        self.status_text = wx.StaticText(self, -1, "Choose settings above...")
        status_sizer.Add(self.status_text, 0, wx.EXPAND)

        wells_combined.Value = True
        self.well_column_sizer.Hide(self.wellrow_selector)
        self.well_column_sizer.Hide(self.wellcol_selector)

        input_browse.Bind(wx.EVT_BUTTON, self.browse_input)
        shapeb1.Bind(wx.EVT_RADIOBUTTON, self.set_shape)
        shapeb2.Bind(wx.EVT_RADIOBUTTON, self.set_shape)
        shapeb3.Bind(wx.EVT_RADIOBUTTON, self.set_shape)

        wells_combined.Bind(wx.EVT_RADIOBUTTON, self.set_wells_combined)
        wells_separate.Bind(wx.EVT_RADIOBUTTON, self.set_wells_combined)

        self.topsizer = sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(input_sizer, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(shape_sizer, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(plate_column_sizer, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(self.well_column_sizer, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(gene_column_sizer, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(status_sizer, 0, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(sizer)

    # XXX - handle text field editing
    def browse_input(self, evt):
        dlg = wx.FileDialog(self, "Choose an input file (.XLS)", wildcard="*.xls", style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.normalization.set_input_file(dlg.GetPath())
            self.update_files()
        dlg.Destroy()

    def update_files(self):
        # should check existence, possibly pre-parse
        self.input_text.Value = self.normalization.input_file
        self.TopLevelParent.update_title()

    def set_shape(self, evt):
        self.normalization.shape = evt.EventObject.Label
        self.preflight()

    def set_plate_column(self, val):
        self.normalization.plate_column = val
        # fill well and gene selectors, as well
        for sel in [self.well_selector, self.wellrow_selector, self.wellcol_selector, self.gene_column_selector]:
            sel.set_default_sheet(val[0])
        self.preflight()

    def set_well_column(self, val):
        self.normalization.well_column = val
        self.preflight()

    def set_wellrow_column(self, val):
        self.normalization.wellrow_column = val
        self.preflight()

    def set_wellcol_column(self, val):
        self.normalization.wellcol_column = val
        self.preflight()

    def set_wells_combined(self, evt):
        if evt.EventObject == self.wells_combined:
            self.normalization.combined_wellrowcol = True
            self.well_column_sizer.Show(self.well_selector)
            self.well_column_sizer.Hide(self.wellrow_selector)
            self.well_column_sizer.Hide(self.wellcol_selector)
        else:
            self.normalization.combined_wellrowcol = False
            self.well_column_sizer.Hide(self.well_selector)
            self.well_column_sizer.Show(self.wellrow_selector)
            self.well_column_sizer.Show(self.wellcol_selector)
        self.preflight()
        self.topsizer.Layout()

    def set_gene_column(self, val):
        self.normalization.gene_column = val
        self.preflight()

    def preflight(self):
        # Attempt to parse the data, report what we find
        self.valid = False
        try:
            # fetch (plate, row, col, gene) for every entry in the XLS
            # given the columns we have.
            current_data = zip(self.normalization.fetch_plates(),
                               self.normalization.fetch_rows(),
                               self.normalization.fetch_cols(),
                               self.normalization.fetch_genes())

            self.detected_384 = False
            num_rows = 0
            gene_counts = {}
            wells_per_plate = {}
            for rowidx, (plate, row, col, gene) in enumerate(current_data):
                # XXX - should we allow empty genes?
                if plate == '':
                    # +2 because rowidx is 0-based, plus one for the head.
                    assert row == col == gene == '', "Incomplete data at row %d (plate = '%s', row = '%s', col = '%s', gene = '%s')"%(rowidx + 2, plate, row, col, gene)
                    continue
                if self.normalization.shape == '96':
                    assert row in 'ABCDEFGH', "Bad row for 96 well plate - '%s' at spreadsheet row %d'"%(row, rowidx + 1)
                    assert 1 <= int(col) <= 12, "Bad col for 96 well plate - '%s' at spreadsheet row %d'"%(col, rowidx + 1)
                else:
                    assert 'A' <= row <= 'P', "Bad row for 384 well plate - '%s' at spreadsheet row %d'"%(row, rowidx + 1)
                    assert 1 <= int(col) <= 24, "Bad col for 384 well plate - '%s' at spreadsheet row %d'"%(col, rowidx + 1)
                    if (row > 'H') or (int(col) > 12):
                        self.detected_384 = True
                num_rows += 1
                wells_per_plate[plate] = wells_per_plate.get(plate, 0) + 1
                gene_counts[gene] = gene_counts.get(gene, 0) + 1


            # XXX - check multiple plates for matching well/gene information
            # XXX - check uniqueness of wells (plate, row, col)

            # count number of plates, wells, and wells per gene
            self.valid = True
            plate_shape = self.normalization.shape
            autodetected = ""
            if plate_shape == DETECT:
                plate_shape = "384" if self.detected_384 else "96"
                autodetected = " (autodetected)"
                self.normalization.detected_384 = self.detected_384

            if min(wells_per_plate.values()) == max(wells_per_plate.values()):
                plate_counts_text = "Wells per plate: %d"%(wells_per_plate.values()[0])
            else:
                plate_counts_text = ["Variable number of wells per plate:"]
                plate_counts_text += sorted(["    %s : %d"%(p, v) for p, v in wells_per_plate.iteritems()])
                plate_counts_text = "\n".join(plate_counts_text)

            # report top 10 genes by count
            countgenes = sorted([(c, g) for g, c in gene_counts.iteritems()])[-10:][::-1]
            gene_counts_text = "\n".join(["Number of wells per gene, top 10:"] + 
                                         ["   %s : %d"%(g, c) for (c, g) in countgenes])

            status = "\n".join(["Plate Type: %s%s" %(plate_shape, autodetected),
                                "Number of plates: %d"%(len(wells_per_plate)),
                                plate_counts_text,
                                gene_counts_text])

            self.normalization.gene_counts = gene_counts
            self.status_text.Label = status
            self.topsizer.Layout()

            self.normalization.parsing_finished()

        except AssertionError, e:
            self.status_text.Label = "Parsing error:\n" + e.message
            self.valid = False
        except Exception, e:
            import traceback
            traceback.print_exc()
            self.status_text.Label = "Choose settings..."
            self.valid = False

class Controls(wx.Panel):
    def __init__(self, parent, normalization):
        wx.Panel.__init__(self, parent=parent)
        self.normalization = normalization
        self.row_controls = []

        box = wx.StaticBox(self, wx.ID_ANY, 'Choose control populations')
        box_sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        self.scroll_window = wx.lib.scrolledpanel.ScrolledPanel(self, -1)
        box_sizer.Add(self.scroll_window, 1, wx.EXPAND)

        self.row_sizer = wx.BoxSizer(wx.VERTICAL)
        self.scroll_window.SetSizer(self.row_sizer)

        self.scroll_window.SetupScrolling(False, True)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(box_sizer, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()

        self.normalization.parsing_listeners.append(self.update)

    def update(self):
        print "updating Controls panel"
        # populate with genes, counts, radiobuttons
        self.row_controls = []
        self.row_sizer.DeleteWindows()

        def make_row(panel, g, c, t, n, p):
            self.row_controls.append([g, c, t, n, p])
            sizer = wx.BoxSizer(wx.HORIZONTAL)
            sizer.Add(g, 1, wx.ALIGN_CENTER)
            sizer.Add(c, 1, wx.ALIGN_CENTER)
            sizer.Add(t, 1, wx.ALIGN_CENTER)
            sizer.Add(n, 1, wx.ALIGN_CENTER)
            sizer.Add(p, 1, wx.ALIGN_CENTER)
            panel.SetSizer(sizer)
            return panel

        # sort by count, then name
        countgenes = sorted([(-c, g) for g, c in self.normalization.gene_counts.iteritems()])
        countgenes = [(-c, g) for c, g in countgenes]

        panel = wx.Panel(self.scroll_window, -1)
        panel.BackgroundColour = "light blue"
        # XXX - this should be outside the scrolled area.
        self.row_sizer.Add(make_row(panel,
                                    wx.StaticText(panel, -1, "Gene Name"),
                                    wx.StaticText(panel, -1, "Count"),
                                    wx.StaticText(panel, -1, "Tested Population"),
                                    wx.StaticText(panel, -1, "Negative Control"),
                                    wx.StaticText(panel, -1, "Positive Control")), 
                           0, wx.EXPAND)

        for idx, (count, gene) in enumerate(countgenes):
            panel = wx.Panel(self.scroll_window, -1)
            # panel.BackgroundColour = "white" if (idx % 5) else "light grey"
            self.row_sizer.Add(make_row(panel,
                                        wx.StaticText(panel, -1, gene),
                                        wx.StaticText(panel, -1, "%d"%(count)),
                                        wx.RadioButton(panel, -1, style=wx.RB_GROUP),
                                        wx.RadioButton(panel, -1),
                                        wx.RadioButton(panel, -1)),
                               0, wx.EXPAND)
            if idx % 5 == 4:
                self.row_sizer.Add(wx.StaticLine(self.scroll_window), 0, wx.EXPAND | wx.ALL, 1)


        for g, c, t, n, p in self.row_controls[1:]:
            t.Value = True

        self.row_sizer.Layout()
        self.scroll_window.VirtualSize = self.scroll_window.BestVirtualSize

class Feature(wx.Panel):
    def __init__(self, parent, normalization):
        wx.Panel.__init__(self, parent=parent)
        self.normalization = normalization
        self.num_replicates = 1
        normalization.num_replicates = self.num_replicates

        feature_column_box = wx.StaticBox(self, wx.ID_ANY, 'Feature columns for each replicate')
        self.feature_column_sizer = wx.StaticBoxSizer(feature_column_box, wx.VERTICAL)
        feature_column_selector = ColumnSelector(self, self.set_feature_column, '---', self.normalization, callback_args=(0,))
        self.feature_column_sizer.Add(feature_column_selector, 0, wx.EXPAND)
        self.feature_column_sizer.Add((1,10), 1)

        add_replicate_button = wx.Button(self, label="Add Replicate")
        remove_replicate_button = wx.Button(self, label="Remove Last Replicate")
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(add_replicate_button, 0)
        button_sizer.Add((10,1), 0)
        button_sizer.Add(remove_replicate_button, 0)
        button_sizer.Add((1,1), 2)

        add_replicate_button.Bind(wx.EVT_BUTTON, self.add_replicate)
        remove_replicate_button.Bind(wx.EVT_BUTTON, self.remove_replicate)

        self.feature_column_sizer.Add(button_sizer, 0, wx.EXPAND)

        self.topsizer = sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.feature_column_sizer, 0, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(sizer)

    def set_feature_column(self, val, replicate_index):
        self.normalization.set_replicate_feature(replicate_index, val)

    def add_replicate(self, evt):
        feature_column_selector = ColumnSelector(self, self.set_feature_column, '---', self.normalization, callback_args=(self.num_replicates,))
        self.feature_column_sizer.Insert(self.num_replicates * 2, feature_column_selector, 0, wx.EXPAND)
        self.feature_column_sizer.Insert(self.num_replicates * 2 + 1, (1, 10), 0)
        self.num_replicates += 1
        self.normalization.num_replicates = self.num_replicates
        self.Layout()

    def remove_replicate(self, evt):
        if self.num_replicates == 1:
            return
        self.num_replicates -= 1
        self.normalization.num_replicates = self.num_replicates
        win = self.feature_column_sizer.Children[self.num_replicates * 2].GetWindow()
        self.feature_column_sizer.Detach(self.num_replicates * 2)
        self.feature_column_sizer.Detach(self.num_replicates * 2)
        win.Destroy()
        self.Layout()

class Parameters(wx.Panel):
    def __init__(self, parent, normalization):
        wx.Panel.__init__(self, parent=parent)
        self.normalization = normalization

        transform_box = wx.StaticBox(self, wx.ID_ANY, 'Data transformation')
        transform_sizer = wx.StaticBoxSizer(transform_box, wx.HORIZONTAL)
        transform_buttons = ([wx.RadioButton(self, -1, TRANSFORMATIONS[0], style=wx.RB_GROUP)]
                            + [wx.RadioButton(self, -1, label, style=wx.RB_GROUP) for label in TRANSFORMATIONS[1:]])
        transform_sizer.Add((1,1), 1)
        for b in transform_buttons:
            transform_sizer.Add(b, 0)
            transform_sizer.Add((1,1), 1)
        transform_buttons[0].Value = 1

        self.topsizer = sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(transform_sizer, 0, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(sizer)

        for b in transform_buttons:
            b.Bind(wx.EVT_RADIOBUTTON, self.update_transform)

    def update_transform(self, evt):
        normalization.set_transformation(evt.EventObject.Label)
        print " update", evt


class Plot(wxplotpanel.PlotPanel):
    ''' shared superclass with common __init__ '''
    def __init__(self, parent, normalization, **kwargs):
        self.normalization = normalization
        self.parent = parent
        # initiate plot window
        wxplotpanel.PlotPanel.__init__(self, parent, **kwargs)

    def draw(self):
        self.figure.clear()
        if not self.normalization.ready():
            subplot = self.figure.add_subplot(111)
            subplot.annotate('waiting\nfor settings...', (0, 0),
                             horizontalalignment='center',
                             multialignment='center')
            subplot.axis([-1, 1, -1, 1])
        else:
            self.do_draw()

class OriginalHistograms(Plot):
    def do_draw(self):
        self.figure.suptitle('original')
        for rep in range(self.normalization.num_replicates):
            subplot = self.figure.add_subplot(self.normalization.num_replicates, 1, rep)
            subplot.hist(self.normalization.get_replicate_data(rep), 20)

class OriginalPlates(Plot):
    def do_draw(self):
        self.figure.suptitle('original')
        plotidx = 0
        for plate_name in self.normalization.plate_names():
            for rep in range(self.normalization.num_replicates):
                plotidx += 1
                subplot = self.figure.add_subplot(self.normalization.num_plates(), self.normalization.num_replicates, plotidx)
                try:
                    subplot.matshow(self.normalization.plate_array(plate_name, rep))
                except:
                    print plate_name, rep
                    traceback.print_exc()
                    pass
                subplot.set_title(plate_name)

class TransformedHistograms(Plot):
    def do_draw(self):
        bad_data = False
        for rep in range(self.normalization.num_replicates):
            subplot = self.figure.add_subplot(self.normalization.num_replicates, 1, rep)
            data = self.normalization.get_replicate_data(rep, transformed=True)
            good_data = data[np.isfinite(data)]
            if np.any(data != good_data):
                bad_data = True
            if len(good_data) > 0:
                subplot.hist(good_data, 20)
        self.figure.suptitle('transformed%s'%(' (invalid values discarded)' if bad_data else ''))

class TransformedPlates(Plot):
    def do_draw(self):
        bad_data = False
        plotidx = 0
        for plate_name in self.normalization.plate_names():
            for rep in range(self.normalization.num_replicates):
                plotidx += 1
                subplot = self.figure.add_subplot(self.normalization.num_plates(), self.normalization.num_replicates, plotidx)
                try:
                    data = self.normalization.plate_array(plate_name, rep, transformed=True)
                    if np.any(~ np.isfinite(data)):
                        bad_data = True
                    subplot.matshow(data)
                except:
                    print plate_name, rep
                    traceback.print_exc()
                    pass
                subplot.set_title(plate_name)
        self.figure.suptitle('transformed%s'%(' (invalid values discarded)' if bad_data else ''))


class CleanedPlot(Plot):
    def do_draw(self):
        self.figure.suptitle('cleaned')
        subplot = self.figure.add_subplot(self.normalization.num_replicates, 1, 0)
        subplot.hist(self.normalization.get_replicate_data(0), 20)


class Plots(wx.Panel):
    def __init__(self, parent, normalization):
        wx.Panel.__init__(self, parent=parent)

        self.normalization = normalization

        self.scroll_window = wx.lib.scrolledpanel.ScrolledPanel(self, -1)
        self.subpanel = subpanel = wx.Panel(self.scroll_window, -1)
        self.panels = {}
        self.panels['original data'] = OriginalHistograms(subpanel, normalization, color=(255,255,255))
        self.panels['original platemaps'] = OriginalPlates(subpanel, normalization, color=(255,255,255))
        self.panels['transformed data'] = TransformedHistograms(subpanel, normalization, color=(255,255,255))
        self.panels['transformed platemaps'] = TransformedPlates(subpanel, normalization, color=(255,255,255))
        self.panels['cleaned data'] = CleanedPlot(subpanel, normalization, color=(255,255,255))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panels['original data'], 1, wx.ALL | wx.EXPAND, 1)
        sizer.Add(self.panels['original platemaps'], 1, wx.ALL | wx.EXPAND, 1)
        sizer.Add(self.panels['transformed data'], 1, wx.ALL | wx.EXPAND, 1)
        sizer.Add(self.panels['transformed platemaps'], 1, wx.ALL | wx.EXPAND, 1)
        sizer.Add(self.panels['cleaned data'], 1, wx.ALL | wx.EXPAND, 1)
        subpanel.SetSizer(sizer)

        self.scroll_window.SetupScrolling(False, True)

        top_sizer = wx.BoxSizer(wx.VERTICAL)
        top_sizer.Add(self.scroll_window, 1, wx.EXPAND)
        self.SetSizer(top_sizer)
        self.Layout()

        self.Bind(wx.EVT_SIZE, self.on_size)

        normalization.feature_selection_listeners.append(self.update_plots)

    def update_plots(self):
        for p in self.panels.values():
            p.draw()

    def on_size(self, evt):
        height = self.scroll_window.ClientSize[1]
        width = int(height / np.sqrt(2))
        self.subpanel.Size = (width, height * len(self.panels))
        self.scroll_window.VirtualSize = self.subpanel.Size
        # center sub panel
        self.subpanel.Position = ((self.scroll_window.Size[0] - self.subpanel.Size[0]) / 2, 0)

class Frame(wx.Frame):
    def __init__(self, title, normalization):
        wx.Frame.__init__(self, None, title=title, size=(600,300))
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

        notebook.AddPage(PlateLayout(notebook, self.normalization), "File && Layout")
        notebook.AddPage(Controls(notebook, self.normalization), "Controls")
        notebook.AddPage(Feature(notebook, self.normalization), "Feature")
        notebook.AddPage(Parameters(notebook, self.normalization), "Parameters")
        notebook.AddPage(Plots(notebook, self.normalization), "Plots")

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


normalization = Normalization()
if len(sys.argv) > 1:
    normalization.set_input_file(sys.argv[1])
app = wx.App(redirect=False)
top = Frame(app_name, normalization)
top.Show()
app.MainLoop()
