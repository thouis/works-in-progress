import os
import sys
import xlwt
import wx
import traceback
import xml.parsers.expat
import treeview

from lookup_from_db import lookup_treatment

class DirPanel(wx.Panel):
    def __init__(self, parent, ID, labelstr, flags):
        wx.Panel.__init__(self, parent, ID)
        self.labelstr = labelstr
        label = wx.StaticText(self, -1, labelstr)
        dirname = self.dirname = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        choosedir = wx.Button(self, -1, 'Choose...')

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(label, 0, wx.EXPAND)
        box.Add((5,5))
        box.Add(dirname, 1, wx.EXPAND)
        box.Add((5,5))
        box.Add(choosedir, 0, wx.EXPAND)

        choosedir.Bind(wx.EVT_BUTTON, self.on_choosedir)
        dirname.Bind(wx.EVT_TEXT_ENTER, self.on_enter)

        self.SetAutoLayout(True)
        self.SetSizer(box)
        self.Layout()

    def on_choosedir(self, evt):
        dir_dlg = wx.DirDialog(self, self.labelstr, style=wx.DD_DIR_MUST_EXIST)
        if dir_dlg.ShowModal():
            self.dirname.Value = dir_dlg.GetPath()
        dir_dlg.Destroy()
        self.Parent.update_subdirs()

    def on_enter(self, evt):
        if os.path.isdir(self.dirname.Value):
            self.Parent.update_subdirs()

class FilePanel(wx.Panel):
    def __init__(self, parent, ID, labelstr, flags):
        wx.Panel.__init__(self, parent, ID)

        self.flags = flags
        self.labelstr = labelstr

        label = wx.StaticText(self, -1, labelstr)
        filename = self.filename = wx.TextCtrl(self)
        browse = wx.Button(self, -1, 'Choose...')

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(label, 0, wx.EXPAND)
        box.Add(filename, 1, wx.EXPAND)
        box.Add(browse, 0, wx.EXPAND)

        browse.Bind(wx.EVT_BUTTON, self.on_browse)

        self.SetAutoLayout(True)
        self.SetSizer(box)
        self.Layout()

    def on_browse(self, evt):
        defaultfile = ''
        if self.Parent.substring.Value != '':
            defaultfile = self.Parent.substring.Value + '.XLS'
        file_dlg = wx.FileDialog(self, self.labelstr, defaultDir=self.Parent.parent_dir.dirname.Value, defaultFile=defaultfile, style=self.flags)
        if file_dlg.ShowModal():
            self.filename.Value = file_dlg.GetPath()
        file_dlg.Destroy()

class NonModalWarning(wx.Frame):
    def __init__(self, warning_text):
        wx.Frame.__init__(self, None, -1, 'Warning')

        self.text = wx.StaticText(self, -1, warning_text)
        self.okbutton = wx.Button(self, -1, 'Ok')

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.text, 0, wx.EXPAND)
        box.Add(self.okbutton, 0)

        self.okbutton.Bind(wx.EVT_BUTTON, lambda x: self.Destroy())

        self.SetAutoLayout(True)
        self.SetSizer(box)
        self.Center()
        self.Layout()
        self.Size = self.BestSize

class MyFrame(wx.Frame):
   def __init__(self, parent, ID, title):
       wx.Frame.__init__(self, parent, ID, title)
       self.parent_dir = parent_dir = DirPanel(self, -1, 'Parent directory of replicates ', wx.FD_OPEN)
       self.subdirs = subdirs = treeview.DirTree(self, '.')
       substring_label = wx.StaticText(self, -1, 'Common string in .XML file names: ')
       self.substring = substring = wx.TextCtrl(self, -1)
       extract_label = wx.StaticText(self, -1, 'Extract genes/chemicals from DB?')
       self.extract_from_DB = wx.Choice(self, -1, choices=['No', 'Genes', 'Chemicals'])
       self.go_button = go_button = wx.Button(self, -1, 'Choose output file...')

       substring_box = wx.BoxSizer(wx.HORIZONTAL)
       substring_box.Add(substring_label, 0, wx.CENTER)
       substring_box.Add(substring, 1, wx.EXPAND)

       extract_box = wx.BoxSizer(wx.HORIZONTAL)
       extract_box.Add(extract_label, 0, wx.CENTER)
       extract_box.Add(self.extract_from_DB, 1, wx.EXPAND)

       box = wx.BoxSizer(wx.VERTICAL)
       box.Add(parent_dir, 0, wx.EXPAND | wx.BOTTOM, 5)
       box.Add(subdirs, 1, wx.EXPAND | wx.BOTTOM, 5)
       box.Add(substring_box, 0, wx.EXPAND | wx.BOTTOM, 5)
       box.Add(extract_box, 0, wx.CENTER | wx.BOTTOM, 5)
       box.Add(go_button, 0, wx.CENTER | wx.BOTTOM, 5)

       bigbox = wx.BoxSizer(wx.VERTICAL)
       bigbox.Add(box, 1, wx.EXPAND | wx.ALL, 5)

       self.extract_from_DB.Value = False
       go_button.Bind(wx.EVT_BUTTON, self.process_xml)

       self.SetSizer(bigbox)
       self.Center()
       self.Layout()

   def update_subdirs(self):
       dirname = self.parent_dir.dirname.Value
       self.subdirs.set_directory(dirname)

   def process_xml(self, evt):
       try:
           outfile = None
           dlg = wx.FileDialog(self, 'Choose output .XLS file', defaultDir=self.parent_dir.dirname.Value, defaultFile=(self.substring.Value + '.XLS'), style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
           if dlg.ShowModal():
               outfile = dlg.GetPath()
           dlg.Destroy()
           if not outfile:
               return

           # if not os.access(outfile, os.W_OK):
           # Should probably allow the user to abort here...

           # find all the xml files
           xmlfiles = []
           warn_no_files = []
           warn_too_many_files = []
           count = 0
           progress = wx.ProgressDialog('Finding XML files...', 'Working           ', 100, self, wx.PD_CAN_ABORT | wx.PD_APP_MODAL | wx.PD_ESTIMATED_TIME | wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME)
           selected_dirs = self.subdirs.get_selected_dirs()
           num_subdirs = len(selected_dirs)
           for subdir in selected_dirs:
               rel_subdir = os.path.relpath(subdir, self.parent_dir.dirname.Value)
               _, platedirs, _ = os.walk(subdir).next()
               num_plates = len(platedirs)
               for pld in platedirs:
                   count = count + 1
                   warning = ''
                   if len(warn_no_files) > 0 or len(warn_too_many_files) > 0:
                       warning = '\nMissing or Extra XML files found! (cancel to review)'
                   kont, skip = progress.Update(int((99.0 * min(count, num_subdirs * num_plates)) / (num_subdirs * num_plates)), 'Looking in %s'%(os.path.join(rel_subdir, pld))+warning)
                   if not kont:
                       self.warn_bad_xml(warn_no_files, warn_too_many_files)
                       progress.Destroy()
                       return
                   progress.Fit()
                   xmls = [f for f in os.listdir(os.path.join(subdir, pld)) if self.substring.Value.lower() in f.lower() and f.lower().endswith('.xml')]
                   if len(xmls) == 0:
                       warn_no_files += [os.path.join(subdir, pld)]
                       continue
                   if len(xmls) > 1:
                       # take the youngest
                       xmls = [sorted([(os.stat(os.path.join(subdir, pld, x))[-2], x) for x in xmls])[-1][1]]
                       warn_too_many_files += [(subdir, pld, xmls)]
                   xmlfiles += [(rel_subdir, pld, xmls[0])]
           progress.Destroy()
           progress = None
           self.warn_bad_xml(warn_no_files, warn_too_many_files)

           class StopProcessing(Exception):
               pass

           # Process the XML files into a single Excel file
           progress = wx.ProgressDialog('Processing XML files...', 'Working           ', len(xmlfiles), self, wx.PD_CAN_ABORT | wx.PD_APP_MODAL | wx.PD_ESTIMATED_TIME | wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME)
           def callback(idx, name):
               # called at the start of each file, with 0-based idx
               kont, skip = progress.Update(idx, 'Processing %s'%(name))
               if not kont:
                   raise StopProcessing
           try:
               xmls_to_xls(self.parent_dir.dirname.Value, xmlfiles, outfile, callback, lookup_treatment(self.extract_from_DB.StringSelection))
           except StopProcessing:
               pass
           progress.Destroy()
           progress = None
       except Exception, e:
           if progress:
               progress.Destroy()
           traceback_text = "".join(traceback.format_exception(type(e), e.message, sys.exc_info()[2]))
           dlg = wx.MessageDialog(None, 'Error processing XML\n%s\n%s'%(traceback_text, str(e)),
                                  'Error', wx.OK | wx.ICON_ERROR)
           dlg.ShowModal()
           dlg.Destroy()

   def warn_bad_xml(self, warn_no_files, warn_too_many_files):
       warn_texts = []
       if len(warn_no_files) > 0:
           warn_texts += ['These subdirectories had no matching XML files:']
           warn_texts += ['     %s'%(pld) for pld in warn_no_files]
       if len(warn_too_many_files) > 0:
           warn_texts += ['', 'These subdirectories had multiple XML files (will use youngest, shown)']
           for subdir, pld, xmlnames in warn_too_many_files:
               warn_texts += ['     %s'%(os.path.join(subdir, pld))]
               warn_texts += ['          %s'%(x) for x in xmlnames]
       if len(warn_texts) > 0:
           nm = NonModalWarning("\n".join(warn_texts))
           sz = nm.Size
           for wt in warn_texts:
               sz.SetWidth(max(sz.GetWidth(), nm.GetFullTextExtent(wt)[0]))
           nm.Size = sz
           nm.Fit()
           nm.Show(True)

# XML parsing

def xmls_to_xls(parent_dir, xmlfiles, outfile, callback, lookup_well_treatment):
    xmls_to_xls.active = False
    xmls_to_xls.rowidx = 1 # start at 1, go back and write header
    rowvals = {}

    class StopParsing(Exception):
        pass

    outf = open(outfile, "wb")

    def start_element(name, attrs):
        if name == 'Table' and attrs['title'] == 'Wells Summary':
            xmls_to_xls.active = True
        elif xmls_to_xls.active:
            if name == 'Well':
                start_well(attrs['row'], attrs['col'], attrs['name'])
            elif name == 'Measure':
                emit_col('%s\n%s'%(attrs['source'], attrs['name']), attrs['value'])

    def end_element(name):
        if xmls_to_xls.active:
            if name == 'Well':
                end_well()
                pass
            elif name == 'Table':
                raise StopParsing

    def parse_plate(name):
        return name


    def make_sheetname(name):
        for bad, good in zip("[]:\\?/*\x00", "().-.-.."):
            name = name.replace(bad, good)
        return name

    xmlfiles.sort()
    book = xlwt.Workbook()
    cursheet = book.add_sheet(make_sheetname(xmlfiles[0][0]))

    numsheets = 1

    feature_to_col = {}
    def lookup_feature_col(feature):
        return feature_to_col.setdefault(feature, len(feature_to_col))

    for idx, (subdir, platedir, xmlfile) in enumerate(xmlfiles):
        callback(idx, os.path.join(subdir, platedir, xmlfile))

        def start_well(wellrow, wellcol, wellname):
            rowvals.clear()
            # force these to be first
            lookup_feature_col('Plate')
            lookup_feature_col('Well')
            if lookup_treatment is not None:
                lookup_feature_col('Treatment')
            rowvals['Plate'] = parse_plate(platedir)
            # prefer well row/column, but use name if they are not valid
            if int(wellrow) > 0 and int(wellcol) > 0:
                rowvals['Well'] = '%s%02d'%('ABCDEFGHIJKLMNOP'[int(wellrow)-1], int(wellcol))
            else:
                rowvals['Well'] = wellname
            if lookup_well_treatment is not None:
                rowvals['Treatment'] = lookup_well_treatment(platedir, wellrow, wellcol)

        def end_well():
            colvals = sorted([(lookup_feature_col(feature), rowvals.get(feature, '')) for feature in feature_to_col])
            for idx, val in colvals:
                cursheet.write(xmls_to_xls.rowidx, idx, val)
            xmls_to_xls.rowidx += 1

        def emit_col(feature, value):
            lookup_feature_col(feature)
            rowvals[feature] = value

        if cursheet.name != make_sheetname(subdir):
            cursheet = book.add_sheet(make_sheetname(subdir))
            numsheets += 1
            xmls_to_xls.rowidx = 1 # start at 1, go back and write header

        xmls_to_xls.active = False
        inf = open(os.path.join(parent_dir, subdir, platedir, xmlfile))
        try:
            # create the parser
            parser = xml.parsers.expat.ParserCreate()
            parser.returns_unicode = False
            parser.StartElementHandler = start_element
            parser.EndElementHandler = end_element
            parser.ParseFile(inf)
        except StopParsing:
            pass
        inf.close()


    # write header row
    for idx in range(numsheets):
        sheet = book.get_sheet(idx)
        colvals = sorted([(lookup_feature_col(feature), feature) for feature in feature_to_col])
        for idx, val in colvals:
            sheet.write(0, idx, val)

    # done
    book.save(outf)
    outf.close()


class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, -1, "Excel sheet extractor")
        frame.Show(True)
        self.SetTopWindow(frame)
        return True

app = MyApp(0)
app.MainLoop()
