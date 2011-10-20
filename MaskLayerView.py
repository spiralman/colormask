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
            
            self.point_callback = None
            self.rendered = None
            
            self.zoom_factor = 1.0
            self.translation = (0.0,0.0)
            
            self.root_layer = CALayer.layer()
            self.root_layer.setNeedsDisplayOnBoundsChange_(True)
            self.root_layer.setMasksToBounds_(True)
            
            self.setLayer_(self.root_layer)
            self.setWantsLayer_(True)
        
            # redraw when requested
            self.setLayerContentsRedrawPolicy_(1)
            # center.
            self.setLayerContentsPlacement_(3)
            
            self.content_layer = None
        return self
    
    def acceptsFirstResponder(self):
        return True

    def awakeFromNib(self):
        #self.window().makeFirstResponder_(self)
        pass
    
    def displayLayer_(self,layer):
        if self.rendered != None:
            layer.setContents_(self.rendered)
    
    def setImageWithURL_(self,url):        
        self.image = CIImage.imageWithContentsOfURL_(url)
        
        nsContext = NSGraphicsContext.graphicsContextWithAttributes_({'NSGraphicsContextDestinationAttributeName':'NSBitmapImageRep'})
        ciContext = CIContext.contextWithCGContext_options_(nsContext.graphicsPort(), None)
        
        self.rendered = ciContext.createCGImage_fromRect_(self.image,self.image.extent())
        
        self.content_layer = self.getNewEmptyLayer(centerLayer=False)
        self.root_layer.addSublayer_(self.content_layer)
        
        self.centerImageAnchor()
        
        CGImageRetain(self.rendered)
    
    def getNewEmptyLayer(self, centerLayer=True):
        newLayer = CALayer.layer()
        newLayer.setDelegate_(self)
            
        newLayer.setAutoresizingMask_(kCALayerMinXMargin | kCALayerMaxXMargin | kCALayerMinYMargin | kCALayerMaxYMargin)
        
        newLayer.setBounds_(self.image.extent())
        
        if centerLayer:
            center = CGPoint()
            center.x = self.content_layer.bounds().size.width / 2
            center.y = self.content_layer.bounds().size.height / 2
            
            newLayer.setPosition_(center)
        
        return newLayer
    
    def getNewContentLayer(self):
        newLayer = self.getNewEmptyLayer()
        
        newLayer.setContents_(self.rendered)
        
        return newLayer
    
    def showLayer(self,layer):
        self.content_layer.setSublayers_(None)
        self.content_layer.addSublayer_(layer)
    
    def selectPoint(self, callback):
        self.point_callback = callback
    
    def onBoundsChanged_(self,notification):
        self.root_layer.setBounds_(self.bounds())
        self.applyAnchorWithinBounds(self.content_layer.anchorPoint())
    
    def centerImageAnchor(self):
        center = CGPoint()
        center.x = self.bounds().size.width / 2
        center.y = self.bounds().size.height / 2
            
        self.content_layer.setPosition_(center)
        
    def updateTransform(self):
        transform = CATransform3DMakeScale(self.zoom_factor, self.zoom_factor, 1.0)
        
        self.content_layer.setTransform_(transform)
        self.setNeedsDisplay_(True)
        
    def setZoomFactor_(self,factor):
        factor = max(0.001,factor)
        self.zoom_factor = factor
        self.updateTransform()
        self.applyAnchorWithinBounds(self.content_layer.anchorPoint())
    
    def zoomFactor(self):
        return self.zoom_factor
    
    def zoomImageToFit_(self,sender):
        width_scale = self.bounds().size.width / self.image.extent().size.width
        height_scale = self.bounds().size.height / self.image.extent().size.height
        self.setZoomFactor_(min(width_scale,height_scale))
    
    def zoomImageToActualSize_(self,sender):
        self.setZoomFactor_(1.0)
    
    def zoomIn_(self,sender):
        self.setZoomFactor_(self.zoom_factor + (0.2 * self.zoom_factor))
    
    def zoomOut_(self,sender):
        self.setZoomFactor_(self.zoom_factor - (0.2 * self.zoom_factor))
        
    def applyAnchorWithinBounds(self,anchorPoint):
        current_size = self.bounds().size
        image_size = self.image.extent().size
        
        x_margin = (current_size.width / 2) / self.zoom_factor / image_size.width
        y_margin = (current_size.height / 2) / self.zoom_factor / image_size.height
        
        x_margin = min(x_margin,0.5)
        y_margin = min(y_margin,0.5)
        
        if anchorPoint.x < x_margin:
            anchorPoint.x = x_margin
        elif anchorPoint.x > 1.0 - x_margin:
            anchorPoint.x = 1.0 - x_margin
        
        if anchorPoint.y < y_margin:
            anchorPoint.y = y_margin
        elif anchorPoint.y > 1.0 - y_margin:
            anchorPoint.y = 1.0 - y_margin
        
        self.content_layer.setAnchorPoint_(anchorPoint)
        self.centerImageAnchor()
    
    def mouseDown_(self,event):
        if self.point_callback == None:
            self.mouse_last_pos = event.locationInWindow()
    
    def mouseDragged_(self,event):
        if self.point_callback == None:
            cur_pos = event.locationInWindow()
        
            anchorPoint = self.content_layer.anchorPoint()
            anchorPoint.x = anchorPoint.x - (((cur_pos.x - self.mouse_last_pos.x) / self.zoom_factor) / self.image.extent().size.width)
            anchorPoint.y = anchorPoint.y - (((cur_pos.y - self.mouse_last_pos.y) / self.zoom_factor) / self.image.extent().size.height)
        
            self.applyAnchorWithinBounds(anchorPoint)
        
            self.mouse_last_pos = cur_pos
    
    def mouseUp_(self,event):
        if self.point_callback == None:
            self.mouse_last_pos = None
        else:
            local_point = self.convertPoint_fromView_(event.locationInWindow(),None)
            image_point = self.root_layer.convertPoint_toLayer_(local_point, self.content_layer)
            self.point_callback(image_point)
            self.point_callback = None
        
    def scrollWheel_(self,event):
        anchorPoint = self.content_layer.anchorPoint()
        anchorPoint.x = anchorPoint.x - (event.deltaX() / self.zoom_factor / self.image.extent().size.width)
        anchorPoint.y = anchorPoint.y + (event.deltaY() / self.zoom_factor / self.image.extent().size.height)
        self.applyAnchorWithinBounds(anchorPoint)
