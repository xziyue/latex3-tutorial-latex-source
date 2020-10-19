import sys
import os

_this_dir, _ = os.path.split(os.path.abspath(__file__))
_last_dir, _ = os.path.split(_this_dir)
sys.path.append(_last_dir)

import wx
from pygments import highlight
from tex_lexer import Tex3Lexer
from pygments.formatters.html import HtmlFormatter

class CodeHtmlFormatter(HtmlFormatter):
    def wrap(self, source, outfile):
        return self._wrap_code(source)

    def _wrap_code(self, source):
        yield 0, '<code class="highlight">'
        for i, t in source:
            if i == 1:
                # it's a line of formatted code
                pass
            yield i, t
        yield 0, '</code>'

class MyFrame(wx.Frame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel = wx.Panel(self)

        self.SetSize(wx.Size(800, 600))
        self.SetTitle('Highlight LaTeX3')

        self.textIn = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE)
        self.textOut = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        sizer.Add(self.textIn, 1, wx.ALL | wx.EXPAND, 10)
        sizer.Add(self.textOut, 1, wx.ALL | wx.EXPAND, 10)

        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btnConv1 = wx.Button(self.panel, label='Convert (Block)')
        self.btnConv1.Bind(wx.EVT_BUTTON, self.evtBtn1)
        hSizer.Add(self.btnConv1, 1, wx.ALL | wx.ALIGN_CENTER, 10)
        self.btnConv2 = wx.Button(self.panel, label='Convert (Inline)')
        self.btnConv2.Bind(wx.EVT_BUTTON, self.evtBtn2)
        hSizer.Add(self.btnConv2, 1, wx.ALL | wx.ALIGN_CENTER, 10)

        sizer.Add(hSizer, 0, wx.ALL | wx.EXPAND)

        self.panel.SetSizerAndFit(sizer)

        self.Show()


    def evtBtn1(self, evt):
        inText = self.textIn.GetValue()
        output = highlight(inText, Tex3Lexer(), HtmlFormatter())
        self.textOut.SetValue(output)

    def evtBtn2(self, evt):
        inText = self.textIn.GetValue()
        output = highlight(inText, Tex3Lexer(), CodeHtmlFormatter())
        self.textOut.SetValue(output)


app = wx.App()
MyFrame(None)
app.MainLoop()
