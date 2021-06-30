import ipywidgets as widgets
from IPython.display import display

class NotebookPBar(object):
    '''Create a notebook style progress bar'''
    
    def __init__(self, start=0, max=100, prefix=None):
        self.pbar = widgets.IntProgress(
            value = start,
            min = 0,
            max = max,
            bar_style='info',
            orientation='horizontal'
        )
        if prefix is not None:
            self.prefix = prefix.strip() + ' '
        else:
            self.prefix = ''
        self.label = widgets.Label()
        self.output = widgets.HBox([self.pbar, self.label])
        self.updateLabel()
        display(self.output)
        
    def update(self, value=None):
        if value is not None:
            self.pbar.value=value
        else:
            self.pbar.value += 1
        self.updateLabel()
        
    def updateLabel(self):
        self.label.value=f'{self.prefix}{self.pbar.value}/{self.pbar.max}'
