#
#  ColorMaskDocument.py
#  ColorMask
#
#  Created by Thomas Stephens on 3/27/11.
#  Copyright __MyCompanyName__ 2011. All rights reserved.
#

import math

import os.path

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
    color_picker = objc.IBOutlet()
    chroma_slider = objc.IBOutlet()
    show_source = objc.IBOutlet()
    invert = objc.IBOutlet()
    
    view_controller = objc.IBOutlet()
    tool_panel = objc.IBOutlet()
    
    def setDoc_Mask_(self,doc,mask):
        self.doc = doc
        self.mask = mask
        self.name = self.mask.valueForKey_('name')
        
        self.colorTransformer = NSValueTransformer.valueTransformerForName_('CIColorToNSColorTransformer')
        
        self.mask_filter = self.createFilterWithCurrentSettings()
        self.inverter = CIFilter.filterWithName_keysAndValues_('CIColorInvert',
            'name','inverter')
        
        self.mask.addObserver_forKeyPath_options_context_(self, 'name', 0, None)
        self.mask.addObserver_forKeyPath_options_context_(self, 'color', 0, None)
        self.mask.addObserver_forKeyPath_options_context_(self, 'chromaTolerance', 0, None)
        self.mask.addObserver_forKeyPath_options_context_(self, 'invert', 0, None)
        
        self.name_input.bind_toObject_withKeyPath_options_('value', self.mask, 'name', None)
        self.chroma_slider.bind_toObject_withKeyPath_options_('value', self.mask, 'chromaTolerance', None)
        self.color_picker.bind_toObject_withKeyPath_options_('value', self.mask, 'color', None)
        self.invert.bind_toObject_withKeyPath_options_('value', self.mask, 'invert', None)
        
        self.updateImage()
    
    def awakeFromNib(self):
        # lets the ColorMaskList item get at the instance created in the Nib
        self.view_controller.setRepresentedObject_(self)
    
    def createFilterWithCurrentSettings(self):
        return CIFilter.filterWithName_keysAndValues_('ColorMaskFilterFilter',
            'name', 'colorMask',
            'inputColor', self.colorTransformer.transformedValue_(self.mask.valueForKey_('color')),
            'inputChromaTolerance', self.mask.valueForKey_('chromaTolerance'), None)
    
    def observeValueForKeyPath_ofObject_change_context_(self,keyPath, object, change, context):
        # The background filters array in the layer object is a copy of our filters array, 
        # so changes to the filters in the layer don't affect our copy of the filters.
        if keyPath == 'color':
            color = self.colorTransformer.transformedValue_(self.mask.valueForKey_('color'))
            if len(self.filters) > 0:
                self.layer.setValue_forKeyPath_(color, 'backgroundFilters.colorMask.inputColor')
            self.mask_filter.setValue_forKey_(color, 'inputColor')
        elif keyPath == 'chromaTolerance':
            if len(self.filters) > 0:
                self.layer.setValue_forKeyPath_(self.mask.valueForKey_('chromaTolerance'), 'backgroundFilters.colorMask.inputChromaTolerance')
            self.mask_filter.setValue_forKey_(self.mask.valueForKey_('chromaTolerance'), 'inputChromaTolerance')
        elif keyPath == 'name':
            self.name = self.mask.valueForKey_('name')
            self.doc.source_list.reloadItem_(self)
    
    def unbind(self):
        self.mask.removeObserver_forKeyPath_(self, 'name')
        self.mask.removeObserver_forKeyPath_(self, 'color')
        self.mask.removeObserver_forKeyPath_(self, 'chromaTolerance')
        self.mask.removeObserver_forKeyPath_(self, 'invert')
        
        self.name_input.unbind_('value')
        self.chroma_slider.unbind_('value')
        self.color_picker.unbind_('value')
        self.invert.unbind_('value')
    
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
    
    def updateImage(self):
        if self.show_source.state() == NSOnState:
            self.filters = []
        else:
            self.filters = [self.mask_filter]
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

class ColorMaskDocument(NSPersistentDocument):
    window = objc.IBOutlet()
    source_list = objc.IBOutlet()
    image_view = objc.IBOutlet()
    zoom_slider = objc.IBOutlet()
    
    mask_tool_window = objc.IBOutlet()
    
    ZOOM_OUT = 0
    ZOOM_IN = 1
    ZOOM_ACTUAL_SIZE = 2
    ZOOM_FIT = 3
    
    @classmethod
    def initialize(self):
        """Class initialization, called once at load time.
        Can be used to do static initialization prior to Xib files being loaded.
        self is a class, not an object.
        """
        CIPlugIn.loadAllPlugIns()
        self.colorTransformer = CIColorToNSColorTransformer.alloc().init()
        NSValueTransformer.setValueTransformer_forName_(self.colorTransformer, 'CIColorToNSColorTransformer')
        
    def init(self):
        self = super(ColorMaskDocument,self).init()
        
        self.root = None
        self.project = None
        
        self.selected = None
        self.image = None
        
        return self
    
    def initWithType_error_(self,typeName,outError):
        self,error = super(ColorMaskDocument, self).initWithType_error_(typeName, outError)
        
        objContext = self.managedObjectContext()
        
        objContext.undoManager().disableUndoRegistration()
        
        self.project = NSEntityDescription.insertNewObjectForEntityForName_inManagedObjectContext_('MaskProject', objContext)
        self.project.setValue_forKeyPath_('','sourceURL')
        
        objContext.processPendingChanges()
        objContext.undoManager().enableUndoRegistration()
        
        return self,None
    
    def windowNibName(self):
        return u"ColorMaskDocument"
    
    def validateUserInterfaceItem_(self,item):
        if item.action() == 'exportMasks:':
            return self.image != None and len(self.maskList.masks) > 0
        
        return True
    
    def selectSource_(self,sender):
        dialog = NSOpenPanel.openPanel()
        dialog.setFloatingPanel_(True)
        dialog.setCanChooseDirectories_(False)
        dialog.setCanChooseFiles_(True)
        dialog.setAllowsMultipleSelection_(False)
        result = dialog.runModalForTypes_(['public.image'])
        
        if result == NSOKButton:
            selected_url = dialog.URLs()[0]
            self.project.setValue_forKeyPath_(selected_url.absoluteString(),'sourceURL')
            self.updateImage()
            
    
    def exportMasks_(self,sender):
        savePanel = NSSavePanel.savePanel()
        
        sourceURL = NSURL.URLWithString_(self.project.valueForKeyPath_('sourceURL'))
 
        cgSource = CGImageSourceCreateWithURL(sourceURL, None)
        type = CGImageSourceGetType(cgSource)
        metaData = self.image_view.imageProperties()
        fileName = sourceURL.path().lastPathComponent()
        
        saveOptions = IKSaveOptions.alloc().initWithImageProperties_imageUTType_(metaData, type)
        
        saveOptions.addSaveOptionsAccessoryViewToSavePanel_(savePanel)
        
        result = savePanel.runModal()
        
        if result == NSOKButton:
            baseURL = savePanel.URLs()[0]
            base,file = os.path.split(baseURL.absoluteString())
            file,ext = os.path.splitext(file)
            
            for mask in self.maskList.masks:
                mask_file = os.path.join(base, file + '-' + mask.name + ext)
                
                dest = CGImageDestinationCreateWithURL(NSURL.URLWithString_(mask_file), saveOptions.imageUTType(), 1, None)
                
                image = mask.renderImage()
                
                CGImageDestinationAddImage(dest, image, saveOptions.imageProperties())
                CGImageDestinationFinalize(dest)
                del dest
            
    
    def windowControllerDidLoadNib_(self, aController):
        super(ColorMaskDocument, self).windowControllerDidLoadNib_(aController)
        # user interface preparation code
        
        self.image_view.setAutohidesScrollers_(True)
        
        # fetch the project, if we were loaded from a file
        if self.project == None:
            context = self.managedObjectContext()
            fetchRequest = NSFetchRequest.alloc().init()
            entity = NSEntityDescription.entityForName_inManagedObjectContext_('MaskProject',context)
            fetchRequest.setEntity_(entity)
            fetchResult, error = context.executeFetchRequest_error_(fetchRequest, None)
        
            self.project = fetchResult.objectAtIndex_(0)
        
        # Not supported yet
            #StackedItem.alloc().initFromDoc_(self),
            #FlattenedItem.alloc().initFromDoc_(self),
        self.root = [
            OriginalItem.alloc().initFromDoc_(self),
            ColorListItem.alloc().initFromDoc_(self)
            ]
        
        self.maskList = self.root[-1]
        
        self.sourceToolsActions = [
            self.addItem,
            self.removeItem
            ]
        
        self.source_list.reloadData()
        
        self.zoom_slider.setFloatValue_(1.0)
        
        self.updateImage()
        self.updateZoomSliderFromImageView()
        
        self.source_list.expandItem_(self.maskList)
    
    def updateImage(self):
        url = self.project.valueForKeyPath_('sourceURL')
        if url != '':
            self.image_view.setHidden_(False)
            self.image = CIImage.imageWithContentsOfURL_(NSURL.URLWithString_(url))
            self.image_view.setImageWithURL_(NSURL.URLWithString_(url))
            self.updateZoomSliderFromImageView()
        else:
            self.image_view.setHidden_(True)
            self.image = CIImage.emptyImage()
        
        if self.selected != None:
            self.selected.updateImage()
    
    def outlineView_child_ofItem_(self,outlineView,index,item):
        if item == None:
            return self.root[index]
        else:
            return item.child(index)
            
    def outlineView_isItemExpandable_(self,outlineView,item):
        return item.hasChildren()
            
    def outlineView_numberOfChildrenOfItem_(self,outlineView,item):
        if self.root == None:
            # this can be called before we've been loaded from the Xib
            return 0
        elif item == None:
            return len(self.root)
        else:
            return item.numChildren()
        
    def outlineView_objectValueForTableColumn_byItem_(self, outlineView, tableColumn, item):
        return item.name
    
    def outlineView_shouldSelectItem_(self,outlineView, item):
        return item.shouldSelect()
    
    def outlineViewSelectionDidChange_(self,notification):
        if self.selected != None:
            self.selected.unselected()
        self.selected = self.source_list.itemAtRow_(self.source_list.selectedRow())
        self.selected.selected()
    
    def zoomOut_(self,sender):
        self.image_view.zoomOut_(self)
        self.updateZoomSliderFromImageView()
        
    def zoomIn_(self,sender):
        self.image_view.zoomIn_(self)
        self.updateZoomSliderFromImageView()
    
    def zoomActualSize_(self,sender):
        self.image_view.zoomImageToActualSize_(self)
        self.updateZoomSliderFromImageView()
    
    def zoomToFit_(self,sender):
        self.image_view.zoomImageToFit_(self)
        self.updateZoomSliderFromImageView()
    
    def updateZoomSliderFromImageView(self):
        self.zoom_slider.setFloatValue_(math.sqrt(math.sqrt(self.image_view.zoomFactor())))
    
    @objc.IBAction
    def zoomSliderMoved_(self,sender):
        self.image_view.setZoomFactor_(sender.floatValue()**4)
    
    @objc.IBAction
    def sourceToolsClicked_(self,sender):
        self.sourceToolsActions[sender.cell().tagForSegment_(sender.selectedSegment())]()
    
    def addItem(self):
        maskObjs = self.project.mutableSetValueForKey_('masks')
        
        objContext = self.managedObjectContext()
        newMask = NSEntityDescription.insertNewObjectForEntityForName_inManagedObjectContext_('Mask', objContext)
        newMask.setValue_forKey_('test', 'name')
        newMask.setValue_forKey_(NSColor.redColor(), 'color')
        newMask.setValue_forKey_(0.4, 'chromaTolerance')
        newMask.setValue_forKey_(len(self.maskList.masks), 'sortOrder')
        
        maskObjs.addObject_(newMask)
        newItem = self.maskList.addMaskWithMask_(newMask)
        
        self.source_list.reloadItem_reloadChildren_(self.maskList, True)
        
        self.source_list.selectRowIndexes_byExtendingSelection_(NSIndexSet.indexSetWithIndex_(self.source_list.rowForItem_(newItem)), False)
        self.outlineViewSelectionDidChange_(None)
    
    def removeItem(self):
        if isinstance(self.selected,MaskItem):
            maskObjs = self.project.mutableSetValueForKey_('masks')
            objContext = self.managedObjectContext()
            
            toRemove = self.selected
            toRemove.unselected()
            toRemove.unbind()
            
            self.selected = None
            
            self.maskList.masks.remove(toRemove)
            self.source_list.reloadItem_reloadChildren_(self.maskList, True)
            
            maskObjs.removeObject_(toRemove.mask)
            objContext.deleteObject_(toRemove.mask)
            
            self.outlineViewSelectionDidChange_(None)
            