import sys
import wx
import  wx.lib.scrolledpanel
import numpy as np
import matplotlib
matplotlib.use('WxAgg') 
import pylab
import Image
from cpmath.outline import outline
from cpmath.filter import median_filter

    
    
def wMADthresh(im):
    # Flatten the image, and sort it
    vals = np.sort(im.copy().flatten())
    # Every value is a potential threshold.
    # Get an index to each value.
    idx = np.arange(vals.size, dtype=np.int)
    # The medians of the values below and above the threshold are
    # halfway between that value and the end of the array.
    lo_median = (vals[idx / 2] + vals[(idx + 1) / 2]) / 2.0
    hi_median = vals[vals.size - (vals.size - idx) / 2 - 1]
    # The MAD of an array X of length N can be found by
    # finding two indices, L and H, where:
    #    H - L = N / 2, and
    #    X[H] - median(X) = median(X) - X[L]
    # To find the MAD for each possible threshold, for the low and
    # high fractions, we'll use parallel binary search.
    
    # H/L for low set
    lo_L = np.zeros(vals.size, np.int)
    lo_H = lo_L + idx / 2 # first property, and invariant in the loop below
    
    # H/L for high set
    hi_L = np.zeros(vals.size, np.int)
    hi_H = idx[::-1] / 2

    stepsize = 2 ** int(np.log2(vals.size))
    while stepsize > 0:
        # sign indicates which direction to move lo_L and hi_L
        step = stepsize * np.sign((lo_median - vals[lo_L]) - (vals[lo_H] - lo_median)).astype(int)
        lo_L += step
        np.clip(lo_L, 0, vals.size - 1 - idx / 2, lo_L)
        lo_H = lo_L + idx / 2

        step = stepsize * np.sign((hi_median - vals[hi_L]) - (vals[hi_H] - hi_median)).astype(int)
        hi_L += step
        np.clip(hi_L, 0, vals.size - 1 - idx[::-1] / 2, hi_L)
        hi_H = hi_L + idx[::-1] / 2
        stepsize /= 2

    err = idx * (lo_median - vals[lo_L]) + idx[::-1] * (hi_median - vals[hi_L])
    loerr = (lo_median - vals[lo_L])
    loerr = loerr[2:] + loerr[:-2]
    pylab.plot(loerr)
    pylab.show()
    err = err[2:] + err[:-2]
    return vals[err == err.min()].mean()
    

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
        return self.im + im.max() * outline(self.im > thresh) / 10.0

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

im -= median_filter(im, im > -1, 55)
im -= im.min()
im /= im.max()


pylab.hist(im.flatten(), 100)
pylab.show()


print wMADthresh(im)

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
