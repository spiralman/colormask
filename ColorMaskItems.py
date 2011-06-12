#
#  ColorMaskItems.py
#  ColorMask
#
#  Created by Thomas Stephens on 6/4/11.
#  Copyright (c) 2011 __MyCompanyName__. All rights reserved.
#

import objc

from Foundation import *
from CoreData import *
from AppKit import *
from Quartz import *

class ItemWithImage(NSObject):
    def init(self):
        self = super(ItemWithImage,self).init()
        
        self.layer = CALayer.layer()
        self.filters = []
        
        return self
    
    def initFromDoc_(self,doc):
        self = self.init()
        self.doc = doc
        
        return self
        
    def numChildren(self):
        return 0
    
    def hasChildren(self):
        return False
    
    def shouldSelect(self):
        return True
    
    def selected(self):
        if self.doc.image != None:
            self.doc.image_view.setOverlay_forType_(self.layer, IKOverlayTypeImage)
    
    def unselected(self):
        pass
    
    def updateImage(self):
        self.layer.setBackgroundFilters_(self.filters)
        self.layer.setNeedsDisplay()
        
    def renderImage(self):
        cur_image = self.doc.image
        
        sourceRect = cur_image.extent()
        
        width = sourceRect.size.width
        height = sourceRect.size.height
        
        imageData = objc.allocateBuffer(int(4 * width * height))
        
        bitmapContext = CGBitmapContextCreate(imageData, width,height,8,4 * width,CGImageGetColorSpace(cur_image.cgImageRepresentation()),kCGImageAlphaPremultipliedFirst)
        
        ciContext = CIContext.contextWithCGContext_options_(bitmapContext, None)
        
        for filter in self.filters:
            filter.setValue_forKey_(cur_image, 'inputImage')
        
            cur_image = filter.valueForKey_('outputImage')
        
        rendered = ciContext.createCGImage_fromRect_(cur_image,sourceRect)
        
        del bitmapContext
        
        return rendered

class OriginalItem(ItemWithImage):
    def initFromDoc_(self,doc):
        self = super(OriginalItem,self).initFromDoc_(doc)
        
        self.name = NSString.stringWithString_('Original Image')
        
        return self

class StackedItem(ItemWithImage):
    def initFromDoc_(self,doc):
        self = super(StackedItem,self).initFromDoc_(doc)
        
        self.name = NSString.stringWithString_('Stacked')
        
        return self
        
class FlattenedItem(ItemWithImage):
    def initFromDoc_(self,doc):
        self = super(FlattenedItem,self).initFromDoc_(doc)
        
        self.name = NSString.stringWithString_('Flattened')
        
        return self
        
class ColorListItem(NSObject):
    def initFromDoc_(self,doc):
        self = super(ColorListItem,self).init()
        
        self.name = NSString.stringWithString_('Colors')
        self.doc = doc
        
        self.masks = []
        for mask in sorted(self.doc.project.valueForKey_('masks'), 
                            key = lambda x: x.valueForKey_('sortOrder') ):
            self.addMaskWithMask_(mask)
        
        return self
    
    def addMaskWithMask_(self,mask):
        toolController = NSViewController.alloc().initWithNibName_bundle_('ColorMaskView', None).retain()
        toolController.loadView()
        mask_item = toolController.representedObject()
        mask_item.setDoc_Mask_(self.doc,mask)
        self.masks.append(mask_item)
        
        return mask_item
    
    def numChildren(self):
        return len(self.masks)
        
    def hasChildren(self):
        return True
        
    def child(self,index):
        return self.masks[index]
    
    def shouldSelect(self):
        return False

class MaskItem(ItemWithImage):
    name_input = objc.IBOutlet()
    show_source = objc.IBOutlet()
    
    selection_menu = objc.IBOutlet()
    color_picker = objc.IBOutlet()
    chroma_slider = objc.IBOutlet()
    luminance_slider = objc.IBOutlet()
    falloff_slider = objc.IBOutlet()
    invert = objc.IBOutlet()
    
    halftone_menu = objc.IBOutlet()
    
    view_controller = objc.IBOutlet()
    tool_panel = objc.IBOutlet()
    
    def setDoc_Mask_(self,doc,mask):
        self.doc = doc
        self.mask = mask
        self.name = self.mask.valueForKey_('name')
        
        self.colorTransformer = NSValueTransformer.valueTransformerForName_('CIColorToNSColorTransformer')
        
        self.color_filter = self.createColorFilterWithCurrentSettings()
        self.luminance_filter = self.createLuminanceFilterWithCurrentSettings()
        self.perceptual_filter = self.createPerceptualFilterWithCurrentSettings()
        
        self.selection_filters = [self.color_filter, self.luminance_filter, self.perceptual_filter]
        
        self.inverter = CIFilter.filterWithName_keysAndValues_('CIColorInvert',
            'name','inverter')
        
        self.mask.addObserver_forKeyPath_options_context_(self, 'name', 0, None)
        self.mask.addObserver_forKeyPath_options_context_(self, 'selectionMode', 0, None)
        self.mask.addObserver_forKeyPath_options_context_(self, 'color', 0, None)
        self.mask.addObserver_forKeyPath_options_context_(self, 'chromaTolerance', 0, None)
        self.mask.addObserver_forKeyPath_options_context_(self, 'luminanceTolerance', 0, None)
        self.mask.addObserver_forKeyPath_options_context_(self, 'falloff', 0, None)
        self.mask.addObserver_forKeyPath_options_context_(self, 'invert', 0, None)
        
        self.name_input.bind_toObject_withKeyPath_options_('value', self.mask, 'name', None)
        self.chroma_slider.bind_toObject_withKeyPath_options_('value', self.mask, 'chromaTolerance', None)
        self.luminance_slider.bind_toObject_withKeyPath_options_('value', self.mask, 'luminanceTolerance', None)
        self.falloff_slider.bind_toObject_withKeyPath_options_('value', self.mask, 'falloff', None)
        self.color_picker.bind_toObject_withKeyPath_options_('value', self.mask, 'color', None)
        self.invert.bind_toObject_withKeyPath_options_('value', self.mask, 'invert', None)
        
        self.updateImage()
    
    def awakeFromNib(self):
        # lets the ColorMaskList item get at the instance created in the Nib
        self.view_controller.setRepresentedObject_(self)
    
    def createColorFilterWithCurrentSettings(self):
        return CIFilter.filterWithName_keysAndValues_('ColorDistance',
            'name', 'colorDistance',
            'inputColor', self.colorTransformer.transformedValue_(self.mask.valueForKey_('color')),
            'inputChromaTolerance', self.mask.valueForKey_('chromaTolerance'), 
            'inputFalloff', self.mask.valueForKey_('falloff'), None)
    
    def createLuminanceFilterWithCurrentSettings(self):
        return CIFilter.filterWithName_keysAndValues_('LuminanceDistance',
            'name', 'luminanceDistance',
            'inputLuminanceTolerance', self.mask.valueForKey_('luminanceTolerance'), 
            'inputFalloff', self.mask.valueForKey_('falloff'), None)
    
    def createPerceptualFilterWithCurrentSettings(self):
        return CIFilter.filterWithName_keysAndValues_('PerceptualDistance',
            'name', 'colorDistance',
            'inputColor', self.colorTransformer.transformedValue_(self.mask.valueForKey_('color')),
            'inputChromaTolerance', self.mask.valueForKey_('chromaTolerance'),
            'inputLuminanceTolerance', self.mask.valueForKey_('luminanceTolerance'), 
            'inputFalloff', self.mask.valueForKey_('falloff'), None)
    
    def updateFilterKeyValues(self,key,value):
        for filter in self.selection_filters:
            if key in filter.attributes():
                filter.setValue_forKey_(value, key)
                if filter in self.filters:
                    self.layer.setValue_forKeyPath_(value, 'backgroundFilters.{0}.{1}'.format(filter.valueForKey_('name'),key))
    
    def observeValueForKeyPath_ofObject_change_context_(self,keyPath, object, change, context):
        # The background filters array in the layer object is a copy of our filters array, 
        # so changes to the filters in the layer don't affect our copy of the filters.
        if keyPath == 'color':
            color = self.colorTransformer.transformedValue_(self.mask.valueForKey_('color'))
            self.updateFilterKeyValues('inputColor',color)
        elif keyPath == 'chromaTolerance':
            self.updateFilterKeyValues('inputChromaTolerance',self.mask.valueForKey_('chromaTolerance'))
        elif keyPath == 'luminanceTolerance':
            self.updateFilterKeyValues('inputLuminanceTolerance',self.mask.valueForKey_('luminanceTolerance'))
        elif keyPath == 'falloff':
            falloff = self.mask.valueForKey_('falloff')
            if falloff == 0:
                falloff = 0.0000001
            self.updateFilterKeyValues('inputFalloff',falloff)
        elif keyPath == 'name':
            self.name = self.mask.valueForKey_('name')
            self.doc.source_list.reloadItem_(self)
    
    def unbind(self):
        self.mask.removeObserver_forKeyPath_(self, 'name')
        self.mask.removeObserver_forKeyPath_(self, 'color')
        self.mask.removeObserver_forKeyPath_(self, 'chromaTolerance')
        self.mask.removeObserver_forKeyPath_(self, 'luminanceTolerance')
        self.mask.removeObserver_forKeyPath_(self, 'falloff')
        self.mask.removeObserver_forKeyPath_(self, 'invert')
        self.mask.removeObserver_forKeyPath_(self, 'selectionMode')
        
        self.name_input.unbind_('value')
        self.chroma_slider.unbind_('value')
        self.luminance_slider.unbind_('value')
        self.falloff_slider.unbind_('value')
        self.color_picker.unbind_('value')
        self.invert.unbind_('value')
        self.selection_menu.unbind_('tag')
    
    def selected(self):
        self.updateImage()
        self.tool_panel.makeKeyAndOrderFront_(self)
        super(MaskItem,self).selected()
    
    def unselected(self):
        self.tool_panel.orderOut_(self)
    
    @objc.IBAction
    def showSourceChanged_(self,sender):
        self.updateImage()
    
    @objc.IBAction
    def invertChanged_(self,sender):
        self.updateImage()
    
    @objc.IBAction
    def selectionModeChanged_(self,sender):
        self.updateImage()
    
    def updateImage(self):
        if self.show_source.state() == NSOnState:
            self.filters = []
        else:
            self.filters = [self.selection_filters[self.selection_menu.selectedItem().tag()]]
            if self.invert.state() == NSOnState:
                self.filters.append(self.inverter)

        super(MaskItem,self).updateImage()

class CIColorToNSColorTransformer(NSObject):
    @classmethod
    def transformedValueClass(self):
        return NSColor
        
    @classmethod
    def allowReverseTransformation(self):
        return True
    
    def transformedValue_(self,value):
        return CIColor.colorWithRed_green_blue_alpha_(value.redComponent(), value.greenComponent(), value.blueComponent(), value.alphaComponent())
    
    def reverseTransformedValue_(self,value):
        if value != None:
            return NSColor.colorWithCIColor_(value)
