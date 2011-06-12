//
//  ColorDistance.h
//  MaskingPlugins
//
//  Created by Thomas Stephens on 6/11/11.
//  Copyright 2011 __MyCompanyName__. All rights reserved.
//

#import <Cocoa/Cocoa.h>
#import <QuartzCore/QuartzCore.h>


@interface ColorDistance : CIFilter
{
    CIImage      *inputImage;
    CIColor      *inputColor;
    NSNumber     *inputChromaTolerance;
    NSNumber     *inputFalloff;
}
@end

@interface LuminanceDistance : CIFilter
{
    CIImage      *inputImage;
    NSNumber     *inputLuminanceTolerance;
    NSNumber     *inputFalloff;
}
@end

@interface PerceptualDistance : CIFilter
{
    CIImage      *inputImage;
    CIColor      *inputColor;
    NSNumber     *inputChromaTolerance;
    NSNumber     *inputLuminanceTolerance;
    NSNumber     *inputFalloff;
}
@end
