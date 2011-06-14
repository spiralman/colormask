#
#  MaskLayerView.py
#  ColorMask
#
#  Created by Thomas Stephens on 6/12/11.
#  Copyright (c) 2011 __MyCompanyName__. All rights reserved.
#

from objc import YES, NO, IBAction, IBOutlet
from Foundation import *
from AppKit import *
from Quartz import *

class MaskLayerView(NSView):
    def initWithFrame_(self, frame):
        self = super(MaskLayerView, self).initWithFrame_(frame)
        if self:
            # initialization code here
            pass
        return self
    
    def acceptsFirstResponder(self):
        return True

    def awakeFromNib(self):
        self.window().makeFirstResponder_(self)
        self.content_layer = CALayer.layer()
        
        self.setLayer_(self.content_layer)
        self.setWantsLayer_(True)
        
        # redraw on resize or when requested
        self.setLayerContentsRedrawPolicy_(3)
        # Fill, preserve aspect.
        self.setLayerContentsPlacement_(1)
        
    def setImageWithURL_(self,url):        
        self.image = CIImage.imageWithContentsOfURL_(url)
        
        ciContext = CIContext.contextWithCGContext_options_(NSGraphicsContext.currentContext().graphicsPort(), None)
        
        rendered = ciContext.createCGImage_fromRect_(self.image,self.image.extent())
        
        CGImageRetain(rendered)
        self.content_layer.setContents_(rendered)
        self.content_layer.setNeedsDisplay()
        
        #rect = self.frame()
        #rect.size.width = rect.size.width + 1
        #self.setFrame_(rect)
        #rect.size.width = rect.size.width - 1
        #self.setFrame_(rect)
    
    def zoomFactor(self):
        return 1.0
