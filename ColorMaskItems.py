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

import pdb

class ItemWithImage(NSObject):
    def init(self):
        self = super(ItemWithImage,self).init()
        
        self.layer = None
        self.filters = []
        
        return self
    
    def initFromDoc_(self,doc):
        self = self.init()
        self.doc = doc
        self.layer = None
        
        return self
        
    def numChildren(self):
        return 0
    
    def hasChildren(self):
        return False
    
    def shouldSelect(self):
        return True
    
    def imageSet(self):
        self.layer = self.doc.image_view.getNewContentLayer()
        self.updateImage()
    
    def selected(self):
        if self.layer:
            #self.doc.image_view.showLayer(self.layer)
            self.updateImage()
    
    def unselected(self):
        pass
    
    def updateImage(self):
        if self.layer != None:
            self.layer.setFilters_(self.filters)
            self.doc.image_view.setNeedsDisplay_(True)
        
    def renderImage(self, dest, properties):
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
        
        CGImageDestinationAddImage(dest, rendered, properties)
        
        CGImageDestinationFinalize(dest)

class OriginalItem(ItemWithImage):
    def initFromDoc_(self,doc):
        self = super(OriginalItem,self).initFromDoc_(doc)
        
        self.name = NSString.stringWithString_('Original Image')
        
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
    
    selection_menu = objc.IBOutlet()
    color_picker = objc.IBOutlet()
    
    chroma_slider = objc.IBOutlet()
    chroma_text = objc.IBOutlet()
    chroma_stepper = objc.IBOutlet()
    
    luminance_slider = objc.IBOutlet()
    luminance_text = objc.IBOutlet()
    luminance_stepper = objc.IBOutlet()
    
    falloff_slider = objc.IBOutlet()
    falloff_text = objc.IBOutlet()
    falloff_stepper = objc.IBOutlet()
    
    invert = objc.IBOutlet()
    
    halftone_menu = objc.IBOutlet()
    
    halftone_angle = objc.IBOutlet()
    halftone_angle_text = objc.IBOutlet()
    halftone_angle_stepper = objc.IBOutlet()
    
    halftone_width = objc.IBOutlet()
    halftone_width_text = objc.IBOutlet()
    halftone_width_stepper = objc.IBOutlet()
    
    halftone_sharpness = objc.IBOutlet()
    halftone_sharpness_text = objc.IBOutlet()
    halftone_sharpness_stepper = objc.IBOutlet()
    
    halftone_x = objc.IBOutlet()
    halftone_y = objc.IBOutlet()
    halftone_center_picker = objc.IBOutlet()
    
    view_controller = objc.IBOutlet()
    tool_panel = objc.IBOutlet()
    
    def setDoc_Mask_(self,doc,mask):
        self.doc = doc
        
        self.mask = mask
        self.name = self.mask.valueForKey_('name')
        
        tool_panel_controller = NSWindowController.alloc().initWithWindow_(self.tool_panel)
        
        self.doc.addWindowController_(tool_panel_controller)
        self.tool_panel.setWindowController_(tool_panel_controller)
        
        self.colorTransformer = NSValueTransformer.valueTransformerForName_('CIColorToNSColorTransformer')
        
        self.selection_filters = [self.createFilterWithName('ColorDistance', 'colorDistance'), 
                                self.createFilterWithName('LuminanceDistance', 'luminanceDistance'),
                                self.createFilterWithName('PerceptualDistance', 'perceptualDistance')]
        
        for filter in self.selection_filters:
            self.updateSelectionFilterFromMask(filter)
        
        self.halftone_filters = [self.createFilterWithName('CIDotScreen','dotScreen'),
                                self.createFilterWithName('CILineScreen', 'lineScreen'),
                                self.createFilterWithName('CIHatchedScreen', 'hatchScreen'),
                                self.createFilterWithName('CICircularScreen', 'circleScreen')]
        
        for filter in self.halftone_filters:
            self.updateHalftoneFilterFromMask(filter)
        
        self.inverter = CIFilter.filterWithName_keysAndValues_('CIColorInvert',
            'name','inverter')
        
        self.mask.addObserver_forKeyPath_options_context_(self, 'name', 0, None)
        self.mask.addObserver_forKeyPath_options_context_(self, 'selectionMode', 0, None)
        self.mask.addObserver_forKeyPath_options_context_(self, 'color', 0, None)
        self.mask.addObserver_forKeyPath_options_context_(self, 'chromaTolerance', 0, None)
        self.mask.addObserver_forKeyPath_options_context_(self, 'luminanceTolerance', 0, None)
        self.mask.addObserver_forKeyPath_options_context_(self, 'falloff', 0, None)
        self.mask.addObserver_forKeyPath_options_context_(self, 'invert', 0, None)
        
        self.mask.addObserver_forKeyPath_options_context_(self, 'halftoneMode', 0, None)
        self.mask.addObserver_forKeyPath_options_context_(self, 'halftoneSharpness', 0, None)
        self.mask.addObserver_forKeyPath_options_context_(self, 'halftoneWidth', 0, None)
        self.mask.addObserver_forKeyPath_options_context_(self, 'halftoneAngle', 0, None)
        self.mask.addObserver_forKeyPath_options_context_(self, 'halftoneCenterX', 0, None)
        self.mask.addObserver_forKeyPath_options_context_(self, 'halftoneCenterY', 0, None)
        
        self.name_input.bind_toObject_withKeyPath_options_('value', self.mask, 'name', None)
        self.selection_menu.bind_toObject_withKeyPath_options_('selectedTag', self.mask, 'selectionMode', None)
        
        self.chroma_slider.bind_toObject_withKeyPath_options_('value', self.mask, 'chromaTolerance', None)
        self.chroma_text.bind_toObject_withKeyPath_options_('value', self.mask, 'chromaTolerance', None)
        self.chroma_stepper.bind_toObject_withKeyPath_options_('value', self.mask, 'chromaTolerance', None)
        
        self.luminance_slider.bind_toObject_withKeyPath_options_('value', self.mask, 'luminanceTolerance', None)
        self.luminance_text.bind_toObject_withKeyPath_options_('value', self.mask, 'luminanceTolerance', None)
        self.luminance_stepper.bind_toObject_withKeyPath_options_('value', self.mask, 'luminanceTolerance', None)
        
        self.falloff_slider.bind_toObject_withKeyPath_options_('value', self.mask, 'falloff', None)
        self.falloff_text.bind_toObject_withKeyPath_options_('value', self.mask, 'falloff', None)
        self.falloff_stepper.bind_toObject_withKeyPath_options_('value', self.mask, 'falloff', None)
        
        self.color_picker.bind_toObject_withKeyPath_options_('value', self.mask, 'color', None)
        self.invert.bind_toObject_withKeyPath_options_('value', self.mask, 'invert', None)
        
        self.halftone_menu.bind_toObject_withKeyPath_options_('selectedTag', self.mask, 'halftoneMode', None)
        
        self.halftone_angle.bind_toObject_withKeyPath_options_('value', self.mask, 'halftoneAngle', None)
        self.halftone_angle_text.bind_toObject_withKeyPath_options_('value', self.mask, 'halftoneAngle', None)
        self.halftone_angle_stepper.bind_toObject_withKeyPath_options_('value', self.mask, 'halftoneAngle', None)
        
        self.halftone_width.bind_toObject_withKeyPath_options_('value', self.mask, 'halftoneWidth', None)
        self.halftone_width_text.bind_toObject_withKeyPath_options_('value', self.mask, 'halftoneWidth', None)
        self.halftone_width_stepper.bind_toObject_withKeyPath_options_('value', self.mask, 'halftoneWidth', None)
        
        self.halftone_sharpness.bind_toObject_withKeyPath_options_('value', self.mask, 'halftoneSharpness', None)
        self.halftone_sharpness_text.bind_toObject_withKeyPath_options_('value', self.mask, 'halftoneSharpness', None)
        self.halftone_sharpness_stepper.bind_toObject_withKeyPath_options_('value', self.mask, 'halftoneSharpness', None)
        
        self.halftone_x.bind_toObject_withKeyPath_options_('value', self.mask, 'halftoneCenterX', None)
        self.halftone_y.bind_toObject_withKeyPath_options_('value', self.mask, 'halftoneCenterY', None)
    
    def awakeFromNib(self):
        # lets the ColorMaskList item get at the instance created in the Nib
        self.view_controller.setRepresentedObject_(self)
    
    def createFilterWithName(self, className, filterName):
        return CIFilter.filterWithName_keysAndValues_(className, 
            'name', filterName, None)
    
    def updateSelectionFilterFromMask(self, filter):
        self.updateFilterKeyValues(filter, 'inputColor', self.colorTransformer.transformedValue_(self.mask.valueForKey_('color')))
        self.updateFilterKeyValues(filter, 'inputChromaTolerance', self.mask.valueForKey_('chromaTolerance'))
        self.updateFilterKeyValues(filter, 'inputLuminanceTolerance', self.mask.valueForKey_('luminanceTolerance'))
        self.updateFilterKeyValues(filter, 'inputFalloff', self.mask.valueForKey_('falloff'))
    
    def updateHalftoneFilterFromMask(self, filter):
        self.updateFilterKeyValues(filter, 'inputWidth', self.mask.valueForKey_('halftoneWidth'))
        self.updateFilterKeyValues(filter, 'inputAngle', self.mask.valueForKey_('halftoneAngle'))
        self.updateFilterKeyValues(filter, 'inputSharpness', self.mask.valueForKey_('halftoneSharpness'))
        self.updateFilterKeyValues(filter, 'inputCenter', 
                                CIVector.vectorWithX_Y_(self.mask.valueForKey_('halftoneCenterX'), 
                                                        self.mask.valueForKey_('halftoneCenterY')))
    
    def updateFilterKeyValues(self,filter,key,value):
        if key in filter.attributes():
            filter.setValue_forKey_(value, key)
            if filter in self.filters:
                self.layer.setValue_forKeyPath_(value, 'filters.{0}.{1}'.format(filter.valueForKey_('name'),key))
    
    def observeValueForKeyPath_ofObject_change_context_(self,keyPath, object, change, context):
        selection_filter = self.selection_filters[self.selection_menu.selectedItem().tag()]
        
        # The background filters array in the layer object is a copy of our filters array, 
        # so changes to the filters in the layer don't affect our copy of the filters.
        if keyPath == 'color':
            color = self.colorTransformer.transformedValue_(self.mask.valueForKey_('color'))
            self.updateFilterKeyValues(selection_filter, 'inputColor',color)
        elif keyPath == 'chromaTolerance':
            self.updateFilterKeyValues(selection_filter, 'inputChromaTolerance',self.mask.valueForKey_('chromaTolerance'))
        elif keyPath == 'luminanceTolerance':
            self.updateFilterKeyValues(selection_filter, 'inputLuminanceTolerance',self.mask.valueForKey_('luminanceTolerance'))
        elif keyPath == 'falloff':
            falloff = self.mask.valueForKey_('falloff')
            if falloff == 0:
                falloff = 0.0000001
            self.updateFilterKeyValues(selection_filter, 'inputFalloff',falloff)
        elif keyPath == 'selectionMode' or keyPath == 'halftoneMode' or keyPath == 'invert':
            self.updateImage()
        elif keyPath.startswith('halftone'):
            halftone_mode = self.halftone_menu.selectedItem().tag()
            if halftone_mode > -1:
                halftone_filter = self.halftone_filters[halftone_mode]
                value = self.mask.valueForKey_(keyPath)
                filter_key =  keyPath.replace('halftone','input')
                if keyPath == 'halftoneCenterX':
                    value = CIVector.vectorWithX_Y_(value, self.mask.valueForKey_('halftoneCenterY'))
                    filter_key = 'inputCenter'
                elif keyPath == 'halftoneCenterY':
                    value = CIVector.vectorWithX_Y_(self.mask.valueForKey_('halftoneCenterX'), value)
                    filter_key = 'inputCenter'
                self.updateFilterKeyValues(halftone_filter,filter_key, value)
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
        
        self.mask.removeObserver_forKeyPath_(self, 'halftoneMode')
        self.mask.removeObserver_forKeyPath_(self, 'halftoneSharpness')
        self.mask.removeObserver_forKeyPath_(self, 'halftoneWidth')
        self.mask.removeObserver_forKeyPath_(self, 'halftoneAngle')
        self.mask.removeObserver_forKeyPath_(self, 'halftoneCenterX')
        self.mask.removeObserver_forKeyPath_(self, 'halftoneCenterY')
        
        self.name_input.unbind_('value')
        self.chroma_slider.unbind_('value')
        self.luminance_slider.unbind_('value')
        self.falloff_slider.unbind_('value')
        self.color_picker.unbind_('value')
        self.invert.unbind_('value')
        self.selection_menu.unbind_('tag')
        
        self.halftone_menu.unbind_('selectedTag')
        
        self.halftone_angle.unbind_('value')
        self.halftone_angle_text.unbind_('value')
        self.halftone_angle_stepper.unbind_('value')
        
        self.halftone_width.unbind_('value')
        self.halftone_width_text.unbind_('value')
        self.halftone_width_stepper.unbind_('value')
        
        self.halftone_sharpness.unbind_('value')
        self.halftone_sharpness_text.unbind_('value')
        self.halftone_sharpness_stepper.unbind_('value')
        self.halftone_x.unbind_('value')
        self.halftone_y.unbind_('value')
    
    def selected(self):
        self.tool_panel.makeKeyAndOrderFront_(self)
        super(MaskItem,self).selected()
    
    def unselected(self):
        self.tool_panel.orderOut_(self)
    
    @objc.IBAction
    def selectHalftoneCenterPushed_(self,sender):
        self.doc.image_view.selectPoint(self.halftoneCenterSelected)
    
    def halftoneCenterSelected(self,point):
        self.mask.setValue_forKey_(point.x, 'halftoneCenterX')
        self.mask.setValue_forKey_(point.y, 'halftoneCenterY')
        self.halftone_center_picker.setState_(NSOffState)
    
    def updateImage(self):
        self.filters = []
            
        selection_filter = self.selection_filters[self.selection_menu.selectedItem().tag()]
        self.updateSelectionFilterFromMask(selection_filter)
            
        self.filters = [selection_filter]
            
        if self.invert.state() == NSOnState:
            self.filters.append(self.inverter)
            
        halftone_mode = self.halftone_menu.selectedItem().tag()
            
        if halftone_mode > -1:
            halftone_filter = self.halftone_filters[halftone_mode]
                
            self.updateHalftoneFilterFromMask(halftone_filter)
            self.filters.append(halftone_filter)

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
