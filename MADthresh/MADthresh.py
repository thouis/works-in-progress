import sys
import wx
import  wx.lib.scrolledpanel
import numpy as np
import matplotlib
matplotlib.use('WxAgg') 
import pylab
import Image
from cpmath.outline import outline

def MAD_based_error(im):
    hist, bins = np.histogram(im, 100)
    # bins is the set of possible thresholds.
    
    # compute medians of the lower intensity of pixels for every possible threshold
    

def wMADthresh(im):
    err = MAD_based_error(im)

    
    

class ImagePanel(wx.lib.scrolledpanel.ScrolledPanel):
    def __init__(self, parent, im):
        # make the scrolled panel larger than its parent
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, 
            wx.ID_ANY, style=wx.TAB_TRAVERSAL)
        self.SetupScrolling()

        self.im = im

        # get the width and height of the parent
        bmp = self.im_to_bmp(im)
        self.sbmp = sbmp = wx.StaticBitmap(self, wx.ID_ANY, bmp)
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(sbmp, 0, wx.ALL, 5)
        self.SetSizer(vbox)

    def update(self, thresh):
        self.sbmp.SetBitmap(self.im_to_bmp(self.threshold(thresh)))
        self.sbmp.Refresh()

    def threshold(self, thresh):
        print thresh
        return self.im + im.max() * outline(self.im > thresh)

    def im_to_bmp(self, im):
        h, w = im.shape
        im = ((im / im.max()).flatten() * 255).astype(np.uint8)
        stacked = np.dstack((im, im, im)) # gray to RGB
        image = wx.EmptyImage(w, h)
        image.SetData(stacked.tostring())
        return wx.BitmapFromImage(image)

class ControlPanel(wx.Panel):
    def __init__(self, parent, impanel, im):
        wx.Panel.__init__(self, parent, wx.ID_ANY)

        self.impanel = impanel
        self.im = im

        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)

        self.sld = wx.Slider(self, -1, 50, 0, 100, (-1, -1), (250, -1), 
                             wx.SL_AUTOTICKS | wx.SL_HORIZONTAL | wx.SL_LABELS)
        btn1 = wx.Button(self, 1, 'Adjust')
        btn2 = wx.Button(self, 2,  'Close')

        wx.EVT_BUTTON(self, 1, self.OnOk)
        wx.EVT_BUTTON(self, 2, self.OnClose)

        vbox.Add(self.sld, 1, wx.ALIGN_CENTRE)
        hbox.Add(btn1, 1, wx.RIGHT, 10)
        hbox.Add(btn2, 1)
        vbox.Add(hbox, 0, wx.ALIGN_CENTRE | wx.ALL, 20)
        self.SetSizer(vbox)

    def OnOk(self, evt):
        thresh = wMADthresh(self.im)

        self.impanel.update(thresh)

    def OnClose(self, evt):
        wx.GetApp().Close()

        

def PIL_to_numpy(img):
    assert img.mode == 'I;16'
    imgdata = np.fromstring(img.tostring(),np.uint8)
    imgdata.shape=(int(imgdata.shape[0]/2),2)
    imgdata = imgdata.astype(np.uint16)
    hi,lo = (0,1) if img.tag.prefix == 'MM' else (1,0)
    imgdata = imgdata[:,hi]*256 + imgdata[:,lo]
    img_size = list(img.size)
    img_size.reverse()
    return imgdata.reshape(img_size)
    


im = PIL_to_numpy(Image.open(sys.argv[1]))
im = np.log(im.astype(float))
im -= im.min()
im /= im.max()

app = wx.App(0)

# create window/frame
mytitle = "Image thresholder"
imframe = wx.Frame(None, wx.ID_ANY, title=mytitle, size=(480, 480))
impanel = ImagePanel(imframe, im)
imframe.Show(True)

# create control pane
ctrlframe = wx.Frame(None, wx.ID_ANY, title='threshold controls', size=(200, 100))
ControlPanel(ctrlframe, impanel, im)
ctrlframe.Show(True)

app.MainLoop()
