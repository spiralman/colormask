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
from MaskLayerView import *

import traceback

class ColorMaskDocument(NSPersistentDocument):
    window = objc.IBOutlet()
    source_list = objc.IBOutlet()
    image_view = objc.IBOutlet()
    zoom_slider = objc.IBOutlet()
    export_panel = objc.IBOutlet()
    export_progress = objc.IBOutlet()
    export_label = objc.IBOutlet()
    
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
        self.model = None
        NSValueTransformer.setValueTransformer_forName_(self.colorTransformer, 'CIColorToNSColorTransformer')
        
    def init(self):
        self = super(ColorMaskDocument,self).init()
        
        self.root = None
        self.project = None
        
        self.selected = None
        self.image = None
        
        self.drawingMode = 'mask'
        
        return self
    
    # Almost 20 lines of code to get the "automatic" file version upgrade working...
    def managedObjectModel(self):
        """ The default implementation tries to merge the 2 versions of the models together,
        which doesn't work. Instead, we return the "current" version.
        """
        if self.__class__.model == None:
            bundle = NSBundle.bundleForClass_(self.class__())
            url = bundle.URLForResource_withExtension_('ColorMaskDocument', 'momd')
            self.__class__.model = NSManagedObjectModel.alloc().initWithContentsOfURL_(url)
        
        return self.__class__.model
    
    def configurePersistentStoreCoordinatorForURL_ofType_modelConfiguration_storeOptions_error_(self, url, fileType, configuration, storeOptions, error):
        """ The default implementation doesn't turn on the auto-migration feature. 
        This version does.
        """
        if storeOptions != None:
            mutableOptions = storeOptions.mutableCopyWithZone_(None)
        else:
            mutableOptions = NSMutableDictionary.dictionaryWithCapacity_(2)
        
        mutableOptions.setObject_forKey_(True,'NSMigratePersistentStoresAutomaticallyOption')
        mutableOptions.setObject_forKey_(True,'NSInferMappingModelAutomaticallyOption')
        
        return super(ColorMaskDocument,self).configurePersistentStoreCoordinatorForURL_ofType_modelConfiguration_storeOptions_error_(url, fileType, configuration, mutableOptions, error)
    
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
        if item.action() == 'showMask:' and self.drawingMode != 'mask':
            item.setState_(NSOffState)
        elif item.action() == 'showSource:' and self.drawingMode != 'source':
            item.setState_(NSOffState)
        elif item.action() == 'showStacked:' and self.drawingMode != 'stacked':
            item.setState_(NSOffState)
        
        if item.action() == 'exportMasks:' or item.action() == 'showMask:' or item.action() == 'showStacked:':
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
    
    def showMask_(self,sender):
        sender.setState_(NSOnState)
        self.drawingMode = 'mask'
        self.updateSelected()
        
    def showSource_(self,sender):
        sender.setState_(NSOnState)
        self.drawingMode = 'source'
        self.updateSelected()
    
    def showStacked_(self,sender):
        sender.setState_(NSOnState)
        self.drawingMode = 'stacked'
        self.updateSelected()
    
    def exportMasks_(self,sender):
        savePanel = NSSavePanel.savePanel()
        
        sourceURL = NSURL.URLWithString_(self.project.valueForKeyPath_('sourceURL'))
 
        cgSource = CGImageSourceCreateWithURL(sourceURL, None)
        type = CGImageSourceGetType(cgSource)
        
        fileName = sourceURL.path().lastPathComponent()
        
        saveOptions = IKSaveOptions.alloc().initWithImageProperties_imageUTType_(None, type)
        
        saveOptions.addSaveOptionsAccessoryViewToSavePanel_(savePanel)
        
        result = savePanel.runModal()
        
        if result == NSOKButton:
            if self.export_panel is None:
                NSBundle.loadNibNamed_owner_('ExportSheet',self)
                
            NSApp.beginSheet_modalForWindow_modalDelegate_didEndSelector_contextInfo_(self.export_panel,self.window,None,None,None)
            
            baseURL = savePanel.URLs()[0]
            base,file = os.path.split(baseURL.absoluteString())
            file,ext = os.path.splitext(file)
            
            session = NSApp.beginModalSessionForWindow_(self.export_panel)
            
            for index,mask in enumerate(self.maskList.masks):
                self.export_progress.setDoubleValue_(float(index)/len(self.maskList.masks) * 100.0)
                self.export_label.setStringValue_(''.join(['Exporting: ',mask.name]))
                
                NSApp.runModalSession_(session)
                
                mask_file = os.path.join(base, file + '-' + mask.name.replace(' ','_') + ext)
                
                dest = CGImageDestinationCreateWithURL(NSURL.URLWithString_(mask_file), saveOptions.imageUTType(), 1, None)
                
                mask.renderImage(dest, saveOptions.imageProperties())
            
            NSApp.endModalSession_(session)
            
            NSApp.endSheet_(self.export_panel)
            self.export_panel.orderOut_(self)
                
    def windowControllerDidLoadNib_(self, aController):
        super(ColorMaskDocument, self).windowControllerDidLoadNib_(aController)
        # user interface preparation code
        
        aController.setShouldCloseDocument_(True)
        
        # fetch the project, if we were loaded from a file
        if self.project == None:
            context = self.managedObjectContext()
            fetchRequest = NSFetchRequest.alloc().init()
            entity = NSEntityDescription.entityForName_inManagedObjectContext_('MaskProject',context)
            fetchRequest.setEntity_(entity)
            fetchResult, error = context.executeFetchRequest_error_(fetchRequest, None)
        
            self.project = fetchResult.objectAtIndex_(0)
        
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
        
        self.image_view.addObserver_forKeyPath_options_context_(self, 'zoom_factor', NSKeyValueObservingOptionNew, None)
        
        self.source_list.expandItem_(self.maskList)
    
    def windowWillClose_(self,notification):
        if self.selected != None:
            self.selected.unselected()
        self.image_view.removeObserver_forKeyPath_(self, 'zoom_factor')
    
    def updateImage(self):
        url = self.project.valueForKeyPath_('sourceURL')
        if url != '':
            self.image_view.setHidden_(False)
            self.image_view.setImageWithURL_(NSURL.URLWithString_(url))
            
            self.root[0].imageSet()
            for mask in self.maskList.masks:
                mask.imageSet()
            
            self.image = self.image_view.image
            
            self.sourceLayer = self.image_view.getNewContentLayer()
            
            self.stackedLayer = self.image_view.getNewEmptyLayer()
            
            self.updateSelected()
            self.image_view.zoomImageToFit_(self)
        else:
            self.image_view.setHidden_(True)
            self.image = CIImage.emptyImage()
    
    def updateSelected(self):
        if self.selected == None:
            self.image_view.showLayer(self.sourceLayer)
        else:
            if self.drawingMode == 'mask':
                if self.selected.layer != None:
                    self.selected.displayedLayer = self.selected.layer
                    self.image_view.showLayer(self.selected.layer)
            elif self.drawingMode == 'source':
                self.image_view.showLayer(self.sourceLayer)
            elif self.drawingMode == 'stacked':
                anchor = CGPoint()
                anchor.x = 0.5
                anchor.y = 0.5
                
                position = CGPoint()
                position.x = 0.0
                position.y = 0.0
                self.stackedLayer.setSublayers_(None)
                layer = self.stackedLayer
                
                for mask in self.maskList.masks:
                    newLayer = self.image_view.getNewContentLayer()
                    filters = mask.filters + [CIFilter.filterWithName_keysAndValues_('CIColorInvert', 'name', 'invertToMask', None), CIFilter.filterWithName_keysAndValues_('CIMaskToAlpha', 'name', 'mask', None), CIFilter.filterWithName_keysAndValues_('CIColorInvert', 'name', 'maskToBlack', None)]
                    newLayer.setFilters_(filters)
                    newLayer.setOpacity_(0.5)
                    
                    mask.displayedLayer = newLayer
                    
                    layer.addSublayer_(newLayer)
                
                self.image_view.showLayer(self.stackedLayer)
    
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
        self.updateSelected()
    
    def zoomOut_(self,sender):
        self.image_view.zoomOut_(self)
        
    def zoomIn_(self,sender):
        self.image_view.zoomIn_(self)
    
    def zoomActualSize_(self,sender):
        self.image_view.zoomImageToActualSize_(self)
    
    def zoomToFit_(self,sender):
        self.image_view.zoomImageToFit_(self)
    
    def observeValueForKeyPath_ofObject_change_context_(self,key,object,change,context):
        if key == 'zoom_factor' and object == self.image_view:
            self.zoom_slider.setFloatValue_(math.sqrt(math.sqrt(change._.new)))
    
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
        newItem.imageSet()
        
        self.source_list.reloadItem_reloadChildren_(self.maskList, True)
        
        self.source_list.selectRowIndexes_byExtendingSelection_(NSIndexSet.indexSetWithIndex_(self.source_list.rowForItem_(newItem)), False)
        self.outlineViewSelectionDidChange_(None)
    
    def removeItem(self):
        if isinstance(self.selected,MaskItem):
            maskObjs = self.project.mutableSetValueForKey_('masks')
            objContext = self.managedObjectContext()
            
            toRemove = self.selected
            toRemove.unbind()
            toRemove.unselected()
            
            self.selected = None
            
            self.maskList.masks.remove(toRemove)
            self.source_list.reloadItem_reloadChildren_(self.maskList, True)
            
            maskObjs.removeObject_(toRemove.mask)
            objContext.deleteObject_(toRemove.mask)
            
            self.outlineViewSelectionDidChange_(None)
            