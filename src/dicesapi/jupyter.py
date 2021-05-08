import ipywidgets as widgets
from IPython.display import display

class NotebookPBar(object):
    '''Create a notebook style progress bar'''
    
    def __init__(self, start=0, max=100):
        self.pbar = widgets.IntProgress(
            value = start,
            min = 0,
            max = max,
            bar_style='info',
            orientation='horizontal'
        )
        self.label = widgets.Label()
        self.output = widgets.HBox([self.pbar, self.label])
        self.updateLabel()
        display(self.output)
        
    def update(self, value):
        self.pbar.value=value
        self.updateLabel()
        
    def updateLabel(self):
        self.label.value=f'{self.pbar.value}/{self.pbar.max}'