//
//  ColorMaskFilterPlugInLoader.h
//  ColorMaskFilter
//
//  Created by Thomas Stephens on 4/2/11.
//  Copyright __MyCompanyName__ 2011. All rights reserved.
//

#import <Foundation/Foundation.h>
#import <QuartzCore/CoreImage.h>


@interface MaskingPluginsLoader : NSObject <CIPlugInRegistration>
{

}

-(BOOL)load:(void*)host;

@end
