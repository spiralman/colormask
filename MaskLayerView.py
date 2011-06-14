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
            NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(self, self.onBoundsChanged_, NSViewFrameDidChangeNotification, self)
            self.setPostsFrameChangedNotifications_(True)
            
            self.rendered = None
            self.affine_transform = CGAffineTransform()
            self.affine_transform.a = 1.0
            self.affine_transform.b = 0.0
            self.affine_transform.c = 0.0
            self.affine_transform.d = 1.0
            self.affine_transform.tx = 0.0
            self.affine_transform.ty = 0.0
            
            self.root_layer = CALayer.layer()
            self.root_layer.setNeedsDisplayOnBoundsChange_(True)
            self.root_layer.setMasksToBounds_(True)
            
            self.content_layer = CALayer.layer()
            self.content_layer.setDelegate_(self)
            
            self.content_layer.setAutoresizingMask_(kCALayerMinXMargin | kCALayerMaxXMargin | kCALayerMinYMargin | kCALayerMaxYMargin)
            self.root_layer.addSublayer_(self.content_layer)
        
            self.setLayer_(self.root_layer)
            self.setWantsLayer_(True)
        
            # redraw when requested
            self.setLayerContentsRedrawPolicy_(1)
            # center.
            self.setLayerContentsPlacement_(3)
            pass
        return self
    
    def acceptsFirstResponder(self):
        return True

    def awakeFromNib(self):
        self.window().makeFirstResponder_(self)
    
    def displayLayer_(self,layer):
        if self.rendered != None:
            layer.setContents_(self.rendered)
        
    def setImageWithURL_(self,url):        
        self.image = CIImage.imageWithContentsOfURL_(url)
        
        ciContext = CIContext.contextWithCGContext_options_(NSGraphicsContext.currentContext().graphicsPort(), None)
        
        self.rendered = ciContext.createCGImage_fromRect_(self.image,self.image.extent())
        
        CGImageRetain(self.rendered)
        self.content_layer.setContents_(self.rendered)
        
        self.content_layer.setBounds_(self.image.extent())
        
        center = CGPoint()
        center.x = self.bounds().size.width / 2
        center.y = self.bounds().size.height / 2
            
        self.content_layer.setPosition_(center)
        
        self.zoomImageToFit_(self)
    
    def onBoundsChanged_(self,notification):
        self.root_layer.setBounds_(self.bounds())
        
    def setZoomFactor_(self,factor):
        self.affine_transform.a = factor
        self.affine_transform.d = factor
        self.content_layer.setAffineTransform_(self.affine_transform)
        self.setNeedsDisplay_(True)
    
    def zoomFactor(self):
        return self.affine_transform.a
    
    def zoomImageToFit_(self,sender):
        width_scale = self.bounds().size.width / self.image.extent().size.width
        height_scale = self.bounds().size.height / self.image.extent().size.height
        self.setZoomFactor_(min(width_scale,height_scale))
    
    def zoomImageToActualSize_(self,sender):
        self.setZoomFactor_(1.0)
