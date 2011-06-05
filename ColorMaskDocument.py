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

from ColorMaskItems import *

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
            